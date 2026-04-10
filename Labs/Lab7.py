import streamlit as st
from openai import OpenAI
import requests
import base64

# ── Page config ──────────────────────────────────────────────────────────────
st.set_page_config(page_title="Image Caption Bot", page_icon="🖼️", layout="centered")

# ── OpenAI client ─────────────────────────────────────────────────────────────
client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])

# ── Session state ─────────────────────────────────────────────────────────────
if "url_response" not in st.session_state:
    st.session_state.url_response = None
if "url_image" not in st.session_state:
    st.session_state.url_image = None

if "upload_response" not in st.session_state:
    st.session_state.upload_response = None
if "upload_image_bytes" not in st.session_state:
    st.session_state.upload_image_bytes = None

# ── Shared prompt text ─────────────────────────────────────────────────────────
CAPTION_PROMPT = (
    "Describe the image in at least 3 sentences. "
    "Then write five different captions for this image. "
    "Captions must vary in length — minimum one word but no longer than 2 sentences. "
    "Captions should vary in tone, such as (but not limited to) funny, intellectual, and aesthetic."
)

# ── Header ────────────────────────────────────────────────────────────────────
st.title("🖼️ Image Caption Bot")
st.write("Generate creative captions for any image — paste a URL or upload a file.")
st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# PART A — Image URL
# ═════════════════════════════════════════════════════════════════════════════
st.header("Part A: Caption from URL")
st.caption("The URL must point **directly** to an image file (ending in .jpg, .png, .webp, etc.).")

url = st.text_input("Image URL", placeholder="https://example.com/photo.jpg")

if st.button("✨ Generate Captions from URL", key="url_btn"):
    if url:
        with st.spinner("Analyzing image..."):
            try:
                url_response = client.chat.completions.create(
                    model="gpt-5-2025-08-07",
                    max_completion_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": url, "detail": "auto"},
                                },
                                {"type": "text", "text": CAPTION_PROMPT},
                            ],
                        }
                    ],
                )
                st.session_state.url_response = url_response
                st.session_state.url_image = url
            except Exception as e:
                st.error(f"Error calling the API: {e}")
    else:
        st.warning("Please enter an image URL first.")

if st.session_state.url_response:
    st.image(st.session_state.url_image, caption="Your image", use_container_width=True)
    st.subheader("Description & Captions")
    st.write(st.session_state.url_response.choices[0].message.content)

st.divider()

# ═════════════════════════════════════════════════════════════════════════════
# PART B — File Upload
# ═════════════════════════════════════════════════════════════════════════════
st.header("Part B: Caption from Uploaded File")
st.caption("Supported formats: JPG, JPEG, PNG, WEBP, GIF")

uploaded = st.file_uploader(
    "Upload an image",
    type=["jpg", "jpeg", "png", "webp", "gif"],
    key="file_uploader",
)

if st.button("✨ Generate Captions from File", key="upload_btn"):
    if uploaded:
        with st.spinner("Analyzing image..."):
            try:
                # Encode the image to base64
                b64 = base64.b64encode(uploaded.read()).decode("utf-8")
                mime = uploaded.type          # e.g. "image/png"
                data_uri = f"data:{mime};base64,{b64}"

                upload_response = client.chat.completions.create(
                    model="gpt-5-2025-08-07",
                    max_completion_tokens=1024,
                    messages=[
                        {
                            "role": "user",
                            "content": [
                                {
                                    "type": "image_url",
                                    "image_url": {"url": data_uri, "detail": "low"},
                                },
                                {"type": "text", "text": CAPTION_PROMPT},
                            ],
                        }
                    ],
                )
                st.session_state.upload_response = upload_response
                # Reset file pointer so st.image() can read it again
                uploaded.seek(0)
                st.session_state.upload_image_bytes = uploaded.read()
            except Exception as e:
                st.error(f"Error calling the API: {e}")
    else:
        st.warning("Please upload an image file first.")

if st.session_state.upload_response:
    st.image(
        st.session_state.upload_image_bytes,
        caption="Your uploaded image",
        use_container_width=True,
    )
    st.subheader("Description & Captions")
    st.write(st.session_state.upload_response.choices[0].message.content)