# main.py (Corrected Version with Base64 Output)

import os
import re
import json
import logging
import asyncio
import uuid
import base64 # 👈 1. IMPORT THE BASE64 LIBRARY
from contextlib import asynccontextmanager
from typing import Optional, Dict, Any, List

import litellm
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from gradio_client import Client
from pydantic import BaseModel, Field

# --- Initial Configuration ---

load_dotenv()
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    from bot_prompts import BOT_PROMPTS as VALID_BOT_IDS
except ImportError:
    logger.error("FATAL: bot_prompts.py not found. Please create it.")
    exit()

# --- Pydantic Models for API Validation ---

class ImageGenerationRequest(BaseModel):
    bot_id: str = Field(..., description="Unique identifier for the bot (e.g., 'delhi_mentor_male').")
    message: str = Field(..., description="The user message that will provide context for the image.")
    email: str = Field(..., description="User's email for identification and tracking.")
    previous_conversation: Optional[str] = Field("", description="A string of the previous conversation history.")
    username: Optional[str] = Field("User", description="Display name for the user.")

# 2. MODIFY THE RESPONSE MODEL
class ImageGenerationResponse(BaseModel):
    bot_id: str
    image_url: str
    image_base64: str # 👈 ADD THIS FIELD FOR THE BASE64 STRING
    status: str
    emotion_context: Dict[str, str]

class ErrorDetail(BaseModel):
    status: str = "error"
    message: str

# --- FastAPI Application Setup ---

@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Application startup...")
    await chatbot_service.initialize_gradio_client()
    yield
    logger.info("Application shutdown.")

app = FastAPI(
    title="AI Image Generation API",
    description="Generates a contextual selfie for an AI persona based on conversation.",
    version="3.2.0", # Version updated
    lifespan=lifespan,
    responses={
        400: {"model": ErrorDetail, "description": "Bad Request"},
        404: {"model": ErrorDetail, "description": "Not Found"},
        500: {"model": ErrorDetail, "description": "Internal Server Error"},
        503: {"model": ErrorDetail, "description": "Service Unavailable"},
    }
)

os.makedirs("static/images", exist_ok=True)
app.mount("/static", StaticFiles(directory="static"), name="static")

allowed_origins = os.environ.get("CORS_ALLOWED_ORIGINS", "*").split(",")
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# --- Core Logic in a Service Class ---

class ChatbotService:
    def __init__(self):
        self.gradio_client = None
        self.gemini_api_key = os.environ.get("GEMINI_API_KEY")
        if not self.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is not set.")
        os.environ["GEMINI_API_KEY"] = self.gemini_api_key

    async def initialize_gradio_client(self):
        try:
            self.gradio_client = await asyncio.to_thread(Client, "multimodalart/Ip-Adapter-FaceID")
            logger.info("Gradio client initialized successfully.")
        except Exception as e:
            logger.error(f"Failed to initialize Gradio client: {e}")
            self.gradio_client = None

    def get_bot_response_for_context(self, request_data: ImageGenerationRequest, bot_name: str) -> str:
        messages = [
            {"role": "system", "content": f"You are {bot_name}. Briefly react to the user's message in a way that reveals emotion."},
            {"role": "user", "content": request_data.message}
        ]
        try:
            response = litellm.completion(
                model="gemini/gemini-1.5-flash", messages=messages, stream=False, max_tokens=50
            )
            return response.choices[0].message.content
        except Exception as e:
            logger.error(f"Gemini API call for context failed: {e}")
            return f"{bot_name} is thinking about the message: '{request_data.message}'"

    def extract_context(self, text: str) -> Dict[str, str]:
        context_prompt = f"""
        Analyze the following text and describe the scene in simple terms.
        Text: "{text}"
        Respond ONLY with a JSON object with keys "emotion", "location", and "action".
        Example: {{"emotion": "happy and smiling", "location": "at a bustling cafe", "action": "sipping a coffee"}}
        """
        try:
            response = litellm.completion(
                model="gemini/gemini-1.5-flash",
                messages=[{"role": "user", "content": context_prompt}],
                response_format={"type": "json_object"}
            )
            return json.loads(response.choices[0].message.content)
        except Exception as e:
            logger.warning(f"Context extraction failed, using defaults. Error: {e}")
            return {"emotion": "neutral", "location": "a room", "action": "looking at the camera"}

    # 3. MODIFY THE SERVICE FUNCTION TO RETURN THE BASE64 STRING
    async def generate_and_save_selfie(self, bot_name: str, base_image_path: str, context: Dict) -> tuple[str, str]:
        """
        Generates a selfie, saves it, and returns the URL path AND the base64 encoded string.
        """
        if not self.gradio_client:
            raise HTTPException(status_code=503, detail="Image generation service is not available.")

        prompt_text = (
            f"Close-up portrait of a person who looks like the reference image, with a {context.get('emotion', 'neutral expression')} expression, "
            f"{context.get('action', 'looking at the camera')}, at {context.get('location', 'a neutral background')}. "
            f"The person's name is {bot_name}. Ultra-detailed, dslr quality, cinematic photo."
        )
        
        logger.info(f"Using base image: {base_image_path}")

        try:
            logger.info(f"Generating image with prompt: {prompt_text}")
            result = await asyncio.to_thread(
                self.gradio_client.predict,
                images=[base_image_path],
                prompt=prompt_text,
                negative_prompt="nsfw, low quality, deformed, ugly",
                api_name="/generate_image"
            )

            if not (result and isinstance(result, list) and result[0].get("image")):
                raise ValueError("Invalid response from image generation service.")
            
            temp_image_path = result[0]["image"]
            
            with open(temp_image_path, "rb") as f:
                image_bytes = f.read()
            
            # Encode the image bytes into a Base64 string
            base64_encoded_image = base64.b64encode(image_bytes).decode('utf-8')
            
            unique_filename = f"{uuid.uuid4()}.png"
            output_path = f"static/images/{unique_filename}"
            
            with open(output_path, "wb") as f:
                f.write(image_bytes)
                
            logger.info(f"Image successfully saved to {output_path}")
            
            # Return both the path and the base64 string
            return f"/static/images/{unique_filename}", base64_encoded_image

        except Exception as e:
            logger.error(f"FaceID generation failed: {e}")
            raise HTTPException(status_code=500, detail="Failed to generate the image internally.")


# --- Global Service Instance and API Endpoints ---

chatbot_service = ChatbotService()

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(status_code=exc.status_code, content={"status": "error", "message": exc.detail})

@app.get("/", include_in_schema=False)
def root():
    return {"status": "healthy", "message": "API is running."}

@app.post("/v1/generate_image", response_model=ImageGenerationResponse)
async def generate_image(request: ImageGenerationRequest, http_request: Request):
    bot_id = request.bot_id
    
    if bot_id not in VALID_BOT_IDS:
        raise HTTPException(status_code=404, detail=f"Bot with id '{bot_id}' is not a valid bot.")

    photos_dir = "photos"
    supported_extensions = [".jpeg", ".jpg", ".png", ".webp"]
    base_image_path = None
    for ext in supported_extensions:
        path = os.path.join(photos_dir, f"{bot_id}{ext}")
        if os.path.exists(path):
            base_image_path = path
            break
            
    if not base_image_path:
        raise HTTPException(status_code=404, detail=f"Base image for bot '{bot_id}' not found in the '{photos_dir}' folder. Please ensure the image file exists and has a matching name (e.g., delhi_mentor_male.jpeg).")

    bot_name = bot_id.replace("_", " ").title()
    bot_response_text = chatbot_service.get_bot_response_for_context(request, bot_name)
    context = chatbot_service.extract_context(bot_response_text)
    
    # 4. MODIFY THE ENDPOINT TO HANDLE BOTH RETURNED VALUES
    # Unpack both the path and the base64 string from the service function
    image_path, image_base64 = await chatbot_service.generate_and_save_selfie(bot_name, base_image_path, context)
    
    base_url = str(http_request.base_url)
    full_image_url = f"{base_url.rstrip('/')}{image_path}"

    return ImageGenerationResponse(
        bot_id=bot_id,
        image_url=full_image_url,
        image_base64=image_base64, # 👈 Include the base64 string in the final response
        status="success",
        emotion_context=context
    )

# --- Main execution block ---
if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)