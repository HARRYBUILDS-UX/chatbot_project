import requests
import tiktoken
import os
import time
import re
import concurrent.futures
from sentence_transformers import SentenceTransformer
import numpy as np
from dotenv import load_dotenv
# Load environment variables
load_dotenv()
GROQ_API_KEY = os.getenv("GROQ_API_KEY")

if not GROQ_API_KEY:
    raise ValueError("⚠️ Missing GROQ_API_KEY. Please set it in the .env file.")


embedding_model = SentenceTransformer("all-MiniLM-L6-v2")

def find_relevant_chunks(question, chunks, top_n=2):
    """Uses embeddings to find the most relevant chunks for answering a question."""
    question_embedding = embedding_model.encode([question])
    chunk_embeddings = embedding_model.encode(chunks)
    similarities = np.dot(chunk_embeddings, question_embedding.T).flatten()
    top_indices = similarities.argsort()[-top_n:][::-1]
    return [chunks[i] for i in top_indices]


def split_text_into_chunks(text, max_tokens=3000, overlap_ratio=0.05):
    """Splits text into context-preserving chunks while minimizing overlap for speed."""
    enc = tiktoken.get_encoding("cl100k_base")
    tokens = enc.encode(text)
    chunks = []
    step_size = int(max_tokens * (1 - overlap_ratio))  # Reduce overlap to speed up
    i = 0

    while i < len(tokens):
        chunk_tokens = tokens[i : i + max_tokens]
        chunk_text = enc.decode(chunk_tokens)
        chunks.append(chunk_text)
        i += step_size
    return chunks

def ask_groq(question, context, max_retries=5, initial_delay=2):
    """Sends a single question-context pair to Groq API with rate limiting and exponential backoff."""
    url = "https://api.groq.com/openai/v1/chat/completions"
    headers = {"Authorization": f"Bearer {GROQ_API_KEY}", "Content-Type": "application/json"}
    
    payload = {
        "model": "mixtral-8x7b-32768",
        "messages": [
            {"role": "system", "content": "You are an AI assistant answering questions based on provided context."},
            {"role": "user", "content": f"Context: {context}\nQuestion: {question}"}
        ]
    }
    
    delay = initial_delay
    for attempt in range(max_retries):
        try:
            response = requests.post(url, headers=headers, json=payload)
            if response.status_code == 429:
                print(f"Rate limit exceeded. Retrying in {delay} seconds...")
                time.sleep(delay)  # Wait before retrying
                delay *= 2  # Exponential backoff
                continue  
            
            response.raise_for_status()
            response_json = response.json()
            return response_json.get("choices", [{}])[0].get("message", {}).get("content", "").strip()

        except requests.exceptions.RequestException as e:
            return f"API request error: {e}"

    return "Failed after multiple retries due to rate limiting."

def ask_question_groq(question, full_text):
    """Handles both summarization and question answering with optimized API usage."""
    chunks = split_text_into_chunks(full_text, max_tokens=3000)

    # Detect if user asks for a summary
    if any(kw in question.lower() for kw in ["summarize", "summary", "give me a summary"]):
        return summarize_document(chunks)

    # Retrieve most relevant chunks
    relevant_chunks = find_relevant_chunks(question, chunks, top_n=2)

    answers = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_chunk = {executor.submit(ask_groq, question, chunk): chunk for chunk in relevant_chunks}
        for future in concurrent.futures.as_completed(future_to_chunk):
            answer = future.result()
            if answer:
                answers.append(answer)

    if len(answers) == 1:
        return answers[0]

    return summarize_final(question, answers)

def summarize_document(chunks):
    """Summarizes a document efficiently while avoiding too many API calls."""
    summary_parts = []
    with concurrent.futures.ThreadPoolExecutor(max_workers=2) as executor:
        future_to_chunk = {executor.submit(ask_groq, "Summarize this text:", chunk): chunk for chunk in chunks[:2]}  
        for future in concurrent.futures.as_completed(future_to_chunk):
            summary_parts.append(future.result())

    combined_summaries = '\n\n'.join(summary_parts)
    final_summary_prompt = f"""
    Here are multiple partial summaries:

    {combined_summaries}

    Please refine and generate a clear, well-structured summary of the document.
    """
    return ask_groq("Generate final summary:", final_summary_prompt)

def summarize_final(question, answers):
    """Merges and refines multiple extracted answers to create a final structured response."""
    combined_text = "\n\n".join(answers)
    summary_prompt = f"""
    Here are multiple answers related to the question:

    {combined_text}

    Please refine and generate a clear, well-structured response for: {question}
    """
    return ask_groq("Summarize and refine:", summary_prompt)