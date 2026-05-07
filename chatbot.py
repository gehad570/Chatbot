import streamlit as st
import requests

# ============================================
# MEMORY (safe for Streamlit)
# ============================================

conversation_history = []
user_profile = {"name": None}
bot_state = {"waiting_for": None, "city": None}


def add_to_memory(role, content):
    conversation_history.append({"role": role, "content": content})


# ============================================
# SIMPLE WEATHER
# ============================================

def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=3"
        r = requests.get(url, timeout=5)
        return r.text
    except:
        return "Weather unavailable"


# ============================================
# CITY DETECTION
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
# MAIN HANDLER (NO MODEL - SAFE)
# ============================================

def handle_user_input(user_message):

    add_to_memory("user", user_message)

    msg = user_message.lower()

    # Greeting
    if "hello" in msg or "hi" in msg:
        return "👋 Hello! Where do you want to travel?"

    # Name
    if "my name is" in msg:
        name = user_message.split("my name is")[-1].strip().split()[0]
        user_profile["name"] = name.title()
        return f"Nice to meet you {user_profile['name']} 😊"

    # City detection
    city = extract_city(user_message)

    if city:
        weather = get_weather(city)

        response = f"""
✈️ Travel info for {city}

🌤️ Weather: {weather}

🗺️ Suggestion:
- Visit main attractions
- Try local food
- Explore city center
"""

        add_to_memory("assistant", response)
        return response

    # fallback chat
    response = "🌍 Tell me a city and I will plan your trip!"
    add_to_memory("assistant", response)

    return response
    
