import streamlit as st
from openai import OpenAI
from pydantic import BaseModel

# ── Page config ───────────────────────────────────────────────────────────────
st.set_page_config(page_title="Research Agent", page_icon="🔍", layout="centered")

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ── Pydantic model for structured output (Part D) ────────────────────────────
class ResearchSummary(BaseModel):
    main_answer: str
    key_facts: list[str]
    source_hint: str

# ── Session state defaults ────────────────────────────────────────────────────
if "last_response_id" not in st.session_state:
    st.session_state.last_response_id = None
if "conversation" not in st.session_state:
    st.session_state.conversation = []  # list of {"role": str, "content": str}

# ── Sidebar controls ──────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Agent Settings")
    structured_mode = st.checkbox("Return structured summary", value=False)
    streaming_mode  = st.checkbox("Enable streaming", value=False)
    if st.button("🗑️ Clear conversation"):
        st.session_state.last_response_id = None
        st.session_state.conversation = []
        st.rerun()

# ── Title ─────────────────────────────────────────────────────────────────────
st.title("🔍 Research Agent")
st.caption("Powered by the OpenAI Responses API · Web search enabled 🌐")

# ── Render stored conversation history ───────────────────────────────────────
for msg in st.session_state.conversation:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# ── Chat input ────────────────────────────────────────────────────────────────
placeholder_text = (
    "Ask a follow-up question…"
    if st.session_state.last_response_id
    else "Ask a question…"
)
user_input = st.chat_input(placeholder_text)

if user_input:
    # 1. Show & store user message
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.conversation.append({"role": "user", "content": user_input})

    previous_id = st.session_state.last_response_id

    # 2. Call the API and show assistant response
    with st.chat_message("assistant"):

        # ── Streaming (non-structured) ────────────────────────────────────────
        if streaming_mode and not structured_mode:
            try:
                with client.responses.stream(
                    model="gpt-4o",
                    instructions="You are a helpful research assistant. Always cite your sources when using web search.",
                    input=user_input,
                    tools=[{"type": "web_search_preview"}],
                    previous_response_id=previous_id,
                ) as stream:
                    box = st.empty()
                    collected = ""
                    for event in stream:
                        if hasattr(event, "delta") and hasattr(event.delta, "text"):
                            collected += event.delta.text
                            box.markdown(collected + "▌")
                    box.markdown(collected)
                    final = stream.get_final_response()

                st.session_state.last_response_id = final.id
                st.session_state.conversation.append({"role": "assistant", "content": collected})

            except Exception as e:
                st.error(f"Streaming error: {e}")

        # ── Structured output ─────────────────────────────────────────────────
        elif structured_mode:
            try:
                with st.spinner("Thinking…"):
                    response = client.responses.parse(
                        model="gpt-4o",
                        instructions="You are a helpful research assistant. Always cite your sources when using web search.",
                        input=user_input,
                        tools=[{"type": "web_search_preview"}],
                        previous_response_id=previous_id,
                        text_format=ResearchSummary,
                    )

                summary: ResearchSummary = response.output_parsed

                st.markdown(f"**Answer:** {summary.main_answer}")
                st.markdown("**Key facts:**")
                for fact in summary.key_facts:
                    st.markdown(f"- {fact}")
                st.caption(f"Source hint: {summary.source_hint}")

                # Build a plain text version to store in history
                facts_md = "\n".join(f"- {f}" for f in summary.key_facts)
                display_text = (
                    f"**Answer:** {summary.main_answer}\n\n"
                    f"**Key facts:**\n{facts_md}\n\n"
                    f"*Source hint: {summary.source_hint}*"
                )

                st.session_state.last_response_id = response.id
                st.session_state.conversation.append({"role": "assistant", "content": display_text})

            except Exception as e:
                st.error(f"Structured output error: {e}")

        # ── Plain response ────────────────────────────────────────────────────
        else:
            try:
                with st.spinner("Thinking…"):
                    response = client.responses.create(
                        model="gpt-4o",
                        instructions="You are a helpful research assistant. Always cite your sources when using web search.",
                        input=user_input,
                        tools=[{"type": "web_search_preview"}],
                        previous_response_id=previous_id,
                    )

                st.markdown(response.output_text)

                st.session_state.last_response_id = response.id
                st.session_state.conversation.append({"role": "assistant", "content": response.output_text})

            except Exception as e:
                st.error(f"API error: {e}")