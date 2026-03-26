import streamlit as st
from openai import OpenAI
from pydantic import BaseModel

# ── Page config ──────────────────────────────────────────────────────────────
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
    st.session_state.conversation = []   # list of {"role": str, "content": str}

# ── Sidebar controls ─────────────────────────────────────────────────────────
with st.sidebar:
    st.header("⚙️ Agent Settings")
    structured_mode = st.checkbox("Return structured summary", value=False)
    streaming_mode  = st.checkbox("Enable streaming", value=False)
    if st.button("🗑️ Clear conversation"):
        st.session_state.last_response_id = None
        st.session_state.conversation = []
        st.rerun()

# ── Title & description ───────────────────────────────────────────────────────
st.title("🔍 Research Agent")
st.caption("Powered by the OpenAI Responses API · Web search enabled 🌐")

# ── Helper: display conversation history ─────────────────────────────────────
def render_history():
    for msg in st.session_state.conversation:
        with st.chat_message(msg["role"]):
            st.markdown(msg["content"])

render_history()

# ── Helper: make a Responses API call ────────────────────────────────────────
def call_responses_api(user_input: str, previous_id: str | None):
    """Calls client.responses.create() or .parse() based on sidebar toggles."""

    base_kwargs = dict(
        model="gpt-4o",
        instructions=(
            "You are a helpful research assistant. "
            "Always cite your sources when using web search."
        ),
        input=user_input,
        tools=[{"type": "web_search_preview"}],
        previous_response_id=previous_id,
    )

    # ── Part D: structured output ────────────────────────────────────────────
    if structured_mode:
        response = client.responses.parse(
            **base_kwargs,
            text_format=ResearchSummary,
        )
        summary: ResearchSummary = response.output_parsed

        # Build a markdown string for history storage
        facts_md = "\n".join(f"- {f}" for f in summary.key_facts)
        display_text = (
            f"**Answer:** {summary.main_answer}\n\n"
            f"**Key facts:**\n{facts_md}\n\n"
            f"*Source hint: {summary.source_hint}*"
        )
        return response, display_text, summary

    # ── Part E: streaming ────────────────────────────────────────────────────
    if streaming_mode:
        return "stream", None, None   # handled separately below

    # ── Default: plain create ────────────────────────────────────────────────
    response = client.responses.create(**base_kwargs)
    return response, response.output_text, None


# ── Streaming helper ──────────────────────────────────────────────────────────
def stream_response(user_input: str, previous_id: str | None):
    """Streams the response and returns (response_id, full_text)."""
    with client.responses.stream(
        model="gpt-4o",
        instructions=(
            "You are a helpful research assistant. "
            "Always cite your sources when using web search."
        ),
        input=user_input,
        tools=[{"type": "web_search_preview"}],
        previous_response_id=previous_id,
    ) as stream:
        placeholder = st.empty()
        collected = ""
        for event in stream:
            # text_delta events carry incremental text
            if hasattr(event, "delta") and hasattr(event.delta, "text"):
                collected += event.delta.text
                placeholder.markdown(collected + "▌")
        placeholder.markdown(collected)
        final = stream.get_final_response()
        return final.id, collected


# ── Chat input ────────────────────────────────────────────────────────────────
user_input = st.chat_input(
    "Ask a question…" if not st.session_state.last_response_id
    else "Ask a follow-up question…"
)

if user_input:
    # Show user message immediately
    with st.chat_message("user"):
        st.markdown(user_input)
    st.session_state.conversation.append({"role": "user", "content": user_input})

    previous_id = st.session_state.last_response_id

    with st.chat_message("assistant"):

        # ── Streaming branch ─────────────────────────────────────────────────
        if streaming_mode and not structured_mode:
            response_id, display_text = stream_response(user_input, previous_id)
            st.session_state.last_response_id = response_id

        # ── Non-streaming branch ─────────────────────────────────────────────
        else:
            with st.spinner("Thinking…"):
                response, display_text, summary = call_responses_api(
                    user_input, previous_id
                )

            st.session_state.last_response_id = response.id

            if structured_mode and summary:
                # Render structured fields nicely
                st.markdown(f"**Answer:** {summary.main_answer}")
                st.markdown("**Key facts:**")
                for fact in summary.key_facts:
                    st.markdown(f"- {fact}")
                st.caption(f"Source hint: {summary.source_hint}")
            else:
                st.markdown(display_text)

    st.session_state.conversation.append(
        {"role": "assistant", "content": display_text or ""}
    )