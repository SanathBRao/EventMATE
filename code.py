import streamlit as st
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.messages import HumanMessage, AIMessage
import google.generativeai as genai
import base64
from PIL import Image
from io import BytesIO
import os

# =========================================================
# 🔑 Default Login Credentials
# =========================================================
DEFAULT_USERNAME = "admin"
DEFAULT_PASSWORD = "12345"

if "logged_in" not in st.session_state:
    st.session_state.logged_in = False

# =========================================================
# 🔹 Gemini Setup
# =========================================================
load_pro.env
API_KEY = os.getenv("GOOGLE_API_KEY")
if API_KEY:
    genai.configure(api_key=API_KEY)
else:
    st.error("⚠️ GOOGLE_API_KEY not found in environment variables.")

# LangChain Text Model
llm_text = ChatGoogleGenerativeAI(model="gemini-2.0-flash")

# Gemini Image Model
image_model = genai.GenerativeModel("gemini-2.0-flash-preview-image")

# =========================================================
# 🔹 Chatbot State Initialization
# =========================================================
if "chat_history" not in st.session_state:
    st.session_state.chat_history = []  # for display
if "llm_history" not in st.session_state:
    st.session_state.llm_history = []  # structured conversation memory

# =========================================================
# 🔹 Login Page
# =========================================================
def login_page():
    st.title("🔑 Login")

    username = st.text_input("Username").strip().lower()
    password = st.text_input("Password", type="password").strip()

    if st.button("Login"):
        if username == DEFAULT_USERNAME.lower() and password == DEFAULT_PASSWORD:
            st.session_state.logged_in = True
            st.success("✅ Login successful!")
            st.rerun()
        else:
            st.error("❌ Invalid username or password")

# =========================================================
# 🔹 Chatbot Page
# =========================================================
def chatbot_page():
    st.title("🧠 Gemini Chatbot + 🎨 Image Generator")

    # Logout option
    if st.sidebar.button("Logout"):
        st.session_state.logged_in = False
        st.session_state.chat_history = []
        st.session_state.llm_history = []
        st.rerun()

    # Chat input
    prompt = st.chat_input("Say something or type 'generate image: <your prompt>'...")

    if prompt:
        # Save user input
        st.session_state.chat_history.append({"role": "user", "content": prompt})
        st.session_state.llm_history.append(HumanMessage(content=prompt))

        # ---- Image Generation ----
        if "generate image:" in prompt.lower():
            image_prompt = prompt.lower().replace("generate image:", "").strip()
            with st.spinner("🎨 Generating image..."):
                try:
                    response = image_model.generate_content(image_prompt)

                    text_response = ""
                    image_data = None

                    for part in response.candidates[0].content.parts:
                        if getattr(part, "text", None):
                            text_response += part.text
                        elif getattr(part, "inline_data", None):
                            img_bytes = base64.b64decode(part.inline_data.data)
                            image_data = Image.open(BytesIO(img_bytes))

                    st.session_state.chat_history.append({
                        "role": "assistant",
                        "content": text_response if text_response else "Here’s your generated image:",
                        "image_data": image_data
                    })

                    if text_response:
                        st.session_state.llm_history.append(AIMessage(content=text_response))

                except Exception as e:
                    error_msg = f"❌ Image generation failed: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.session_state.llm_history.append(AIMessage(content=error_msg))

        # ---- Text Chat ----
        else:
            with st.spinner("🤔 Thinking..."):
                try:
                    response = llm_text.invoke(st.session_state.llm_history)
                    st.session_state.chat_history.append(
                        {"role": "assistant", "content": response.content}
                    )
                    st.session_state.llm_history.append(AIMessage(content=response.content))
                except Exception as e:
                    error_msg = f"❌ Chat generation failed: {str(e)}"
                    st.session_state.chat_history.append({"role": "assistant", "content": error_msg})
                    st.session_state.llm_history.append(AIMessage(content=error_msg))

    # ---- Display Chat History ----
    for msg in st.session_state.chat_history:
        if msg["role"] == "user":
            st.chat_message("user").write(msg["content"])
        elif msg["role"] == "assistant":
            if "image_data" in msg and msg["image_data"] is not None:
                st.chat_message("assistant").image(msg["image_data"], caption="Generated Image")
            st.chat_message("assistant").write(msg["content"])

# =========================================================
# 🔹 App Flow
# =========================================================
if not st.session_state.logged_in:
    login_page()
else:
    chatbot_page()
