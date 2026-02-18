import requests, time
import streamlit as st

BASE_URL = "http://localhost:8005"
API_FILES = f"{BASE_URL}/files"
API_CHAT  = f"{BASE_URL}/chat"
API_UPLOAD = f"{BASE_URL}/upload"
API_DELETE = f"{BASE_URL}/delete_file"


st.set_page_config(page_title="RAG", layout="wide")

st.markdown("""
<style>
.block-container {
    max-width: 100% !important;
    padding-bottom: 140px;
}

div[data-testid="stChatInput"] {
    position: fixed !important;
    bottom: 0px;
    left: 0;
    width: 100vw;          
    background: #0E1117;
    padding: 14px 0px;
    z-index: 9999;
}

div[data-testid="stChatInput"] > div {
    max-width: 1100px;
    margin: 0 auto;
    padding: 15px 20px;
    border-radius: 50px;
}

div[data-testid="stChatInput"] textarea {
    width: 100vw !important;
    border-radius: 12px !important;
    font-size: 16px;
}

div[data-testid="stChatInput"] button {
    margin-left: 10px;
    width: 50px;
    height: 50px;
    border-radius: 100%;
}
</style>
""", unsafe_allow_html=True)

st.title("📚 Retrieval Augmented Generator")


def fetch_files():
    try:
        res = requests.get(API_FILES)
        if res.status_code == 200:
            return res.json().get("files", [])
    except Exception:
        return []
    return []


def refresh_files():
    st.session_state.file_options = fetch_files()


if "file_options" not in st.session_state:
    refresh_files()

if "selected_files" not in st.session_state:
    st.session_state.selected_files = []

if "messages" not in st.session_state:
    st.session_state.messages = []

# uploader reset flag
if "clear_uploader" not in st.session_state:
    st.session_state.clear_uploader = False

# selected files cleanup flag
if "clean_selected_files" not in st.session_state:
    st.session_state.clean_selected_files = False


tab_chat, tab_upload = st.tabs(["Chat", "Upload PDFs"])


with tab_chat:

    st.subheader("💬 Chat with your documents")

    file_options = st.session_state.file_options

    if st.session_state.clean_selected_files:
        st.session_state.selected_files = [
            f for f in st.session_state.selected_files
            if f in file_options
        ]
        st.session_state.clean_selected_files = False

    selected_files = st.multiselect(
        "📎 Select files to use as context",
        file_options,
        key="selected_files"
    )

    st.divider()

    # Chat history
    for msg in st.session_state.messages:
        with st.chat_message(msg["role"]):
            st.write(msg["content"])

    user_input = st.chat_input(
        "Ask a question about the selected files...",
        disabled=len(st.session_state.selected_files) == 0
    )

    if not st.session_state.selected_files:
        st.warning("Select at least one file to enable chat")

    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        with st.chat_message("user"):
            st.write(user_input)

        payload = {
            "question": user_input,
            "files": st.session_state.selected_files
        }

        with st.chat_message("assistant"):
            placeholder = st.empty()

            placeholder.markdown("🔍 **Retrieving relevant chunks...**")
            time.sleep(1)

            placeholder.markdown("🧠 **Augmenting context with embeddings...**")
            time.sleep(1)

            placeholder.markdown("✍️ **Generating response...**")

            try:
                response = requests.post(API_CHAT, json=payload)

                if response.status_code == 200:
                    answer = response.json().get("message")
                else:
                    answer = response.json().get("detail", "Error processing request")

            except Exception as e:
                answer = f"API error: {e}"

            placeholder.markdown(answer)

        st.session_state.messages.append({"role": "assistant", "content": answer})
        st.rerun()


with tab_upload:

    st.subheader("📤 Upload PDF files")

    if st.session_state.clear_uploader:
        st.session_state.pop("uploader", None)
        st.session_state.clear_uploader = False

    uploaded_files = st.file_uploader(
        "Drag and drop or browse PDFs",
        type=["pdf"],
        accept_multiple_files=True,
        key="uploader"
    )

    if st.button("Upload Files"):
        if not uploaded_files:
            st.warning("Please select at least one file.")
        else:
            files = [
                ("files", (f.name, f.getvalue(), f.type))
                for f in uploaded_files
            ]

            try:
                response = requests.post(API_UPLOAD, files=files)

                if response.status_code == 200:
                    st.success(response.json().get("message", "Uploaded!"))

                    refresh_files()

                    st.session_state.clear_uploader = True

                    st.rerun()
                else:
                    st.error(response.json().get("detail", "Upload failed"))

            except Exception as e:
                st.error(f"API error: {e}")


    st.markdown("### 📁 Available Files")

    file_options = st.session_state.file_options

    if file_options:
        for f in file_options:
            col1, col2 = st.columns([8, 1])

            with col1:
                st.write(f"📄 {f}")

            with col2:
                if st.button("🗑️", key=f"delete_{f}"):
                    try:
                        res = requests.delete(API_DELETE, params={"filename": f})

                        if res.status_code == 200:
                            st.success(res.json().get('message', 'Removed!'))

                            refresh_files()

                            st.session_state.clean_selected_files = True

                            st.rerun()
                        else:
                            st.error("Delete failed")

                    except Exception as e:
                        st.error(f"Error: {e}")
    else:
        st.info("No files uploaded yet")
