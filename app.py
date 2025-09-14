import streamlit as st
import requests
import random
import json
from PIL import Image
from collections import defaultdict

# --------- Load banner image ----------
try:
    image = Image.open("image/hadith_banner.png")
except FileNotFoundError:
    image = None

# --------- Load local hadiths ----------
try:
    with open("hadiths.json", "r", encoding="utf-8") as f:
        local_hadiths = json.load(f)
except Exception as e:
    st.error(f"Error loading hadiths.json: {e}")
    local_hadiths = []

# --------- Session state for random Hadith ----------
if "random_hadith" not in st.session_state:
    st.session_state.random_hadith = None

# --------- Functions ----------
def get_local_hadith(query):
    query_lower = query.lower()
    results = [
        h for h in local_hadiths
        if query_lower in h.get("topic", "").lower() or query_lower in h.get("text", "").lower()
    ]
    return results if results else [{"text": "No matching hadith found locally."}]

def get_local_hadith_grouped(query):
    query_lower = query.lower()
    grouped = defaultdict(list)
    for h in local_hadiths:
        if query_lower in h.get("topic", "").lower() or query_lower in h.get("text", "").lower():
            grouped[h.get("book", "Unknown")].append(h["text"])
    if not grouped:
        grouped["No matching hadith found locally."].append("")
    return grouped

def get_random_local_hadith():
    if not local_hadiths:
        return {"text": "Hadith dataset is empty."}
    return random.choice(local_hadiths)

def get_hadith_from_api(collection="bukhari", number=1):
    url = f"https://hadithapi.com/api/hadiths?apiKey=MY_API_KEY&book={collection}&hadithNumber={number}"
    try:
        res = requests.get(url).json()
        return res.get("hadiths", [{}])[0].get("hadithEnglish", "No hadith found.")
    except Exception as e:
        return f"⚠️ API error: {e}"

# --------- Streamlit UI ----------
# Header
if image:
    st.image(image, use_container_width=True)
st.title("📖 Hadith Chatbot")
st.markdown("Search, explore, or get a random Hadith from 200+ Hadiths.")

# Sidebar
mode = st.sidebar.radio("Choose mode:", ["Local JSON", "API (HadithAPI.com)"])
st.sidebar.markdown("Developed by Jasiah")
st.sidebar.info(
    "ℹ️ Local JSON mode is faster and offline-friendly.\n"
    "API mode requires a valid API key."
)

# Input + Search Button
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Type a topic or 'random':")
with col2:
    search_btn = st.button("Search")

# --------- Search / Random logic ----------
if search_btn:
    if not query.strip():
        st.warning("Please type a topic or 'random'.")
    elif query.strip().lower() == "random":
        if mode == "Local JSON":
            st.session_state.random_hadith = get_random_local_hadith()
            h = st.session_state.random_hadith
            st.success(
                f"🎲 **Random Hadith**\n\n**Book:** {h.get('book','')}\n\n**Text:** {h['text']}"
            )
        else:
            st.success(get_hadith_from_api())
    else:
        if mode == "Local JSON":
            results_grouped = get_local_hadith_grouped(query)
            for book, texts in results_grouped.items():
                with st.expander(f"📖 {book}"):
                    for t in texts:
                        st.write(f"- {t}")
        else:
            st.success(get_hadith_from_api())
