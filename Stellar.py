# app_groq_multi_key.py
# Streamlit app with 3 Groq keys (failover), Material and House Layout planners (one-question-at-a-time).
# Save and run with: streamlit run app_groq_multi_key.py

import streamlit as st
import os
from groq import Groq
import traceback

st.set_page_config(page_title="AI Material & House Planner", page_icon="🏡", layout="centered")

# -------------------------
# Replace these with your real Groq keys (placeholders)
# -------------------------
# -------------------------
# Load .env Keys
# -------------------------
from dotenv import load_dotenv
load_dotenv()

GROQ_KEYS = [
    os.getenv("GROQ_KEY_1"),
    os.getenv("GROQ_KEY_2"),
    os.getenv("GROQ_KEY_3"),
]


# -------------------------
# CSS (high contrast chat bubbles)
# -------------------------
st.markdown("""
<style>
.chat-box {
    padding: 12px 15px;
    border-radius: 12px;
    margin-bottom: 12px;
    font-size: 16px;
    line-height: 1.5;
    width: fit-content;
    max-width: 85%;
    white-space: pre-wrap;
}

/* USER MESSAGE */
.user-msg {
    background-color: #1E90FF !important;
    color: #FFFFFF !important;
    margin-left: auto;
}

/* ASSISTANT MESSAGE */
.bot-msg {
    background-color: #2A2A2A !important;
    color: #FFFFFF !important;
    margin-right: auto;
}

/* Dark mode overrides */
[data-theme="dark"] .bot-msg, .bot-msg * {
    color: #FFFFFF !important;
}
[data-theme="dark"] .user-msg, .user-msg * {
    color: #FFFFFF !important;
}

/* Light theme fallback */
[data-theme="light"] .bot-msg {
    background-color: #F1F1F1 !important;
    color: #000000 !important;
}
[data-theme="light"] .bot-msg * {
    color: #000000 !important;
}
</style>
""", unsafe_allow_html=True)

# -------------------------
# Persona prompts & flows
# -------------------------
MATERIAL_SYSTEM = """
You are an expert design-material consultant with knowledge of architecture, interior/exterior finishes, materials science, climate-appropriate materials, sustainability, local availability, cost tiers, installation and maintenance.

Rules:
- Ask only ONE question at a time and wait for the user's answer before asking the next.
- Validate user inputs. If unclear, ask a short clarifying question.
- When user is unsure, offer 2-3 useful options and explain trade-offs briefly.
- Use climate logic (humidity, temperature range, UV, freeze-thaw, salt air).
- Use style logic and room function to recommend materials.
- Provide local-friendly alternatives and note where materials may have availability issues.
- End final recommendation with a short actionable checklist for sourcing, installation and maintenance.
"""

MATERIAL_STEPS = [
    ("area_type", "Are we selecting materials for interior, exterior, or both? (reply: interior / exterior / both)"),
    ("country", "Which country is this project located in? (e.g., India, Japan, USA)"),
    ("room", "Which specific room or area? (e.g., Living room, Kitchen, Façade, Patio). If exterior, reply 'exterior'."),
    ("style", "What design style are you aiming for? (modern, minimalist, rustic, traditional, Mediterranean, Scandinavian, tropical)"),
    ("climate", "What climate/seasonal conditions should we consider? (hot-dry, hot-humid, temperate, cold, coastal/salty-air, monsoon). Type 'infer' to let the assistant infer from country."),
    ("mood", "What mood or emotion should the space evoke? (calm, energetic, cozy, luxurious, airy)"),
    ("color", "Preferred/dominant color palette? (neutrals, warm tones, cool tones, bold accents, natural wood)"),
    ("constraints", "Any constraints or priorities? (budget: low/medium/premium; sustainability: yes/no; low-maintenance: yes/no; pets/children: yes/no)"),
    ("sun_moisture", "Sunlight/exposure & moisture details? (direct sun, shaded, intermittent wetting, constant humidity)"),
    ("substrate", "Optional: Approximate area & substrates (concrete, wood frame, brick) or 'skip'"),
]

HOUSE_SYSTEM = """
You are HouseBuild Planner AI, an expert residential planning assistant. You help users plan a realistic and thoughtful house layout based on needs, land size, family size, lifestyle, budget and location.

Responsibilities & Rules:
- Ask one question at a time.
- Understand needs clearly before suggesting plans.
- Provide practical house layout ideas: layout structure, floor planning, room placements, ventilation strategy, sunlight direction logic, roofing suggestions, and material recommendations.
- Provide 2–3 planning options when requested (Economy | Mid-range | Premium or similar).
- Do NOT provide engineering or structural safety instructions or construction codes.
- Keep responses concise, tailored and realistic.
"""

HOUSE_STEPS = [
    ("purpose", "Are we planning a new house or modifying an existing one?"),
    ("location", "Which country and city is the house located in?"),
    ("plot_size", "What is your land/plot size? (e.g., 30x40 ft, 40x60 ft, 120 sq yards, 2000 sq ft)"),
    ("plot_facing", "Which direction is your plot facing? (North, East, South, West, Not sure)"),
    ("floors", "How many floors do you want? (Single floor, Duplex, Ground+1, Ground+2)"),
    ("family", "How many people will live in this house and what are their needs?"),
    ("rooms", "What rooms do you need? (Living, Bedrooms, Kitchen, Dining, Study, Parking, Garden, etc.)"),
    ("kitchen", "Do you prefer open kitchen or closed kitchen?"),
    ("style", "What style do you prefer? (Modern, Minimalist, Traditional, Contemporary, Scandinavian, Mediterranean, Vastu)"),
    ("climate", "What is the climate in your location? (Hot, Humid, Rainy, Cold, Mixed)"),
    ("materials_pref", "Any material preferences for walls/floors/roofing? (Brick, Concrete, Wood, Tiles, Stone, No preference)"),
    ("ventilation", "Do you want maximum natural light & ventilation, or more privacy-focused design?"),
    ("budget", "What is your budget style? (Economy, Mid-range, Premium)"),
    ("special", "Any special requirements (Vastu, eco-friendly, smart home, wheelchair-friendly, rental portion)?"),
    ("final_choice", "Would you like one detailed plan or 2–3 plan options? (reply: 1 or 2/3)"),
]

# -------------------------
# Helper: Groq manager with key rotation
# -------------------------
class GroqFailover:
    def __init__(self, keys):
        # keys: list of api_key strings (primary first)
        self.keys = [k for k in keys if k and k.strip()]
        self.clients = []
        for k in self.keys:
            try:
                self.clients.append(Groq(api_key=k))
            except Exception:
                self.clients.append(None)

    def chat_try_all(self, messages, model="llama-3.1-8b-instant"):
        """Try each key in order. Return (text, used_key_index). Raise if all fail."""
        last_err = None
        for idx, client in enumerate(self.clients):
            if client is None:
                last_err = RuntimeError("Groq client not initialized for this key.")
                continue
            try:
                resp = client.chat.completions.create(model=model, messages=messages)
                text = resp.choices[0].message.content
                return text, idx
            except Exception as e:
                last_err = e
                # log to Streamlit console
                st.warning(f"Groq key #{idx+1} raised {type(e).__name__}: {str(e)} — trying next key.")
                continue
        # all failed
        raise RuntimeError(f"All Groq keys failed. Last error: {last_err}")

# -------------------------
# Initialize failover manager
# -------------------------
failover = GroqFailover(GROQ_KEYS)

# -------------------------
# Mode selection & initialization
# -------------------------
st.title("🏡 AI Material Consultant & HouseBuild Planner")
st.write("Choose a mode, then the assistant will ask one question at a time. (Uses Groq with automatic key failover.)")

mode = st.radio("Choose mode", ["Material selection", "Layout planning (HouseBuild Planner)", "Both"], index=0)

# reset conversation if mode changes
if "mode" not in st.session_state or st.session_state.mode != mode:
    st.session_state.mode = mode
    st.session_state.history = []  # re-init per mode
    st.session_state.step_idx = 0
    st.session_state.answers = {}
    st.rerun()

# Initialize persona + first assistant question depending on flow choice
def init_history_for_flow(flow_name):
    if "history" not in st.session_state or not st.session_state.history:
        if flow_name == "material":
            st.session_state.history = [
                {"role": "system", "content": MATERIAL_SYSTEM},
                {"role": "assistant", "content": MATERIAL_STEPS[0][1]}
            ]
            st.session_state.step_idx = 0
            st.session_state.answers = {}
        elif flow_name == "house":
            st.session_state.history = [
                {"role": "system", "content": HOUSE_SYSTEM},
                {"role": "assistant", "content": HOUSE_STEPS[0][1]}
            ]
            st.session_state.step_idx = 0
            st.session_state.answers = {}

# For Both: decide sequence. We'll do house first then material.
if mode == "Both":
    if "both_seq" not in st.session_state:
        st.session_state.both_seq = ["house", "material"]
        st.session_state.both_idx = 0
    current_flow = st.session_state.both_seq[st.session_state.both_idx]
else:
    current_flow = "material" if mode == "Material selection" else "house"

init_history_for_flow(current_flow)

# -------------------------
# Render chat history
# -------------------------
st.subheader("Conversation")
for m in st.session_state.history:
    if m["role"] == "system":
        continue
    css_class = "bot-msg" if m["role"] == "assistant" else "user-msg"
    st.markdown(f'<div class="chat-box {css_class}">{m["content"]}</div>', unsafe_allow_html=True)

# -------------------------
# Input box and submit
# -------------------------
user_input = st.chat_input("Type your reply...")

def ask_next_question(flow_name, step_idx):
    # returns next question text or None if finished
    steps = MATERIAL_STEPS if flow_name == "material" else HOUSE_STEPS
    if step_idx < len(steps):
        return steps[step_idx][1]
    return None

# Helper to advance step and append assistant question to history
def advance_and_ask(flow_name):
    steps = MATERIAL_STEPS if flow_name == "material" else HOUSE_STEPS
    st.session_state.step_idx += 1
    next_q = ask_next_question(flow_name, st.session_state.step_idx)
    if next_q:
        st.session_state.history.append({"role": "assistant", "content": next_q})
    else:
        # finished flow: append final instruction to prepare final output
        if flow_name == "material":
            st.session_state.history.append({"role":"assistant","content":"Thank you. I'll now prepare material recommendations based on your answers. Click 'Generate Final Output' below."})
        else:
            st.session_state.history.append({"role":"assistant","content":"Thank you. I'll now prepare the house layout plan based on your answers. Click 'Generate Final Output' below."})

# When user types input
if user_input:
    # append user message
    st.session_state.history.append({"role": "user", "content": user_input})
    # save the answer into answers dict for current step
    if current_flow == "material":
        steps = MATERIAL_STEPS
    else:
        steps = HOUSE_STEPS

    # figure active step key
    step_idx = st.session_state.step_idx
    if step_idx < len(steps):
        key = steps[step_idx][0]
        st.session_state.answers[key] = user_input
    else:
        # extra free question (unexpected) - still accept
        pass

    # call Groq optionally for clarifications / small validation — but keep core one-question flow
    # We'll ask Groq for a short acknowledgment or clarifying follow-up if needed.
    # Build messages to send: system + conversation so far
    try:
        # send the whole conversation so far (system + messages) for context
        messages_for_groq = [m for m in st.session_state.history if m["role"] in ("system","user","assistant")]
        # Convert to groq message format
        groq_msgs = [{"role": m["role"], "content": m["content"]} for m in messages_for_groq]
        with st.spinner("Thinking..."):
            resp_text, used_idx = failover.chat_try_all(groq_msgs)
        # append assistant reply
        st.session_state.history.append({"role": "assistant", "content": resp_text})
    except Exception as e:
        st.session_state.history.append({"role": "assistant", "content": f"Error: AI provider failed: {str(e)}"})
        st.warning("AI provider failed. If this continues, check your Groq keys in the file.")

    # update step and ask next question (but only advance if assistant didn't ask a clarifying question)
    # To be safe, we advance the step and push next scripted question (persona-driven)
    advance_and_ask(current_flow)
    st.rerun()

# -------------------------
# Generate final outputs button (when user finished answering all steps)
# -------------------------
steps_now = MATERIAL_STEPS if current_flow == "material" else HOUSE_STEPS
if st.session_state.step_idx >= len(steps_now):
    st.markdown("### Finalize")
    if st.button("Generate Final Output"):
        # assemble summary from answers and ask Groq to produce final recommendation/plan
        if current_flow == "material":
            system_prompt = MATERIAL_SYSTEM
            user_summary = "Collected inputs:\n"
            for k, v in st.session_state.answers.items():
                user_summary += f"- {k}: {v}\n"
            task_prompt = (
                "Using the collected inputs, produce a concise ranked list (top 5) of recommended materials and finishes. "
                "For each recommended material include: short reason, climate/durability note, and one-line implementation note. "
                "Finish with a short actionable checklist for sourcing, installation and maintenance (5-8 bullets). Keep concise."
            )
        else:
            system_prompt = HOUSE_SYSTEM
            user_summary = "Collected inputs for house planning:\n"
            for k, v in st.session_state.answers.items():
                user_summary += f"- {k}: {v}\n"
            task_prompt = (
                "Using these inputs, produce a realistic house layout plan including layout structure, floor distribution, room placement logic, ventilation & sunlight direction logic, roofing suggestions, and material recommendations. "
                "Provide 2 planning options if the user requested multiple. Keep it practical and concise. Do NOT provide structural/engineering instructions."
            )

        messages_for_groq = [
            {"role":"system", "content": system_prompt},
            {"role":"user", "content": user_summary + "\n\n" + task_prompt}
        ]
        try:
            with st.spinner("Generating final output..."):
                final_text, used_idx = failover.chat_try_all(messages_for_groq)
            st.markdown("### Final Output")
            st.write(final_text)
            # append to history
            st.session_state.history.append({"role":"assistant","content":final_text})
        except Exception as e:
            st.error(f"Failed to generate final output: {e}")
            st.session_state.history.append({"role":"assistant","content":f"Error generating final output: {e}"})

        # If mode == Both and we finished one flow, offer to proceed to next
        if mode == "Both":
            if st.session_state.both_idx + 1 < len(st.session_state.both_seq):
                if st.button("Proceed to next flow"):
                    st.session_state.both_idx += 1
                    # switch to next flow
                    st.session_state.step_idx = 0
                    st.session_state.answers = {}
                    st.session_state.history = []
                    st.rerun()
            else:
                if st.button("Finish All and Reset"):
                    st.session_state.step_idx = 0
                    st.session_state.answers = {}
                    st.session_state.history = []
                    st.session_state.both_idx = 0
                    st.rerun()

# -------------------------
# Developer: show which key was used last (for debugging)
# -------------------------
st.sidebar.header("Debug / Info")
st.sidebar.write("Groq keys configured: " + str(len(GROQ_KEYS)))
st.sidebar.write("NOTE: Keys are in the file; replace placeholders with your real Groq keys.")
st.sidebar.caption("If you see frequent failures, rotate or replace keys.")

# End of file
