import hashlib
from html import escape
import streamlit as st
from engine import MovieEngine
from movies import MOVIES

st.set_page_config(page_title="Movie Match", page_icon="🎬", layout="wide")

st.markdown("""
<style>
.stApp { background: #141414; color: #fff; }
header[data-testid="stHeader"] { background: transparent; }
.logo { color: #E50914; font-size: 2.4rem; font-weight: 800; letter-spacing: 1px; margin: 0; }
.tag { color: #b3b3b3; margin: 0 0 1rem 0; }
.section { font-size: 1.3rem; font-weight: 700; margin: 1.6rem 0 .6rem 0; }
.card { border-radius: 6px; padding: 14px; height: 215px; display: flex;
        flex-direction: column; justify-content: flex-end; margin-bottom: 14px; }
.card h4 { margin: 0 0 4px 0; font-size: 1rem; color: #fff; }
.card .meta { color: #d2d2d2; font-size: .78rem; }
.card .match { color: #46d369; font-weight: 700; font-size: .85rem; }
.feat { border-radius: 8px; padding: 28px; min-height: 230px; display: flex;
        flex-direction: column; justify-content: flex-end; }
.feat h1 { margin: 0; font-size: 2.2rem; color: #fff; }
.feat p { max-width: 640px; color: #e5e5e5; }
</style>
""", unsafe_allow_html=True)


@st.cache_resource(show_spinner="Loading model and movie vectors (first run downloads the model)...")
def get_engine():
    return MovieEngine()


def bg(title, a=26, b=14):
    hue = int(hashlib.md5(title.encode()).hexdigest()[:6], 16) % 360
    return f"linear-gradient(160deg, hsl({hue},50%,{a}%), hsl({(hue+40)%360},45%,{b}%))"


def card_html(m):
    return (f'<div class="card" style="background:{bg(m["title"])}">'
            f'<div class="match">{m["match"]}% Match</div>'
            f'<h4>{escape(m["title"])}</h4>'
            f'<div class="meta">{m["year"]} | {escape(", ".join(m["genres"]))}</div></div>')


def set_query(text):
    st.session_state.q = text


engine = get_engine()

st.markdown('<p class="logo">MOVIE MATCH</p>', unsafe_allow_html=True)
st.markdown('<p class="tag">Type a movie name or describe what you feel like watching.</p>', unsafe_allow_html=True)

query = st.text_input("Search", key="q", label_visibility="collapsed",
                      placeholder="Try: Inception, or 'funny movies about friendship'")
all_genres = sorted({g for m in MOVIES for g in m["genres"]})
genres = st.multiselect("Filter by genre", all_genres)

examples = ["Inception", "movies about dreams", "heartwarming animated family film", "dark crime thriller"]
cols = st.columns(len(examples))
for col, ex in zip(cols, examples):
    col.button(ex, on_click=set_query, args=(ex,), use_container_width=True)

if query.strip():
    featured, results = engine.search(query, genres=genres or None, top_k=10)

    if featured:
        st.markdown(
            f'<div class="feat" style="background:{bg(featured["title"], 32, 12)}">'
            f'<h1>{escape(featured["title"])}</h1>'
            f'<div class="meta">{featured["year"]} | {escape(", ".join(featured["genres"]))}</div>'
            f'<p>{escape(featured["overview"])}</p></div>', unsafe_allow_html=True)
        st.markdown('<div class="section">More like this</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="section">Top matches for "{escape(query)}"</div>', unsafe_allow_html=True)

    if not results:
        st.info("No movies match these genres. Remove a genre filter to see more results.")
    for start in range(0, len(results), 5):
        row = st.columns(5)
        for col, m in zip(row, results[start:start + 5]):
            col.markdown(card_html(m), unsafe_allow_html=True)
else:
    st.markdown('<div class="section">Start by searching above or pick an example.</div>', unsafe_allow_html=True)
