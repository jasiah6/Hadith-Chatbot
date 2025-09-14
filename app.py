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
def get_local_hadith_grouped(query):
    """Searches local hadiths and groups them by book."""
    query_lower = query.lower()
    grouped = defaultdict(list)
    for h in local_hadiths:
        if query_lower in h.get("topic", "").lower() or query_lower in h.get("text", "").lower():
            grouped[h.get("book", "Unknown")].append(h["text"])
    if not grouped:
        st.warning("No matching hadith found locally.")
    return grouped

def get_random_local_hadith():
    """Returns a random hadith from the local JSON file."""
    if not local_hadiths:
        return {"text": "Hadith dataset is empty."}
    return random.choice(local_hadiths)

def get_hadith_from_api(search_query=None, book_slug=None, hadith_number=None):
    """
    Fetches hadiths from HadithAPI.com.
    - If search_query is provided, it performs a keyword search.
    - If book_slug and hadith_number are provided, it fetches a specific hadith.
    Returns a list of hadith objects or an error message string.
    """
    try:
        api_key = st.secrets["api_key"]
    except (FileNotFoundError, KeyError):
        return "⚠️ API key not found. Please add it to your Streamlit secrets."

    base_url = f"https://hadithapi.com/api/hadiths?apiKey={api_key}"
    
    if search_query:
        url = f"{base_url}&hadithEnglish={search_query}"
    elif book_slug and hadith_number:
        url = f"{base_url}&book={book_slug}&hadithNumber={hadith_number}"
    else:
        return "⚠️ Invalid request. Provide either a search query or a book/number."

    try:
        res = requests.get(url)
        res.raise_for_status()
        data = res.json()
        
        # The 'hadiths' key contains the main payload from the API.
        hadiths_payload = data.get("hadiths")

        if isinstance(hadiths_payload, dict):
            # For search results, the API returns a paginated object.
            # The actual list of hadiths is inside the 'data' key.
            return hadiths_payload.get("data", [])
        elif isinstance(hadiths_payload, list):
            # For specific hadith lookups, the API may return a simple list.
            return hadiths_payload
        else:
            # If the payload is neither or None, return an empty list.
            return []
        
    except requests.exceptions.HTTPError as e:
        if e.response.status_code == 401:
            return "⚠️ API Error: Unauthorized. Your API key is invalid."
        return f"⚠️ API HTTP Error: {e}"
    except requests.exceptions.RequestException as e:
        return f"⚠️ API request failed: {e}"
    except Exception as e:
        return f"⚠️ An unknown error occurred: {e}"

# --------- Streamlit UI ----------
# Header
if image:
    st.image(image, use_container_width =True)
st.title("📖 Hadith Chatbot")
st.markdown("Search, explore, or get a random Hadith from local files or a live API.")

# Sidebar
st.sidebar.title("Settings")
mode = st.sidebar.radio("Choose data source:", ["Local JSON (Offline)", "API (HadithAPI.com)"])
st.sidebar.markdown("---")
st.sidebar.markdown("Developed by **Jasiah**")
st.sidebar.info(
    "ℹ️ **Local JSON mode** is fast and works offline.\n\n"
    "**API mode** fetches live data and requires a valid API key."
)

# Input + Search Button
col1, col2 = st.columns([3, 1])
with col1:
    query = st.text_input("Enter a topic (e.g., 'prayer') or type 'random':", key="query_input")
with col2:
    st.write("")
    st.write("")
    search_btn = st.button("Search")

# --------- Search / Random logic ----------
if search_btn:
    if not query.strip():
        st.warning("Please enter a topic or 'random'.")
        st.stop()

    # --- RANDOM HADITH LOGIC ---
    if query.strip().lower() == "random":
        st.subheader("🎲 Random Hadith")
        if mode == "Local JSON (Offline)":
            h = get_random_local_hadith()
            with st.container(border=True):
                st.markdown(f"**Book:** {h.get('book','Unknown')}")
                st.markdown(f"**Text:** {h.get('text', 'No text available.')}")
        else: # API Mode
            with st.spinner("Fetching a random hadith from the API..."):
                random_book = random.choice([
                    "sahih-bukhari", "sahih-muslim", "al-tirmidhi", "abu-dawood", 
                    "ibn-e-majah", "sunan-nasai"
                ])
                random_number = random.randint(1, 200)
                
                results = get_hadith_from_api(book_slug=random_book, hadith_number=random_number)
                
                if isinstance(results, str):
                    st.error(results)
                elif not results:
                    st.warning("Could not fetch a random hadith. The selected number might not exist. Please try again.")
                else:
                    h = results[0]
                    with st.container(border=True):
                        st.markdown(f"**Book:** {h.get('book', {}).get('bookName', 'Unknown')}")
                        st.markdown(f"**Chapter:** {h.get('chapter', {}).get('chapterEnglish', 'N/A')}")
                        st.markdown(f"**Text:** {h.get('hadithEnglish', 'No text available.')}")

    # --- SEARCH LOGIC ---
    else:
        st.subheader(f"Results for: '{query}'")
        if mode == "Local JSON (Offline)":
            results_grouped = get_local_hadith_grouped(query)
            for book, texts in results_grouped.items():
                with st.expander(f"📖 {book} ({len(texts)} found)"):
                    for t in texts:
                        st.markdown(f"- {t}")
        else: # API Mode
            with st.spinner(f"Searching API for '{query}'..."):
                results = get_hadith_from_api(search_query=query)

                if isinstance(results, str):
                    st.error(results)
                elif not results:
                    st.warning(f"No hadiths found for your query '{query}' via the API.")
                else:
                    st.success(f"Found {len(results)} hadiths matching your query.")
                    for h in results:
                        with st.container(border=True):
                            st.markdown(f"**📖 Book:** {h.get('book', {}).get('bookName', 'Unknown')}")
                            st.markdown(f"**Chapter:** {h.get('chapter', {}).get('chapterEnglish', 'N/A')}")
                            st.markdown(f"**Text:** {h.get('hadithEnglish', 'No text available.')}")
                        st.markdown("---")
