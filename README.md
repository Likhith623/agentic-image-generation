# GamifyNovi
Deployed for testing at : https://cvo-app-selfie.streamlit.app/


# Gamification of NoviAI : Jayden Lim Persona Chat Interface

This is a Streamlit-based interactive application that facilitates multi-turn conversations with a fictional persona named **Jayden Lim**. The app supports both free-form conversation and 36 structured activities. Jayden's tone, slang, and behavior are governed by a strict persona specification embedded at runtime.

---

## Table of Contents

* [Overview](#overview)
* [Architecture](#architecture)
* [File Structure](#file-structure)
* [Persona Engine](#persona-engine)
* [Core Features](#core-features)
* [Dependencies](#dependencies)
* [Setup Instructions](#setup-instructions)
* [Secrets and Configuration](#secrets-and-configuration)
* [Usage](#usage)
* [CrewAI Activity System](#crewai-activity-system)
* [Context Extraction](#context-extraction)
* [Selfie Generation](#selfie-generation)

---

## Overview

Jayden responds with short, slang-rich, emotionally aware messages across two interaction types:

1. **Free-form chat**, which is powered by the Gemini 2.0 Flash model using LiteLLM with response streaming. Messages are rendered incrementally for a more natural experience.
2. **Structured activities**, launched through a categorized set of buttons grouped under an expandable dropdown. Each activity modifies Jayden's behavior for multi-turn interactions.
3. **Selfie generation**, which can be manually triggered, uses Jayden's latest message to generate a face-retaining image based on detected emotion, location, and action.

---

## Architecture

### Components

* **Streamlit**: Web interface and session state
* **LiteLLM**: Connects to Gemini 2.0 Flash for message generation
* **CrewAI**: Drives multi-turn structured activities
* **Replicate API**: Generates images using instant-id-ipadapter-plus-face
* **Context Extractor**: Parses emotion, location, and action from bot replies
* **Selfie Generation (manual trigger)**: Accessible via a sidebar command, uses extracted context and reference identity to render updated visual output

---

## File Structure

```plaintext
CVotemp/
│
├── app2.py                 # Main application file
├── requirements.txt        # Python dependency list
│
└── .streamlit/
    └── secrets.toml        # API keys for Gemini and Replicate
```

---

## Persona Engine

Jayden Lim is a fictional 22-year-old Singaporean male with a defined backstory and personality rules. His voice includes Singlish, Gen Z slang, cultural references, and meme awareness. The full persona is injected as a prompt at initialization and used across both default and activity-based interactions.

Constraints include:

* Max 1–2 sentences per message
* Avoids formality
* Responds with emotional awareness and cultural specificity
* Never breaks character or overexplains

---

## Core Features

* Free-form chat powered by Gemini 2.0 Flash with streamed token generation
* 36 structured activities, each with a goal and output style
* Stateful memory using Streamlit’s session\_state
* Activity-specific logic built via CrewAI tasks and agents
* On-demand image generation tied to message content
* Persona consistency enforced across all interaction types

---

## Dependencies

```text
streamlit
requests
crewai
litellm
python-dotenv
google-generativeai
```

Install them with:

```bash
pip install -r requirements.txt
```

---

## Setup Instructions

### 1. Clone the repository

```bash
git clone https://github.com/<your-org>/CVotemp.git
cd CVotemp
```

### 2. Configure secrets

Create `.streamlit/secrets.toml`:

```toml
GEMINI_API_KEY = "your_google_gemini_key"
REPLICATE_API_TOKEN = "your_replicate_token"
```

Or set as environment variables:

```bash
export GEMINI_API_KEY=your_google_gemini_key
export REAPI_TOKEN=your_replicate_token
```

---

## Usage

Launch the app with:

```bash
streamlit run app2.py
```

On startup:

* Jayden sends a default opening message
* A dropdown (Streamlit expander) reveals multiple button grids grouped by interaction type and XP level
* Clicking a button starts an activity
* Typing "exit", "stop", or "end" resets activity state
* Session memory persists chat history, activity flags, and selfie state

All normal chat input outside activities also uses Gemini 2.0 Flash with streamed response rendering.

---

## CrewAI Activity System

Activities are powered by CrewAI’s `Agent` and `Task` system. Each button in the activity panel launches a different conversational template.

Each task is defined with:

* A static description string
* The user's most recent input
* Optionally, the last 8 turns of activity-specific conversation (used as historical context, not full transcript)
* An expected output pattern designed to match Jayden’s persona

Activities include light (e.g., nickname game), medium (e.g., scenario shuffle), and deep (e.g., unsent messages) tiers.

All activities enforce:

* Persona tone
* Continuation logic (always prompt for the next input unless explicitly ended)
* **Note**: Streaming is currently not active for activity-based messages. It is planned and will be added soon.

---

## Context Extraction

Context is parsed from the most recent assistant reply using a second Gemini call. It returns:

* `emotion`: A short label like "happy" or "confused"
* `location`: Where the response appears to be set
* `action`: What Jayden is supposedly doing

The result is extracted as a raw JSON block. A regex is used to isolate the valid object, and it is parsed directly. Failure falls back to safe defaults.

This metadata is used only during image generation.

---

## Selfie Generation

Selfie generation is manually triggered through the UI. The process is:

1. User clicks a sidebar button to generate a new selfie
2. The most recent assistant message is analyzed for emotion, location, and action
3. A prompt string is constructed. Example:

   ```
   Jayden Lim, happy expression, texting, in MRT station, one person, realistic lighting, portrait, close-up
   ```
4. This is passed to **Replicate’s instant-id-ipadapter-plus-face API**
   (average cost per call: \~0.063 USD)
5. The API returns a payload containing a `"web"` key with a URL
6. That URL is extracted and the image is rendered in the chat interface

This API retains facial similarity to a static identity image while updating expression, pose, and background based on context.

This project involved extensive research into multimodal emotion representation to address the challenge of accurately visualizing negative emotions (e.g., sadness, anger) in a non-exaggerated and human-aligned manner. After surveying relevant papers and comparing multiple generative models, Hugging Face’s Modal AI was selected for its balance of control and visual consistency. The codebase was further modified to improve prompt compatibility and ensure stable image generation based on dynamic conversational context. These improvements made the model deployable for use in emotion-aware chatbot systems, with a focus on interpretability and user trust.
Changed the modal art generator, applied payment pipelin, now takes up negative emotions.

-Aditya Namdeo
