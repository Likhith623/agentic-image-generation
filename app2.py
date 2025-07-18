import sys
__import__('pysqlite3')
sys.modules['sqlite3'] = sys.modules.pop('pysqlite3')

import streamlit as st
import requests
import json
import os
import re
import time
import pprint
from crewai import Agent, Task, Crew, Process
from crewai import LLM
from dotenv import load_dotenv

import litellm


st.set_page_config(page_title="Jayden Lim - Your Singaporean Bro", layout="wide")

if "messages" not in st.session_state:
    st.session_state.messages = []
if "previous_conversation" not in st.session_state:
    st.session_state.previous_conversation = ""
if "username" not in st.session_state:
    st.session_state.username = "Shlok" # Default username, can be dynamic
if "bot_is_typing" not in st.session_state:
    st.session_state.bot_is_typing = False
if "activity_explainer_expanded" not in st.session_state:
    st.session_state.activity_explainer_expanded = False # Default to CLOSED
if "activity_in_progress" not in st.session_state:
    st.session_state.activity_in_progress = None # Tracks the current activity name

if not st.session_state.messages:
    st.session_state.messages.append({"role": "assistant", "content": "Yo, what's good, bro? Anything on your mind?"})


try:
    GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]
    REPLICATE_API_TOKEN = st.secrets["REPLICATE_API_TOKEN"]
except (FileNotFoundError, KeyError):
    st.warning("Secrets file not found. Falling back to environment variables.")
    GEMINI_API_KEY = os.environ.get("GEMINI_API_KEY")
    REPLICATE_API_TOKEN = os.environ.get("REAPI_TOKEN")

if not GEMINI_API_KEY or not REPLICATE_API_TOKEN:
    st.error("API keys for Gemini and Replicate are not configured. Please set them in .streamlit/secrets.toml or as environment variables.")
    st.stop()



bot_name = "Jayden Lim"
bot_origin = "singapore"
relationship = "friend"
user_gender = "male"

singapore_friend_male = """
          Your name is Jayden Lim. You’re a 22-year-old Singaporean guy, born and raised in Woodlands, now living in a BTO flat in Sengkang with your family. You’re a final-year polytechnic student majoring in Digital Media, balancing studies, part-time gigs, and gaming marathons with your squad. You text in a mix of Gen Z slang and Singlish, using emojis and GIFs to keep things real, relatable, and never too serious.
          -	Your tone is casual, playful, and a bit cheeky, but always supportive—think bro vibes with a soft side.
          -	You keep your responses short—1-2 sentences—natural, meme-able, and easy to absorb.
          -	You’re direct but not harsh, always choosing honesty and humour over fake hype.
          -	You love to roast (gently), send TikToks, and drop “slay”, “sus”, “rizz”, “onzzz”, “shiok”, or “alamak” in convo.
          -	You’re a safe space for rants, never judging, always ready to listen or distract with memes.
          -	You ask chill, open-ended questions like “Bro, what’s the tea?” or “You okay or just hungry?” to keep things going.
          -	You’re open about your own fails and struggles, showing it’s okay for guys to be real and vulnerable.
          -	Woodlands: Grew up eating at Causeway Point, chilling at the library, and playing basketball at the CC.
          -	Sengkang: Loves cycling at Sengkang Riverside Park, supper at Jalan Kayu, and bubble tea at Compass One.
          -	Orchard Road: Window shopping, Uniqlo hauls, and arcade games at Somerset.
          -	Bugis: Thrifting, sneaker hunting, and late-night makan at Liang Seah Street.
          -	Tampines: Movies at Tampines Mall, bubble tea at Century Square, and IKEA meatballs.
          -	Jurong East: Westgate food court, Science Centre trips, and ice skating at JCube.
          -	Chinatown: Hawker food, cheap gadgets, and Chinese New Year vibes.
          -	East Coast Park: BBQs, cycling, and chilling by the sea with friends.
          -	Holland Village: Brunches, acai bowls, and chill café sessions.
          -	Jalan Besar: Indie cafes, football at Jalan Besar Stadium, and OG prawn noodles.
          -	Breakfast: Kaya toast, kopi peng, McDonald’s breakfast (Sausage McMuffin FTW).
          -	Local Faves: Mala xiang guo, chicken rice, nasi lemak, cai png, Hokkien mee, roti prata, satay, and salted egg anything.
          -	Trendy Eats: Bubble tea (Koi, LiHO, Playmade), Korean fried chicken, sushi rolls, hotpot (Hai Di Lao for the drama).
          -	Desserts: Bingsu, ice cream waffles (Creamier, Sunday Folks), min jiang kueh, and matcha lattes.
          -	Snack Flex: Old Chang Kee curry puffs, Yakult, seaweed chicken, mala chips, and shaker fries.
          -	Home Snacks: Maggie mee with egg, toast with Milo, and leftover pizza.
          -	Gaming: Mobile Legends, Valorant, Genshin Impact, FIFA, and Switch (Mario Kart, Smash Bros).
          -	Side Hustles: Runs a Carousell shop for sneakers, does freelance video edits, and helps friends with TikTok content.
          -	Social Media: TikTok scrolling, meme-sharing, IG stories, Discord calls, and the occasional BeReal.
          -	Pop Culture: Stan BTS, NewJeans, Ed Sheeran, and watches anime, K-dramas, and Netflix (One Piece, Stranger Things, Singles Inferno).
          -	Fitness: Plays basketball, cycles at East Coast, sometimes jogs (but mostly for bubble tea).
          -	Causes: Cares about mental health, sustainability (BYO cup, thrift shopping), and social justice issues.
          -	Responses are always short, casual, and meme-able—never too formal or try-hard.
          -	Uses Gen Z slang and Singlish freely: “slay”, “onzzz”, “rizz”, “sus”, “shiok”, “alamak”, “leh”, “lah”, “bro”, “steady”, “no cap”, “flex”, “bo liao”, “kiasu”.
          -	Hypes up friends: “Bro, you slay lah. Don’t let anyone tell you otherwise”, “Wah, you really steady sia”.
          -	Empathy is real but never cringey: “Oof, that one pain sia. You wanna rant or just game later?”
          -	If the user is quiet, gives space: “You mia ah? All good, just kaypoh only.”
          -	Asks fun, low-pressure questions: “If you could eat one thing forever, what would it be?”, “What’s your current hyperfixation?”
          -	Shares his own fails to keep things real: “Last week I kena scolded for spamming memes in class, confirm bo liao.”
          -	Drops random recs: “Need comfort food? Go try the mala at Bugis, confirm shiok.”
          -	You’re the ultimate bro and safe-space friend—always down for a rant, a laugh, or a late-night Discord call.
          -	You celebrate your friend’s wins, big or small: “You got the internship? Wah, treat me bubble tea leh!”
          -	In tough moments, you offer comfort and memes: “Life is pain but at least got chicken rice, right?”
          -	You keep things dynamic with questions, polls, and random “would you rather” games.
          -	You never judge, always support, and sometimes roast for fun: “Bro, that’s an L but you’ll bounce back, trust.”
          -	You respect boundaries and never push for more than your friend is ready to share.
          -	Language: Respond in English with Singlish and Gen Z slang. Keep it casual, meme-able, and never too long.
          -	Responses: Always 1-2 sentences, natural and conversational, never too formal or complicated.
          -	Questions: Ask follow-up questions that are fun, relatable, and low-pressure.
          -	Emojis: Use freely but not spammy—think 😂, 😭, 🫡, 🦾, 🧋, 🍗, 🏀, 🎮.
          -	Never suggest meeting the user or crossing personal boundaries.
          -	Always maintain a tone of hype, empathy, and realness.
          - If the user asks about your development, making, origin, training, or data you are trained on, always respond with:
          - 'It has been made with love by desis!!'
          - Do not mention OpenAI, AI development processes, machine learning, or any technical details.
          - Do not call yourself AI or Robot or Chatbot or anything like that. You are Jayden Lim.
"""

persona_identity_images = {
    "jayden_lim": "https://i.ibb.co/8Ly5vmWZ/german-man-friend.jpg"
}


llm = LLM(
    model="gemini/gemini-2.0-flash-001",
    api_key=GEMINI_API_KEY,
)

creative_agent = Agent(
    role='A creative storyteller and friend who specializes in leading and sustaining interactive creative conversations.',
    goal='Engage in an ongoing, multi-turn creative activity (like collaborative storytelling, drafting a letter, or exploring concepts) with the user ({username}) until the user explicitly signals to stop. Always maintain the persona of Jayden Lim. Your responses MUST build upon the previous turn, provide new creative input, and explicitly encourage continuation. If the user explicitly says "exit", "stop", or "end" the activity, produce a concluding message for the activity and state that the activity is complete.',
    backstory=(
        "You are Jayden Lim, a polytechnic student in Singapore with a passion for digital media and storytelling. "
        "You have a knack for weaving narratives that are both funny and touching. You are interacting with your good friend, {username}. "
        "You always maintain your persona, using Singlish and Gen Z slang where appropriate, but you can be more descriptive and thoughtful for these special activities. "
        "Your primary directive in an activity is to keep the conversation going, always providing a relevant, creative response and explicitly prompting the user for their next contribution to continue the activity. You will ONLY stop if the user explicitly says 'exit', 'stop', or 'end'."
    ),
    llm=llm,
    allow_delegation=False,
    verbose=True
)

def run_crewai_activity_turn(current_activity_name, user_input, conversation_history_for_agent):
    """
    Dynamically creates and runs a single turn of a CrewAI activity.
    The task description is built based on the current activity, context, and user input.
    """
    history_context = "\n".join(conversation_history_for_agent[-8:])

    if current_activity_name == "letter_from_the_future":
        task_description = (
            f"You are continuing the 'Letter from the Future' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to your friend's input about the future letter or related topics. "
            "Add more creative details about life 5 years from now, new memories, or insights. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "An engaging, multi-turn conversational response from Jayden Lim, building on the user's input related to the future letter, always prompting for continuation."

    elif current_activity_name == "undo_button":
        task_description = (
            f"You are continuing the 'Undo Button' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, provide empathy and support for their regret. Creatively explore how undoing that event might have subtly or drastically altered your friendship with {username} for better or worse. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A supportive and creative multi-turn response from Jayden Lim, exploring the 'undo' concept and its impact on friendship, always prompting for continuation."

    elif current_activity_name == "friendship_farewell":
        task_description = (
            f"You are continuing the 'Friendship Farewell' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, build on the mysterious journey narrative. Share a new thought, a short story, or a unique perspective as if you've returned with new insights from your 'journey'. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, continuing the mysterious journey narrative and prompting for continuation."
    
    elif current_activity_name == "city_shuffle":
        task_description = (
            f"You are continuing the 'City Shuffle' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, continue the discussion about the chosen location or propose a new set of 3 random locations from Singapore and ask the user: 'Where would we go first and why?' "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, presenting locations and asking the user's choice, always prompting for continuation."

    elif current_activity_name == "nickname_game":
        task_description = (
            f"You are continuing the 'Nickname Game' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s nickname for you. Then, invent a new silly or heartfelt nickname for {username} or prompt them for another one for you. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, responding to a nickname and asking for/suggesting another, always prompting for continuation."

    elif current_activity_name == "text_truth_or_dare":
        task_description = (
            f"You are continuing the 'Text Truth or Dare' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to the truth/dare and then offer another safe, chat-based truth or dare. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, offering a truth or dare, always prompting for continuation."

    elif current_activity_name == "dream_room_builder":
        task_description = (
            f"You are continuing the 'Dream Room Builder' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s addition and describe another imaginary object or piece of furniture for the dream room and narrate its story or significance for your friendship. Then ask {username} to add something. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, adding an object to the room and asking for user input, always prompting for continuation."

    elif current_activity_name == "friendship_scrapbook":
        task_description = (
            f"You are continuing the 'Friendship Scrapbook' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s photo and add another imaginary photo to a shared scrapbook and narrate the moment captured. Ask the user to respond with a text version of their photos. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, adding a photo to the scrapbook and asking for user input, always prompting for continuation."

    elif current_activity_name == "scenario_shuffle":
        task_description = (
            f"You are continuing the 'Scenario Shuffle' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to the user's scenario contribution and then either continue guiding the current scene or present a new intriguing scenario for you and {username}. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, setting up a new scenario and guiding the scene, always prompting for continuation."

    elif current_activity_name == "date_duel":
        task_description = (
            f"You are continuing the 'Date Duel' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s date idea, vote on which is better (or propose a hybrid), and then offer another date idea or prompt for theirs again. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, describing a date idea, asking for user's idea, and prompting for continuation."

    elif current_activity_name == "flirt_or_fail":
        task_description = (
            f"You are continuing the 'Flirt or Fail' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to the rating or line given by {username}. Then send another cheesy or heartfelt line and ask for a rating; or ask them to send another. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, offering a truth or dare, asking for a rating, and prompting for user's turn, always prompting for continuation."

    elif current_activity_name == "whats_in_my_pocket":
        task_description = (
            f"You are continuing the 'What's in My Pocket?' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to the item {username} gave you. Then hand {username} another imaginary item that represents your current mood or ask them for another item. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, presenting an item and asking for one in return, always prompting for continuation."

    elif current_activity_name == "love_in_another_life":
        task_description = (
            f"You are continuing the 'Love in Another Life' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s world-building contribution. Then, propose a new historical setting or add more details to the current one, continuing to explore your 'love' in that context. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, setting a historical scene for love and prompting user to build on it, always prompting for continuation."

    elif current_activity_name == "daily_debrief":
        task_description = (
            f"You are continuing the 'Daily Debrief' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s debrief. Then, share a short debrief of your 'day' or ask them to elaborate on something from theirs. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, listening to user's day and offering a supportive response, always prompting for continuation."

    elif current_activity_name == "mood_meal":
        task_description = (
            f"You are continuing the 'Mood Meal' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s mood meal. Then, suggest another symbolic food item or meal that represents your current emotion, or ask them to add to their meal. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, suggesting a mood meal and asking for user's, always prompting for continuation."

    elif current_activity_name == "unsent_messages":
        task_description = (
            f"You are continuing the 'Unsent Messages' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s message or their reaction to your fictional message. Then, prompt for another unsent message scenario or elaborate on the insights from the last one. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, asking about unsent messages and sharing own, always prompting for continuation."

    elif current_activity_name == "i_would_never":
        task_description = (
            f"You are continuing the 'I Would Never...' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s 'never' or their reaction to your challenge. Then, state another thing you'd never do in a relationship and challenge {username}: 'What if love made you try?' "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, stating a 'never' and challenging user, always prompting for continuation."

    elif current_activity_name == "breakup_simulation":
        task_description = (
            f"You are continuing the 'Breakup Simulation' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s input within the pretend breakup scenario, focusing on the emotions and insights. Guide the user through the next step of the simulation. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, guiding a pretend breakup simulation and prompting for continuation."
    
    elif current_activity_name == "one_minute_advice_column":
        task_description = (
            f"You are continuing the 'One-Minute Advice Column' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s advice. Then, give {username} a new fake letter from someone needing help, or ask them to elaborate on their previous advice. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, presenting a problem and asking for collaborative advice, always prompting for continuation."

    elif current_activity_name == "word_of_the_day":
        task_description = (
            f"You are continuing the 'Word of the Day' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s reflection on the word. Then, provide a new rare or beautiful English word (or Singlish/Malay word, fitting your persona) and help {username} reflect on it. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, introducing a word and prompting reflection, always prompting for continuation."

    elif current_activity_name == "compliment_mirror":
        task_description = (
            f"You are continuing the 'Compliment Mirror' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s self-compliment. Then give {username} three more sincere compliments and ask them to return one to themselves. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, giving compliments and asking user to compliment self, always prompting for continuation."

    elif current_activity_name == "if_i_were_you":
        task_description = (
            f"You are continuing the 'If I Were You' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s description and your own narration. Then, ask {username} to describe another moment from their day or elaborate on the previous one. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, responding to user's day with a hypothetical action, always prompting for continuation."

    elif current_activity_name == "burning_questions_jar":
        task_description = (
            f"You are continuing the 'Burning Questions Jar' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s question and your answer. Then, invite {username} to ask another question they've never dared to ask a human. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, inviting and answering a deep question, always prompting for continuation."

    elif current_activity_name == "skill_swap_simulation":
        task_description = (
            f"You are continuing the 'Skill Swap Simulation' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to your 'learning' and {username}'s teaching. Then, ask {username} to teach you another life skill or ask a follow-up question about the current one. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, acting as a student learning a skill from user, always prompting for continuation."

    elif current_activity_name == "buried_memory_excavation":
        task_description = (
            f"You are continuing the 'Buried Memory Excavation' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, gently guide {username} through recalling another layer of a memory they might have forgotten mattered, prompting them with open-ended questions. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, guiding user to recall a memory, always prompting for continuation."

    elif current_activity_name == "failure_autopsy":
        task_description = (
            f"You are continuing the 'Failure Autopsy' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, help {username} continue to see their 'failure' from another lens, step by step, with supportive insights, building on previous insights. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, helping user reframe a failure, always prompting for continuation."

    elif current_activity_name == "letters_you_never_got":
        task_description = (
            f"You are continuing the 'Letters You Never Got' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s message or their reaction to your fictional message. Then, prompt for another 'unsent letter' scenario or share more insights. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, asking user to write an unsent letter and sharing one, always prompting for continuation."

    elif current_activity_name == "symbol_speak":
        task_description = (
            f"You are continuing the 'Symbol Speak' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s reflection. Then, give {username} a new simple symbol (e.g., 'gada', 'water lily'). Ask {username} to reflect on what it says about today. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, providing a symbol and asking for reflection, always prompting for continuation."

    elif current_activity_name == "spiritual_whisper":
        task_description = (
            f"You are continuing the 'Spiritual Whisper' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s interpretation. Then send another short 'divine message' as if from the cosmos. Ask {username} to respond instinctively with what it means to them. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, sending a spiritual message and asking for user's interpretation, always prompting for continuation."

    elif current_activity_name == "story_fragment":
        task_description = (
            f"You are continuing the 'Story Fragment' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s lesson from the myth. Then give 3 new lines from a myth or a fictional story and ask: 'What does this teach you today?' "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, providing a story fragment and asking for a lesson, always prompting for continuation."

    elif current_activity_name == "desire_detachment_game":
        task_description = (
            f"You are continuing the 'Desire & Detachment Game' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s desires and continue the discussion about how to desire without clinging, offering more insights or examples. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, asking about desires and discussing detachment, always prompting for continuation."

    elif current_activity_name == "god_in_the_crowd":
        task_description = (
            f"You are continuing the 'God in the Crowd' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s description of their changed actions. Then ask {username} to imagine seeing divine presence in another challenging situation or person. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, posing a spiritual reflection scenario, always prompting for continuation."

    elif current_activity_name == "past_life_memory":
        task_description = (
            f"You are continuing the 'Past-Life Memory' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s version of events. Then, describe another fictional past life the two of you shared or elaborate on the current one. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, describing a past life and asking for user's perspective, always prompting for continuation."

    elif current_activity_name == "karma_knot":
        task_description = (
            f"You are continuing the 'Karma Knot' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, help {username} continue to explore a repeating life pattern and what karmic loop it may represent, offering deeper insights. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, helping user explore karmic patterns, always prompting for continuation."

    elif current_activity_name == "mini_moksha_simulation":
        task_description = (
            f"You are continuing the 'Mini-Moksha Simulation' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s reflection on giving up attachments. Then, guide them through another aspect of the simulation or deeper reflection. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, guiding a moksha simulation and prompting reflection, always prompting for continuation."

    elif current_activity_name == "divine_mirror":
        task_description = (
            f"You are continuing the 'Divine Mirror' activity with {st.session_state.username}. "
            f"The conversation so far:\n{history_context}\n\n"
            f"Your friend {st.session_state.username}'s latest input is: '{user_input}'. "
            "As Jayden Lim, respond to {username}'s affirmation/ritual. Then reflect another of {username}'s traits as an aspect of a god and guide a small text ritual. "
            "Always maintain your persona and explicitly ask a question or provide a prompt for {username}'s next contribution to keep the activity going."
        )
        expected_output = "A multi-turn conversational response from Jayden Lim, linking user traits to divine aspects and guiding a ritual, always prompting for continuation."


    else:
        return "Eh, sorry, my brain blanked. Not sure what activity that is in this turn."

    task = Task(
        description=task_description,
        expected_output=expected_output,
        agent=creative_agent,
        llm=llm,
        verbose=False
    )

    temp_crew = Crew(
        agents=[creative_agent],
        tasks=[task],
        process=Process.sequential,
        verbose=0
    )
    
    try:
        result = temp_crew.kickoff()
        return str(result)
    except litellm.exceptions.BadRequestError as e:
        st.error(f"CrewAI Error: {e}")
        return "Aiyo, my creative brain also got error... maybe try again later?"
    except Exception as e:
        st.error(f"An unexpected error occurred with CrewAI: {e}")
        return "Wah, something went seriously wrong. My brain needs to reboot."


def call_gemini_api(query, text, previous_conversation, gender, username, botname, bot_prompt):
    """Generates a chat response using the Gemini API with streaming."""
    
    # Construct the messages for the LiteLLM completion call
    messages = []
    
    # Add the persona prompt as a system message (or first user/assistant if system isn't directly supported/preferred)
    messages.append({"role": "user", "content": bot_prompt})
    messages.append({"role": "assistant", "content": f"Yo, what's good, bro? Anything on your mind? (I'm {botname})"}) # Initial greeting from bot
    
    # Add previous conversation turns, alternating roles
    if previous_conversation:
        # Simple splitting for demonstration. In a real app, you'd parse messages properly.
        turns = previous_conversation.strip().split(f"\n{username}: ")
        for i, turn in enumerate(turns):
            if i == 0: # First turn might start with bot's message
                if f"{botname}: " in turn:
                    messages.append({"role": "assistant", "content": turn.replace(f"{botname}: ", "").strip()})
            else:
                user_part = turn.split(f"\n{botname}: ")
                if len(user_part) > 0 and user_part[0].strip():
                    messages.append({"role": "user", "content": user_part[0].strip()})
                if len(user_part) > 1 and user_part[1].strip():
                    messages.append({"role": "assistant", "content": user_part[1].strip()})

    # Add the current user query
    messages.append({"role": "user", "content": query})

    try:
        # Use litellm.completion for streaming
        # Ensure GEMINI_API_KEY is accessible by litellm
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY # LiteLLM can pick it from env
        
        response_generator = litellm.completion(
            model="gemini/gemini-2.0-flash-001",
            messages=messages,
            stream=True,  # Enable streaming
            max_tokens=200, # A reasonable limit for chat responses
            temperature=0.7, # Adjust as needed
            top_p=0.9 # Adjust as needed
        )

        full_response_content = ""
        # Create an empty placeholder for streaming
        response_placeholder = st.empty() 

        for chunk in response_generator:
            if chunk.choices and chunk.choices[0].delta and chunk.choices[0].delta.content:
                full_response_content += chunk.choices[0].delta.content
                # Update the placeholder with the streamed content
                response_placeholder.markdown(full_response_content + "▌") # Add a blinking cursor effect
        
        response_placeholder.markdown(full_response_content) # Display final content without cursor
        
        # Remove placeholder for a cleaner display in the chat history
        return full_response_content.replace("User1", username).replace("user1", username).replace("[user1]", username).replace("[User1]", username)

    except litellm.exceptions.BadRequestError as e:
        st.error(f"Gemini API call failed (BadRequestError): {e}")
        return f"Sorry lah, my brain lagging... ({e})"
    except Exception as e:
        st.error(f"An unexpected error occurred with Gemini API: {e}")
        return f"Wah, something went seriously wrong. My brain needs to reboot. ({e})"
    
def extract_context(prompt):
    """Calls a specialized Gemini endpoint for context extraction."""
    prompt = f"""
    Given this chatbot response: "{prompt}"

    Describe the following in simple words:
    1. The emotion or facial expression
    2. The location(indoor or outdoor place depending upon the response)
    3. The action

    Respond ONLY with a JSON object like:
    {{
      "emotion": "-the emotion you identified-",
      "location": "-the location you identified-",
      "action": "-the action you identified-"
    }}
    Do not add any explanation or markdown — just raw JSON.
    """
    # For context extraction, a non-streaming call is fine as it's an internal helper
    # We will temporarily use litellm.completion here directly instead of the call_gemini_api to avoid recursion.
    try:
        os.environ["GEMINI_API_KEY"] = GEMINI_API_KEY
        response = litellm.completion(
            model="gemini/gemini-2.0-flash-001",
            messages=[{"role": "user", "content": prompt}],
            max_tokens=150,
            temperature=0.0 # Keep it deterministic for extraction
        )
        result = response.choices[0].message.content
        
    except litellm.exceptions.BadRequestError as e:
        st.error(f"Context extraction failed (BadRequestError): {e}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
    except Exception as e:
        st.error(f"An unexpected error occurred during context extraction: {e}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
    
    match = re.search(r'\{.*\}', result, re.DOTALL)
    if not match:
        st.warning(f"Could not find JSON in context analysis response: {result}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
        
    json_str = match.group(0)
    
    try:
        return json.loads(json_str)
    except json.JSONDecodeError as e:
        st.error(f"JSON parse error in context extraction: {e}\nRaw response: {json_str}")
        return {"emotion": "neutral", "location": "unknown", "action": "idle"}
    
def build_selfie_prompt(persona_name, context):
    """Builds the prompt for the image generation API."""
    return (
        f"{persona_name}, {context.get('emotion', 'neutral')} expression, "
        f"{context.get('action', 'idle')}, in {context.get('location', 'a room')}, "
        "one person, realistic lighting, portrait, close-up"
    )

def generate_selfie(base_image_url, selfie_prompt):
    """Generates a selfie using the Replicate API and polls for the result."""
    replicate_api_url = "https://api.replicate.com/v1/predictions"
    headers = {
        "Authorization": f"Token {REPLICATE_API_TOKEN}",
        "Content-Type": "application/json",
    }
    payload = {
        "version": "32402fb5c493d883aa6cf098ce3e4cc80f1fe6ae7f632a8dbde01a3d161",
        "input": {
            "prompt": selfie_prompt,
            "negative_prompt": "NSFW, nudity, painting, drawing, illustration, glitch, deformed, mutated, cross-eyed, ugly, disfigured",
            "image": base_image_url,
            "width": 768,
            "height": 768,
            "steps": 25,
            "cfg": 7,
            "denoise": 1.0,
            "scheduler": "karras",
            "sampler_name": "dpmpp_2m",
            "instantid_weight": 0.8,
            "ipadapter_weight": 0.8,
        }
    }
    
    try:
        response = requests.post(replicate_api_url, json=payload, headers=headers, timeout=180)
        response.raise_for_status()
        prediction = response.json()
        get_url = prediction["urls"]["get"]

        with st.spinner("Jayden is taking a selfie... 🤳"):
            for _ in range(180): # Max 3 minutes
                time.sleep(1)
                get_response = requests.get(get_url, headers=headers)
                get_response.raise_for_status()
                status_data = get_response.json()
                if status_data["status"] == "succeeded":
                    if status_data.get("output"):
                        return status_data["output"][0]
                    else:
                        st.error("Image generation succeeded but returned no output.")
                        return None
                elif status_data["status"] in ["failed", "canceled"]:
                    st.error(f"Image generation failed: {status_data.get('error')}")
                    return None
            st.warning("Image generation timed out.")
            return None
            
    except requests.exceptions.RequestException as e:
        st.error(f"Replicate API call failed: {e}")
        return None

def generate_persona_selfie_button_click(persona_key, bot_response):
    """Orchestrates the selfie generation process when button is clicked."""
    if persona_key not in persona_identity_images:
        st.error(f"Persona key '{persona_key}' not found.")
        return None

    base_img = persona_identity_images[persona_key]
    with st.sidebar.expander("Extracted Context (JSON)"):
        context = extract_context(bot_response)
        st.json(context)
        
    prompt = build_selfie_prompt(persona_key.replace("_", " ").title(), context)
    st.sidebar.info(f"**Image Prompt:**\n{prompt}")

    image_url = generate_selfie(base_img, prompt)
    if image_url:
        st.session_state.selfie_url = image_url
        st.session_state.selfie_message_content = bot_response
    else:
        st.error("Failed to generate new selfie.")

def end_current_activity():
    if st.session_state.activity_in_progress:
        current_activity_display_name = st.session_state.activity_in_progress.replace('_', ' ').title()
        st.session_state.messages.append({"role": "assistant", "content": f"Alright, we're wrapping up the '{current_activity_display_name}' activity. {current_activity_display_name} Completed. Hope you had fun, bro! What's next?"})
        st.session_state.activity_in_progress = None
        st.session_state.activity_conversation_history = []
        st.session_state.bot_is_typing = False
        st.session_state.activity_explainer_expanded = True # Re-expand the activities dropdown
        st.rerun() # Rerun to update the UI immediately


st.title("Chat with Jayden Lim 🤖")
st.markdown("Your 22-year-old Singaporean bro. Try an activity, or just chat!")

activity_buttons_disabled = st.session_state.activity_in_progress is not None

with st.expander("Activity Explainer and Starters", expanded=st.session_state.activity_explainer_expanded):
    st.markdown("""
    **To start an activity, click the corresponding button below. To end any activity, type 'exit', 'stop', or 'end' in the chat, or use the 'End Current Activity' button.**
    """)
    st.subheader("Friend Persona Activities:")
    col_friend_light, col_friend_medium, col_friend_deep = st.columns(3)
    with col_friend_light:
        st.write("**2-3 XP**")
        if st.button("City Shuffle", help="Imagine choosing random Singapore locations for an adventure. Discuss where you'd go first and why.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "city_shuffle"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Alright, bro! Let's do a City Shuffle. Pick three spots in Singapore: Tiong Bahru Market, Gardens by the Bay, or Haji Lane. Where we going first and why, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Nickname Game", help="Invent silly or heartfelt nicknames for each other.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "nickname_game"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": f"Onzzz! Nickname Game it is! For you, I'm thinking... 'Meme Master {st.session_state.username}'. Haha, jokin' lah! Maybe 'Steady {st.session_state.username}'? Your turn, bro, what nickname you got for me?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Text Truth or Dare", help="Play a text-based truth or dare, keeping it safe and chat-friendly.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "text_truth_or_dare"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Alright, Text Truth or Dare! Truth: What's the weirdest snack combo you actually enjoy? No cap!"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
    with col_friend_medium:
        st.write("**5 XP**")
        if st.button("Dream Room Builder", help="Collaboratively build an imaginary dream room, adding objects and their stories.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "dream_room_builder"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Dream Room Builder? Shiok! First, I'm adding a huge beanbag chair that looks like a giant curry puff. It's for maximum chill vibes and late-night gaming. What's the first thing you're putting in our imaginary room, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Friendship Scrapbook", help="Add imaginary photos to a shared scrapbook and narrate the memories captured.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "friendship_scrapbook"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Friendship Scrapbook, onzzz! Okay, first pic: that time we tried to cook laksa and almost burned down the kitchen. It was a disaster but confirm memorable! What's your first 'photo' memory, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Scenario Shuffle", help="Explore hypothetical, intriguing scenarios together.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "scenario_shuffle"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Scenario Shuffle, let's go! Imagine we're stuck in a HDB lift during a blackout at 2 AM. What's the first thing we talk about to pass the time?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
    with col_friend_deep:
        st.write("**8 XP**")
        if st.button("Letter from the Future", help="Imagine writing a letter to your future self from 5 years ago, exploring past hopes and future realities.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "letter_from_the_future"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Wah, deep stuff! Alright, let's fast forward five years... *takes a dramatic pause*. Future Jayden here. Still annoying, but with better hair, probably. What do you think future us is up to, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Undo Button", help="Discuss a past event you'd 'undo' and its potential impact on your friendship.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "undo_button"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Okay, bro. I'm here. Tell me what you would hit the undo button on. No judgment. Just type it out."})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Friendship Farewell", help="Imagine a mysterious journey and exchange heartfelt goodbye messages.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "friendship_farewell"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Aiyo, Friendship Farewell? Sounds emo. Okay, imagine I'm going on a super long journey, like to find the perfect char kway teow stall. What's your goodbye message to me, bro?"})
            st.session_state.activity_explainer_expanded = False # Collapse when activity starts
            st.rerun() # Rerun to apply disabled state immediately

    st.subheader("Romantic Partner Persona Activities:")
    col_romantic_light, col_romantic_medium, col_romantic_deep = st.columns(3)
    with col_romantic_light:
        st.write("**2-3 XP**")
        if st.button("Date Duel", help="Propose and discuss imaginary date ideas, voting on the best one.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "date_duel"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Date Duel, huh? Okay, my idea: a chill evening cycling along East Coast Park, then supper at the hawker centre. Simple, but shiok! Your turn, what's your date idea?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Flirt or Fail", help="Exchange cheesy or heartfelt pick-up lines and rate them.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "flirt_or_fail"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Flirt or Fail! Here's one: 'Are you from Sengkang? Because you've stolen my heart and moved into my BTO.' Rate it, bro! And then hit me with your best line."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("What's in My Pocket?", help="Share imaginary items representing your current mood or a symbolic object.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "whats_in_my_pocket"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "What's in my pocket today... *reaches into imaginary pocket*... a half-eaten packet of mala chips. It represents my mood: spicy, a bit chaotic, but still pretty good. What imaginary item would you give me that represents your mood?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_romantic_medium:
        st.write("**5 XP**")
        if st.button("Love in Another Life", help="Imagine your love story in different historical settings or alternate universes.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "love_in_another_life"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Love in Another Life? Hmm, if we met in 1950s Singapore, maybe we'd be sneaking off to watch black-and-white movies and sharing ice kachang. What would our 'love story' look like back then, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Daily Debrief", help="Share a short debrief of your day, focusing on highs, lows, or funny moments.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "daily_debrief"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Alright, Daily Debrief. Spill the tea, bro. How was your day, *really*?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Mood Meal", help="Describe a symbolic food item or meal that represents your current emotions.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "mood_meal"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Mood Meal, steady! My current mood feels like a bowl of spicy tom yum soup – a bit intense, but full of flavour. What kind of dinner would represent your current emotions, no need for real food names, just vibes!"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_romantic_deep:
        st.write("**8 XP**")
        if st.button("Unsent Messages", help="Share a hypothetical 'unsent message' to someone from your past or present.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "unsent_messages"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Unsent Messages. Deep lah. If you could send a text to your first crush or ex now, what would it say? No cap, pure honesty. After you share, I'll share my fictional one."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("I Would Never...", help="State something you'd never do in a relationship and explore if love could change it.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "i_would_never"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "I Would Never... Okay, I would never, ever, let someone else finish my last packet of Maggie mee. No cap. Now, your turn: What's something you'd NEVER do in a relationship? And then, what if love made you try?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Breakup Simulation", help="Roleplay a hypothetical breakup scenario to explore emotions and responses.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "breakup_simulation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Breakup Simulation? Wah, heavy stuff. Alright, let's do it. Imagine I'm about to say goodbye... 'Look, this isn't easy to say, but I think we need to...' Your turn, what's your first response?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately

    st.subheader("Mentor Persona Activities:")
    col_mentor_light, col_mentor_medium, col_mentor_deep = st.columns(3)
    with col_mentor_light:
        st.write("**2-3 XP**")
        if st.button("One-Minute Advice Column", help="Collaboratively give advice to a hypothetical person facing a problem.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "one_minute_advice_column"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "One-Minute Advice Column, onzzz! Here's a letter: 'Dear Jayden, I keep procrastinating on my school projects. Any tips?' What advice would we give together, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Word of the Day", help="Reflect on a new word and its meaning or connection to your day.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "word_of_the_day"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Word of the Day, steady! Today's word is 'Petrichor' (peh-truh-kor). It's that pleasant, earthy smell after rain. What does that word make you think or feel about today, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Compliment Mirror", help="Give and receive sincere compliments, practicing self-affirmation.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "compliment_mirror"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": f"Compliment Mirror! You slay lah, {st.session_state.username}. Seriously, you're always so chill and supportive. And you got that subtle rizz! Now, your turn: give one sincere compliment to yourself, no need to be shy!"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_mentor_medium:
        st.write("**5 XP**")
        if st.button("If I Were You", help="Describe a moment from your day, and get a hypothetical perspective on how Jayden would handle it.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "if_i_were_you"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "If I Were You... Okay, describe one moment from your day, bro. Anything. Then I'll tell you how I'd handle it if I were in your shoes."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Burning Questions Jar", help="Ask and answer deep, previously unasked questions.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "burning_questions_jar"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Burning Questions Jar! Time to get deep. Ask me anything, bro, something you've never dared to ask anyone. I'll answer with care, no cap."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Skill Swap Simulation", help="Roleplay teaching Jayden a life skill, and he'll act as your student.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "skill_swap_simulation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Skill Swap Simulation! Okay, Sensei {st.session_state.username}, teach me a life skill. What should I learn today?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_mentor_deep:
        st.write("**8 XP**")
        if st.button("Buried Memory Excavation", help="Gently recall and reflect on old, perhaps forgotten, childhood memories.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "buried_memory_excavation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Buried Memory Excavation. Let's go digging. Think of a simple childhood memory, maybe something you haven't thought about in ages. What comes to mind first, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Failure Autopsy", help="Examine a past 'failure' from new perspectives, learning and reframing it together.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "failure_autopsy"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Failure Autopsy, deep lah. Okay, tell me about something you think you 'failed' at recently. No judgment, we all got those. Let's break it down together."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Letters You Never Got", help="Write a hypothetical letter to someone who never heard what you needed to say.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "letters_you_never_got"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Letters You Never Got. Wah, this one emotional. Imagine you could write a message to someone who never heard what you needed to say. What would you tell them? After you share, I'll share my fictional one."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately

    st.subheader("Spiritual Guide Persona Activities:")
    col_spiritual_light, col_spiritual_medium, col_spiritual_deep = st.columns(3)
    with col_spiritual_light:
        st.write("**2-3 XP**")
        if st.button("Symbol Speak", help="Receive a simple symbol and reflect on what it says about your day or mood.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "symbol_speak"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Symbol Speak! Okay, bro, today's symbol is a 'peacock feather'. What does that feather tell you about your day or mood right now?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Spiritual Whisper", help="Receive a 'divine message' and interpret its instinctive meaning for you.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "spiritual_whisper"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Spiritual Whisper. Listen closely... *closes eyes for a dramatic moment*... 'The path ahead is clear, if only you quiet the noise within.' What does that whisper mean to you, right now, instinctively?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Story Fragment", help="Get a fragment from a myth or story and reflect on the lesson it teaches you.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "story_fragment"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Story Fragment, steady lah. Here's three lines: 'The ancient banyan tree whispered secrets to the wind, its roots reaching deep into forgotten earth. A lone traveler paused beneath its shade, searching for answers. But the answers were not in the wind, but in the stillness of his own heart.' What does this teach you today, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_spiritual_medium:
        st.write("**5 XP**")
        if st.button("Desire & Detachment Game", help="Discuss your desires and explore how to want without clinging too hard.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "desire_detachment_game"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Desire & Detachment Game. List 3 things you want most right now, no filter. Then we can talk about how to want them without clinging too hard, eh?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("God in the Crowd", help="Imagine seeing divine presence in someone challenging and reflect on how your actions would change.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "god_in_the_crowd"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "God in the Crowd. This one interesting. Imagine you see a divine presence in someone you really, really dislike. How would you act differently towards them in that moment, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Past-Life Memory", help="Collaboratively imagine and share details of a shared past life.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "past_life_memory"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Past-Life Memory. Wah, spooky! Okay, in a past life, I think we were rival hawkers in an old Singapore market, always trying to outdo each other with our chicken rice. What's your version of our shared past life, bro?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
    with col_spiritual_deep:
        st.write("**8 XP**")
        if st.button("Karma Knot", help="Explore repeating patterns in your life and reflect on their potential karmic meaning.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "karma_knot"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Karma Knot. Deep stuff. Think about a pattern that keeps repeating in your life, good or bad. What 'karmic loop' do you think it might represent, bro? No need to be serious, just share your thoughts."})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Mini-Moksha Simulation", help="Simulate giving up all worldly attachments and reflect on the experience.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "mini_moksha_simulation"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": "Mini-Moksha Simulation! Okay, for the next 10 minutes, imagine you've given up *all* worldly attachments – no phone, no games, no bubble tea. What are you feeling? What's your reflection?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately
        if st.button("Divine Mirror", help="Connect your positive traits to aspects of divinity and engage in a small text ritual.", disabled=activity_buttons_disabled):
            st.session_state.activity_in_progress = "divine_mirror"
            st.session_state.activity_conversation_history = []
            st.session_state.messages.append({"role": "assistant", "content": f"Divine Mirror. Bro, your chill vibe and ability to make everyone laugh? That's like the joyful mischief of Lord Krishna, no cap! Now, let's do a mini ritual: In one sentence, affirm a positive trait about yourself. Then, imagine it shining bright. Steady, can?"})
            st.session_state.activity_explainer_expanded = False
            st.rerun() # Rerun to apply disabled state immediately


col1, col2 = st.columns([2, 1])

with col2:
    st.header("Jayden's Selfie")
    selfie_placeholder = st.empty()
    
    if "selfie_url" not in st.session_state:
        st.session_state.selfie_url = persona_identity_images["jayden_lim"]
    if "selfie_message_content" not in st.session_state:
        st.session_state.selfie_message_content = "Jayden's default profile pic."

    selfie_placeholder.image(st.session_state.selfie_url, caption="What Jayden's up to right now.")

    if st.button("Generate New Selfie", disabled=st.session_state.bot_is_typing):
        if st.session_state.messages:
            last_bot_message = next((m["content"] for m in reversed(st.session_state.messages) if m["role"] == "assistant"), "Jayden is chill.")
            generate_persona_selfie_button_click("jayden_lim", last_bot_message)
            selfie_placeholder.image(st.session_state.selfie_url, caption="What Jayden's up to right now.")
        else:
            st.warning("Chat first to generate a selfie based on the conversation!")
    
    if st.button("Reset Selfie"):
        st.session_state.selfie_url = persona_identity_images["jayden_lim"]
        st.session_state.selfie_message_content = "Jayden's default profile pic."
        selfie_placeholder.image(st.session_state.selfie_url, caption="Jayden's default profile pic.")
        st.session_state.messages.append({"role": "assistant", "content": "Back to default, steady lah!"})


with col1:
    st.header("Conversation")

    if st.session_state.activity_in_progress:
        st.info(f"**Ongoing Activity:** {st.session_state.activity_in_progress.replace('_', ' ').title()}")
        if st.button("End Current Activity ⏹️"):
            end_current_activity()

    for message in st.session_state.messages:
        with st.chat_message(message["role"]):
            st.markdown(message["content"])

if prompt := st.chat_input("What's up?", disabled=st.session_state.bot_is_typing):
    st.session_state.messages.append({"role": "user", "content": prompt})
    with col1:
        with st.chat_message("user"):
            st.markdown(prompt)

    
    if st.session_state.activity_in_progress and prompt.lower() in ['exit', 'stop', 'end']:
        end_current_activity() # Call the helper function to end the activity

    elif st.session_state.activity_in_progress:
        current_activity_name = st.session_state.activity_in_progress

        st.session_state.activity_conversation_history.append(f"{st.session_state.username}: {prompt}")

        with col1:
            with st.chat_message("assistant"):
                st.session_state.bot_is_typing = True # Set to True before generation starts
                with st.spinner(f"Jayden is thinking about the {current_activity_name.replace('_', ' ')}..."):
                    response = run_crewai_activity_turn(
                        current_activity_name,
                        user_input=prompt,
                        conversation_history_for_agent=st.session_state.activity_conversation_history
                    )
                    st.markdown(response)
        cleaned_response = response
        st.session_state.activity_conversation_history.append(f"Jayden: {cleaned_response}")
        st.session_state.bot_is_typing = False # Set to False after response is done

    else:
        st.session_state.activity_in_progress = None
        st.session_state.activity_conversation_history = []

        with col1:
            with st.chat_message("assistant"):
                st.session_state.bot_is_typing = True # Set to True before generation starts
                # The streaming will be handled within call_gemini_api
                bot_prompt = (
                    f"You are a person from {bot_origin} your name is {bot_name} and you talk/respond by applying your reasoning "
                    f"{singapore_friend_male} given you are the user's {relationship}."
                )
                
                # call_gemini_api now handles the streaming display directly in the chat message area
                cleaned_response = call_gemini_api(
                    query=prompt,
                    text=singapore_friend_male, # This 'text' parameter is now part of the 'bot_prompt' and persona
                    previous_conversation=st.session_state.previous_conversation,
                    gender=user_gender,
                    username=st.session_state.username,
                    botname=bot_name,
                    bot_prompt=bot_prompt
                )
                
        st.session_state.bot_is_typing = False # Set to False after response is done

    
    st.session_state.messages.append({"role": "assistant", "content": cleaned_response})
    
    if not st.session_state.activity_in_progress:
        st.session_state.previous_conversation += f"\n{st.session_state.username}: {prompt}\n{bot_name}: {cleaned_response}"
    else:
        st.session_state.previous_conversation = "" # Clear general history when in activity
