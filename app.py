import streamlit as st
import requests
from groq import Groq

# ============================================
# Setup
# ============================================
client = Groq(api_key=st.secrets["GROQ_API_KEY"])

st.set_page_config(page_title="🌍 TravelBot", page_icon="✈️")
st.title("🌍 TravelBot - Your AI Travel Assistant")

# ============================================
# Session State (Memory)
# ============================================
if "conversation_history" not in st.session_state:
    st.session_state.conversation_history = []

if "user_profile" not in st.session_state:
    st.session_state.user_profile = {"name": None}

if "bot_state" not in st.session_state:
    st.session_state.bot_state = {"waiting_for": "city", "city": None}

if "chat_messages" not in st.session_state:
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "👋 Hello! I'm TravelBot 🌍\nWhere do you want to go?"}
    ]

# ============================================
# Weather Feature
# ============================================
def get_weather(city):
    try:
        url = f"https://wttr.in/{city}?format=3"
        response = requests.get(url, timeout=5)
        if response.status_code == 200:
            return f"🌤️ {response.text.strip()}"
        return None
    except:
        return None

def extract_city(text):
    cities = ["paris", "london", "dubai", "cairo", "tokyo",
              "rome", "barcelona", "istanbul", "bangkok", "amsterdam",
              "new york", "sydney", "singapore", "berlin", "madrid"]
    for city in cities:
        if city in text.lower():
            return city.title()
    return None

# ============================================
# Trip Planner via Groq
# ============================================
def chat_with_groq(prompt, system="You are TravelBot, a friendly travel assistant."):
    response = client.chat.completions.create(
        model="llama3-8b-8192",
        messages=[
            {"role": "system", "content": system},
            {"role": "user", "content": prompt}
        ],
        max_tokens=500,
        temperature=0.7
    )
    return response.choices[0].message.content

def get_trip_plan(city):
    return chat_with_groq(
        prompt=f"Plan a detailed 3-day trip to {city}. Include places to visit, local food, and travel tips.",
        system="You are TravelBot, an expert trip planner. Be specific, helpful, and well-organized."
    )

# ============================================
# Smart Response Handler
# ============================================
def handle_user_input(user_message):
    bot_state = st.session_state.bot_state
    user_profile = st.session_state.user_profile

    # Save name
    if "my name is" in user_message.lower():
        name = user_message.lower().split("my name is")[-1].strip().split()[0].title()
        user_profile["name"] = name

    # Goodbye
    goodbyes = ["bye", "goodbye", "thanks", "thank you", "done", "that's all"]
    if any(g in user_message.lower() for g in goodbyes):
        name_part = f" {user_profile['name']}" if user_profile["name"] else ""
        history = st.session_state.conversation_history
        cities_visited = [m["content"].replace("plan a trip to ", "")
                         for m in history if "plan a trip" in m["content"]]
        if cities_visited:
            cities = ", ".join(cities_visited)
            return (f"✈️ Safe travels{name_part}!\n"
                    f"📍 Cities you explored: {cities}\n"
                    f"Have an amazing trip! See you soon 🌍"), True
        return f"✈️ Safe travels{name_part}! See you soon 🌍", True

    # Greeting
    greetings = ["hello", "hi", "hey", "salam", "marhaba"]
    if any(g in user_message.lower() for g in greetings):
        name_part = f", {user_profile['name']}" if user_profile["name"] else ""
        bot_state["waiting_for"] = "city"
        return f"👋 Hello{name_part}! I'm TravelBot 🌍\nWhere do you want to go?", False

    # State 1: Waiting for city
    if bot_state["waiting_for"] == "city":
        city = extract_city(user_message)
        if city:
            bot_state["city"] = city
            bot_state["waiting_for"] = "action"
            return (f"Great choice! ✈️ {city}\n\n"
                    f"What do you want?\n"
                    f"1️⃣ Trip Plan\n"
                    f"2️⃣ Weather\n"
                    f"3️⃣ Both"), False
        return "I didn't recognize that city 😅\nTry: Paris, Tokyo, Dubai, Cairo, London...", False

    # State 2: Waiting for action
    if bot_state["waiting_for"] == "action":
        city = bot_state["city"]
        msg = user_message.lower()

        if msg in ["2", "weather"]:
            bot_state["waiting_for"] = "city"
            bot_state["city"] = None
            weather = get_weather(city)
            if weather:
                return f"{weather}\n\n🌍 Want to explore another city? Where to next?", False
            return f"Sorry, couldn't get weather for {city} 😅\n\n🌍 Try another city?", False

        if msg in ["1", "trip", "plan"]:
            bot_state["waiting_for"] = "want_weather"
            response = get_trip_plan(city)
            st.session_state.conversation_history.append(
                {"role": "user", "content": f"plan a trip to {city}"}
            )
            return f"{response}\n\n🌤️ Want weather for {city} too? (yes / no)", False

        if msg in ["3", "both"]:
            bot_state["waiting_for"] = "city"
            bot_state["city"] = None
            response = get_trip_plan(city)
            weather = get_weather(city)
            st.session_state.conversation_history.append(
                {"role": "user", "content": f"plan a trip to {city}"}
            )
            return (f"{response}\n\n"
                    f"{weather}\n\n"
                    f"🌍 Want to explore another city? Where to next?"), False

        return "Please choose:\n1️⃣ Trip Plan\n2️⃣ Weather\n3️⃣ Both", False

    # State 3: Want weather after trip plan
    if bot_state["waiting_for"] == "want_weather":
        city = bot_state["city"]
        msg = user_message.lower()

        if "yes" in msg or msg == "y":
            bot_state["waiting_for"] = "city"
            bot_state["city"] = None
            weather = get_weather(city)
            if weather:
                return f"{weather}\n\n🌍 Want to explore another city? Where to next?", False
            return f"Sorry, couldn't get weather 😅\n\n🌍 Where to next?", False
        else:
            bot_state["waiting_for"] = "city"
            bot_state["city"] = None
            return "🌍 Want to explore another city? Where to next?", False

    # General conversation
    response = chat_with_groq(user_message)
    return response, False

# ============================================
# Streamlit UI
# ============================================

# Show chat history
for msg in st.session_state.chat_messages:
    with st.chat_message(msg["role"]):
        st.write(msg["content"])

# Clear button
if st.button("🔄 Clear Memory"):
    st.session_state.conversation_history = []
    st.session_state.user_profile = {"name": None}
    st.session_state.bot_state = {"waiting_for": "city", "city": None}
    st.session_state.chat_messages = [
        {"role": "assistant", "content": "👋 Memory cleared! Where do you want to go? 🌍"}
    ]
    st.rerun()

# User input
user_input = st.chat_input("Type your message...")

if user_input:
    # Show user message
    st.session_state.chat_messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.write(user_input)

    # Get bot response
    with st.chat_message("assistant"):
        with st.spinner("Thinking... ✈️"):
            response, should_end = handle_user_input(user_input)
        st.write(response)

    st.session_state.chat_messages.append({"role": "assistant", "content": response})
    st.rerun()
