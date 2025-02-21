import streamlit as st
import os
from backend import store_document, get_documents, get_document_by_name
from extract_text import extract_text_from_pdf, extract_text_from_docx
from qa_model import ask_question_groq  # Change to ask_question_hf if using Hugging Face

st.title("📄 AI-Powered Document Chatbot")

# Ensure 'uploads' folder exists
UPLOADS_DIR = "uploads"
if not os.path.exists(UPLOADS_DIR):
    os.makedirs(UPLOADS_DIR)

# Track uploaded files to prevent duplicates
if "uploaded_files" not in st.session_state:
    st.session_state["uploaded_files"] = set()

# Upload file
uploaded_file = st.file_uploader("Upload a PDF or DOCX", type=["pdf", "docx"])

if uploaded_file:
    file_path = os.path.join(UPLOADS_DIR, uploaded_file.name)

    # Prevent duplicate storage in MongoDB
    if uploaded_file.name not in st.session_state["uploaded_files"]:
        with open(file_path, "wb") as f:
            f.write(uploaded_file.getbuffer())

        # Extract text
        if uploaded_file.name.endswith(".pdf"):
            content = extract_text_from_pdf(file_path)
        else:
            content = extract_text_from_docx(file_path)

        # Store in MongoDB (only if not already stored)
        store_document(uploaded_file.name, content)
        st.session_state["uploaded_files"].add(uploaded_file.name)  # Mark file as stored

        st.success(f"✅ Document '{uploaded_file.name}' uploaded and stored!")
    else:
        st.warning("⚠️ This document is already uploaded.")

# Fetch stored documents
documents = get_documents()
if documents:
    selected_doc = st.selectbox("📂 Select a document", [doc["file_name"] for doc in documents])
    question = st.text_input("💬 Ask a question")

    if st.button("🔍 Get Answer"):
        doc_content = get_document_by_name(selected_doc)["content"]
        answer = ask_question_groq(question, doc_content)  # Change to ask_question_hf if using Hugging Face
        st.write(f"**📝 Answer:** {answer}")
