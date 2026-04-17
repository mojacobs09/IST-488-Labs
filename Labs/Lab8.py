import streamlit as st
import json
import os
from openai import OpenAI

# ─────────────────────────────────────────────
# CONFIG
# ─────────────────────────────────────────────
MEMORIES_FILE = "memories.json"
MAIN_MODEL = "gpt-4o-mini"
EXTRACT_MODEL = "gpt-4o-mini"

client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ─────────────────────────────────────────────
# PART B: MEMORY SYSTEM
# ─────────────────────────────────────────────

def load_memories() -> list[str]:
    """Load memories from memories.json. Returns empty list if file doesn't exist."""
    if os.path.exists(MEMORIES_FILE):
        with open(MEMORIES_FILE, "r") as f:
            return json.load(f)
    return []


def save_memories(memories: list[str]) -> None:
    """Save a list of memory strings to memories.json."""
    with open(MEMORIES_FILE, "w") as f:
        json.dump(memories, f, indent=2)


def extract_new_memories(user_msg: str, assistant_msg: str, existing_memories: list[str]) -> list[str]:
    """
    Use a cheap LLM call to extract new facts about the user from the latest exchange.
    Returns a list of new memory strings (may be empty).
    """
    existing_str = "\n".join(f"- {m}" for m in existing_memories) if existing_memories else "None"

    extraction_prompt = f"""You are a memory extraction assistant. Analyze the conversation exchange below and identify any NEW personal facts about the user worth remembering (e.g., name, age, location, major, job, hobbies, preferences, food, pets, goals, etc.).

Existing memories already saved (DO NOT duplicate these):
{existing_str}

User message: "{user_msg}"
Assistant response: "{assistant_msg}"

Return ONLY a JSON array of short, factual strings describing new facts about the user.
If there are no new facts worth saving, return an empty array: []
Do not include any explanation, markdown, or code fences — just raw JSON.

Example output: ["User's name is Alex", "User studies Computer Science", "User likes sushi"]"""

    response = client.chat.completions.create(
        model=EXTRACT_MODEL,
        messages=[{"role": "user", "content": extraction_prompt}],
        temperature=0,
        max_tokens=300,
    )

    raw = response.choices[0].message.content.strip()
    try:
        new_facts = json.loads(raw)
        if isinstance(new_facts, list):
            return [str(f) for f in new_facts]
    except (json.JSONDecodeError, ValueError):
        pass
    return []


# ─────────────────────────────────────────────
# PART C: CHATBOT
# ─────────────────────────────────────────────

def build_system_prompt(memories: list[str]) -> str:
    """Build the system prompt, injecting saved memories if any exist."""
    base = "You are a helpful, friendly assistant with long-term memory. You remember facts about the user across conversations."

    if memories:
        mem_str = "\n".join(f"- {m}" for m in memories)
        return (
            f"{base}\n\n"
            f"Here are things you remember about this user from past conversations:\n"
            f"{mem_str}\n\n"
            f"Use this information naturally when relevant — don't recite it robotically."
        )
    return base


def chat(messages: list[dict]) -> str:
    """Send messages to the LLM and return the assistant reply."""
    memories = load_memories()
    system_prompt = build_system_prompt(memories)

    response = client.chat.completions.create(
        model=MAIN_MODEL,
        messages=[{"role": "system", "content": system_prompt}] + messages,
        temperature=0.7,
    )
    return response.choices[0].message.content


# ─────────────────────────────────────────────
# STREAMLIT UI
# ─────────────────────────────────────────────

st.set_page_config(page_title="Memory Chatbot", page_icon="🧠", layout="wide")
st.title("🧠 Memory Chatbot")
st.caption("I remember you — even after you leave.")

# ── Sidebar: memory display ──────────────────
with st.sidebar:
    st.header("🗂️ Long-Term Memories")
    memories = load_memories()

    if memories:
        for i, mem in enumerate(memories, 1):
            st.markdown(f"**{i}.** {mem}")
    else:
        st.info("No memories yet. Start chatting!")

    st.divider()

    if st.button("🗑️ Clear All Memories", use_container_width=True):
        save_memories([])
        st.success("Memories cleared!")
        st.rerun()

    st.divider()
    st.caption(f"Model: `{MAIN_MODEL}`  |  Extractor: `{EXTRACT_MODEL}`")

# ── Session state: chat history ──────────────
if "messages" not in st.session_state:
    st.session_state.messages = []

# Display chat history
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ───────────────────────────────
if user_input := st.chat_input("Say something..."):
    # Show user message
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # Get assistant response
    with st.chat_message("assistant"):
        with st.spinner("Thinking..."):
            reply = chat(st.session_state.messages)
        st.markdown(reply)

    st.session_state.messages.append({"role": "assistant", "content": reply})

    # Extract and save new memories
    current_memories = load_memories()
    new_facts = extract_new_memories(user_input, reply, current_memories)

    if new_facts:
        updated = current_memories + new_facts
        save_memories(updated)
        st.rerun()  # Refresh sidebar to show new memories