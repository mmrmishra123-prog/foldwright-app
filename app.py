import streamlit as st
from neo4j import GraphDatabase
import google.generativeai as genai
from google.api_core.exceptions import ResourceExhausted, TooManyRequests
import time
import json

# --- Page config (must be first Streamlit call) ---
st.set_page_config(page_title="Foldwright", page_icon="🧬", layout="centered")

# --- Config from secrets.toml ---
NEO4J_URI = st.secrets["NEO4J_URI"]
NEO4J_USERNAME = st.secrets["NEO4J_USERNAME"]
NEO4J_PASSWORD = st.secrets["NEO4J_PASSWORD"]
DB_NAME = st.secrets["DB_NAME"]
GEMINI_API_KEY = st.secrets["GEMINI_API_KEY"]

genai.configure(api_key=GEMINI_API_KEY)
model = genai.GenerativeModel("gemini-3.6-flash")
driver = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USERNAME, NEO4J_PASSWORD))

# ============================================================
# STYLING — field-notebook / bioluminescence theme
# ============================================================
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Fraunces:ital,opsz,wght@0,9..144,300..700;1,9..144,400..600&family=Space+Grotesk:wght@400;500;600&family=IBM+Plex+Mono:wght@400;500&display=swap');

:root {
    --ink: #152C29;
    --paper: #F6F3EA;
    --glow: #8FE3A0;
    --coral: #FF8B76;
    --sage: #5C6B5E;
}

.stApp {
    background-color: var(--paper);
}

/* kill the default streamlit top padding a bit */
.block-container {
    padding-top: 3rem;
    max-width: 700px;
}

/* Header */
.foldwright-hero {
    text-align: center;
    margin-bottom: 0.3rem;
}
.foldwright-hero h1 {
    font-family: 'Fraunces', serif;
    font-weight: 500;
    font-style: italic;
    font-size: 3rem;
    color: var(--ink);
    margin-bottom: 0.2rem;
    letter-spacing: -0.01em;
}
.foldwright-underline {
    display: block;
    margin: 0 auto 1.1rem auto;
    width: 140px;
}
.foldwright-tagline {
    font-family: 'Space Grotesk', sans-serif;
    color: var(--sage);
    font-size: 1.02rem;
    text-align: center;
    margin-bottom: 2.4rem;
    line-height: 1.5;
}

/* Label above input */
.foldwright-label {
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 500;
    color: var(--ink);
    font-size: 0.95rem;
    margin-bottom: 0.4rem;
}

/* Text input styled like a notebook line, not a boxed field */
.stTextInput > div > div > input {
    background-color: transparent;
    border: none;
    border-bottom: 2px solid #C9C2AC;
    border-radius: 0;
    color: var(--ink);
    font-family: 'Space Grotesk', sans-serif;
    font-size: 1.15rem;
    padding: 0.5rem 0.1rem;
}
.stTextInput > div > div > input:focus {
    border-bottom: 2px solid var(--glow);
    box-shadow: none;
}
.stTextInput label { display: none; }

/* Button — coral pill */
.stButton > button {
    background-color: var(--coral);
    color: var(--ink);
    border: none;
    border-radius: 999px;
    padding: 0.55rem 1.6rem;
    font-family: 'Space Grotesk', sans-serif;
    font-weight: 600;
    font-size: 0.95rem;
    margin-top: 1rem;
    transition: transform 0.15s ease, background-color 0.15s ease;
}
.stButton > button:hover {
    background-color: #ff7a63;
    transform: translateY(-1px);
}
.stButton > button:active {
    transform: translateY(0px);
}

/* Interpreted-goal chip */
.goal-chip {
    display: inline-block;
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.82rem;
    color: var(--ink);
    background-color: rgba(143, 227, 160, 0.35);
    border: 1px solid var(--glow);
    padding: 0.3rem 0.8rem;
    border-radius: 999px;
    margin: 1.4rem 0 1.6rem 0;
}

/* Specimen card */
.specimen {
    background-color: #FFFEFA;
    border-radius: 4px;
    padding: 1.1rem 1.3rem 1.1rem 1.3rem;
    margin-bottom: 1rem;
    position: relative;
    border-left: 4px solid var(--glow);
}
.specimen-index {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.75rem;
    color: var(--sage);
    margin-bottom: 0.35rem;
}
.specimen-title {
    font-family: 'IBM Plex Mono', monospace;
    font-weight: 500;
    font-size: 1.25rem;
    color: var(--ink);
    margin-bottom: 0.15rem;
}
.specimen-position {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.85rem;
    color: var(--sage);
    margin-bottom: 0.7rem;
}
.specimen-explanation {
    font-family: 'Space Grotesk', sans-serif;
    font-size: 0.97rem;
    color: var(--ink);
    line-height: 1.55;
    margin-bottom: 0.6rem;
}
.specimen-source {
    font-family: 'IBM Plex Mono', monospace;
    font-size: 0.78rem;
    color: var(--sage);
    border-top: 1px solid #EDE9DC;
    padding-top: 0.5rem;
    margin-top: 0.4rem;
}
.specimen-score-track {
    background-color: #EDE9DC;
    border-radius: 999px;
    height: 6px;
    width: 100%;
    margin-bottom: 0.85rem;
    overflow: hidden;
}
.specimen-score-fill {
    background-color: var(--coral);
    height: 6px;
    border-radius: 999px;
}
</style>
""", unsafe_allow_html=True)

# ============================================================
# PIPELINE FUNCTIONS
# ============================================================

def generate_explanation(prompt, max_retries=5, base_delay=8):
    for attempt in range(max_retries):
        try:
            response = model.generate_content(prompt)
            time.sleep(3)
            return response.text
        except (ResourceExhausted, TooManyRequests):
            wait = base_delay * (2 ** attempt)
            st.info(f"Quota's catching its breath — retrying in {wait}s...")
            time.sleep(wait)
    raise RuntimeError("Gemini rate limit exceeded after all retries.")


def interpret_goal(user_goal):
    prompt = f"""Classify this protein engineering goal into JSON with two fields:
- effect_type: one of "brightness", "folding", "color_shift", or "other"
- direction: "increase" or "decrease"

Goal: "{user_goal}"

Respond with ONLY the JSON object, nothing else."""
    text = generate_explanation(prompt)
    text = text.strip().strip("```json").strip("```").strip()
    return json.loads(text)


def get_context_for_position(driver, db_name, position):
    query = """
    MATCH (r:Residue {position: $position})
    OPTIONAL MATCH (r)-[:HAS_MUTATION]->(m:Mutation)
    OPTIONAL MATCH (v:Variant)-[:INCLUDES]->(m)
    OPTIONAL MATCH (v)-[:HAS_EFFECT]->(e:Effect)
    OPTIONAL MATCH (m)-[:DOCUMENTED_IN]->(s:Source)
    RETURN r.position AS position, r.wildtype_aa AS wildtype_aa,
           r.buried AS buried, r.rsa AS rsa,
           m.notation AS notation, m.esm2_score AS esm2_score,
           m.blosum62_score AS blosum62_score, m.conservation_score AS conservation_score,
           v.notation AS variant_notation,
           e.description AS effect_description, e.effect_type AS effect_type, e.direction AS direction,
           s.citation AS source, s.doi AS doi
    """
    with driver.session(database=db_name) as session:
        result = session.run(query, position=position)
        record = result.single()
        return dict(record) if record else None


def get_ranked_candidates(driver, db_name, effect_type=None, top_n=8):
    query = """
    MATCH (r:Residue)-[:HAS_MUTATION]->(m:Mutation)
    WHERE m.esm2_score IS NOT NULL AND m.blosum62_score IS NOT NULL
    OPTIONAL MATCH (v:Variant)-[:INCLUDES]->(m)
    OPTIONAL MATCH (v)-[:HAS_EFFECT]->(e:Effect)
    RETURN m.notation AS notation, m.position AS position,
           m.esm2_score AS esm2, m.blosum62_score AS blosum62,
           m.conservation_score AS conservation,
           e.effect_type AS effect_type
    """
    with driver.session(database=db_name) as session:
        results = [dict(r) for r in session.run(query)]

    for r in results:
        cons = r["conservation"] if r["conservation"] is not None else 0
        r["combined_score"] = (0.15 * r["esm2"]) + (0.40 * r["blosum62"]) + (0.45 * cons)

    if effect_type:
        matched = [r for r in results if r["effect_type"] == effect_type]
        unmatched = [r for r in results if r["effect_type"] != effect_type]
        matched.sort(key=lambda x: x["combined_score"], reverse=True)
        unmatched.sort(key=lambda x: x["combined_score"], reverse=True)
        ranked = matched + unmatched
    else:
        ranked = sorted(results, key=lambda x: x["combined_score"], reverse=True)

    return ranked[:top_n]


def get_full_context(driver, db_name, candidates):
    enriched = []
    for c in candidates:
        context = get_context_for_position(driver, db_name, c["position"])
        c["context"] = context
        enriched.append(c)
    return enriched


def generate_all_explanations(candidates):
    for c in candidates:
        has_source = c["context"] is not None and c["context"].get("source") is not None
        if has_source:
            prompt = f"""Mutation {c['notation']} at position {c['position']}.
Documented effect: {c['context'].get('effect_description')}
Source: {c['context'].get('source')}
ESM-2 score: {c['esm2']:.3f}, BLOSUM62: {c['blosum62']:.3f}

In 2-4 sentences, explain why this mutation might help, using ONLY the facts above. Reference the documented source."""
        else:
            cons = c.get('conservation')
            cons_str = f"{cons:.3f}" if cons is not None else "not available"
            prompt = f"""Mutation {c['notation']} at position {c['position']} has no documented literature source.
ESM-2 score: {c['esm2']:.3f}, BLOSUM62: {c['blosum62']:.3f}, Conservation: {cons_str}

In 2-4 sentences, explain what these scores suggest, being explicit that this is a model-based prediction, not a documented result."""
        c["explanation"] = generate_explanation(prompt)
    return candidates


def run_pipeline(driver, db_name, user_goal):
    goal_info = interpret_goal(user_goal)
    candidates = get_ranked_candidates(driver, db_name, effect_type=goal_info["effect_type"], top_n=8)
    candidates = get_full_context(driver, db_name, candidates)
    candidates = generate_all_explanations(candidates)
    return candidates, goal_info


# ============================================================
# UI
# ============================================================

st.markdown("""
<div class="foldwright-hero">
    <h1>Foldwright</h1>
</div>
<svg class="foldwright-underline" viewBox="0 0 140 12" xmlns="http://www.w3.org/2000/svg">
    <path d="M2 8 Q 20 2, 38 8 T 74 8 T 110 8 T 138 6" stroke="#8FE3A0" stroke-width="2.5" fill="none" stroke-linecap="round"/>
</svg>
<div class="foldwright-tagline">
    Type a goal, get ranked mutations with sources attached where they exist.<br>
</div>
""", unsafe_allow_html=True)

st.markdown('<div class="foldwright-label">What are you trying to achieve?</div>', unsafe_allow_html=True)
user_goal = st.text_input("goal", placeholder="e.g. make GFP brighter", label_visibility="collapsed")
run_clicked = st.button("Get suggestions")

if run_clicked:
    if not user_goal.strip():
        st.warning("Type a goal first — even a rough one works.")
    else:
        with st.spinner("Searching the specimen record..."):
            try:
                candidates, goal_info = run_pipeline(driver, DB_NAME, user_goal)

                st.markdown(
                    f'<div class="goal-chip">interpreted as → {goal_info["effect_type"]} / {goal_info["direction"]}</div>',
                    unsafe_allow_html=True
                )

                max_score = max((c["combined_score"] for c in candidates), default=1) or 1

                for i, c in enumerate(candidates, start=1):
                    bar_pct = max(min(c["combined_score"] / max_score, 1.0), 0.03) * 100
                    source_html = ""
                    if c["context"] and c["context"].get("source"):
                        source_html = f'<div class="specimen-source">source — {c["context"]["source"]}</div>'

                    st.markdown(f"""
                    <div class="specimen">
                        <div class="specimen-index">specimen {i:02d}</div>
                        <div class="specimen-title">{c['notation']}</div>
                        <div class="specimen-position">position {c['position']} · combined score {c['combined_score']:.3f}</div>
                        <div class="specimen-score-track">
                            <div class="specimen-score-fill" style="width:{bar_pct:.0f}%;"></div>
                        </div>
                        <div class="specimen-explanation">{c['explanation']}</div>
                        {source_html}
                    </div>
                    """, unsafe_allow_html=True)

            except RuntimeError as e:
                st.error(str(e))