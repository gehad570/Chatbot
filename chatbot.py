import streamlit as st
from transformers import AutoModelForCausalLM, AutoTokenizer
import torch
import requests

# ============================================
# LOAD MODEL (IMPORTANT - cached)
# ============================================

model_name = "google/flan-t5-small"

@st.cache_resource
def load_model():

    tokenizer = AutoTokenizer.from_pretrained(model_name)

    model = AutoModelForCausalLM.from_pretrained(
        model_name,
        device_map="auto",
        torch_dtype="auto"
    )

    return tokenizer, model

tokenizer, model = load_model()

# ============================================
# MEMORY SYSTEM
# ============================================

conversation_history = []
user_profile = {"name": None}
bot_state = {"waiting_for": None, "city": None}


def add_to_memory(role, content):
    conversation_history.append({"role": role, "content": content})


def get_memory_prompt():
    prompt = "You are TravelBot, a helpful travel assistant.\n"

    for msg in conversation_history[-10:]:
        if msg["role"] == "user":
            prompt += f"User: {msg['content']}\n"
        else:
            prompt += f"Assistant: {msg['content']}\n"

    prompt += "Assistant: "
    return prompt

# ============================================
# WEATHER
# ============================================

def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=3"
        r = requests.get(url, timeout=5)
        return r.text
    except:
        return "Weather unavailable"

# ============================================
# CITY DETECTOR
# ============================================

def extract_city(text):
    cities = [
        "paris", "london", "dubai", "cairo", "tokyo",
        "rome", "barcelona", "istanbul", "bangkok",
        "amsterdam", "new york", "sydney"
    ]

    for c in cities:
        if c in text.lower():
            return c.title()

    return None

# ============================================
# CHAT GENERATION
# ============================================

def generate_response(prompt):

    inputs = tokenizer(prompt, return_tensors="pt").to(model.device)

    output = model.generate(
        **inputs,
        max_new_tokens=200,
        temperature=0.7,
        pad_token_id=tokenizer.eos_token_id
    )

    response = tokenizer.decode(output[0], skip_special_tokens=True)

    return response

# ============================================
# MAIN HANDLER
# ============================================

def handle_user_input(user_message):

    # Save memory
    add_to_memory("user", user_message)

    # Greeting
    if "hello" in user_message.lower():
        return "👋 Hello! Where do you want to travel?"

    # City detection
    city = extract_city(user_message)

    if city:
        weather = get_weather(city)
        prompt = f"Plan a short 2-day trip to {city}"
        answer = generate_response(prompt)

        add_to_memory("assistant", answer)

        return f"✈️ Trip Plan for {city}\n\n{answer}\n\n🌤️ {weather}"

    # Normal chat
    prompt = get_memory_prompt()
    response = generate_response(prompt)

    add_to_memory("assistant", response)

    return response
