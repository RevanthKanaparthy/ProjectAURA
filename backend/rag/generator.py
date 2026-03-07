import requests
import os
import json
import re
import time
from config import OLLAMA_URL, OLLAMA_MODEL, LLM_PROVIDER, OPENROUTER_API_KEY, OPENROUTER_MODEL, GEMINI_API_KEY, GEMINI_MODEL

# Optional imports for external providers
try:
    import openai
except ImportError:
    openai = None

try:
    from google import genai
except ImportError:
    genai = None

def generate_answer(context: str, question: str, model_name: str = None, provider: str = LLM_PROVIDER, history: list = None) -> str:
    """
    Generate an answer using the specified LLM provider and model.
    Defaults to the provider defined in config.py.
    """
    print(f"DEBUG: Generating answer with Provider: {provider}")
    
    # if not model_name and provider == "openrouter":
    #     model_name = OPENROUTER_MODEL
    if not model_name and provider == "gemini":
        model_name = GEMINI_MODEL

    history_block = ""
    if history:
        # Format last few turns to provide context
        recent_history = history[-3:]
        history_lines = [f"{msg.get('role', 'user').title()}: {msg.get('content', '')}" for msg in recent_history]
        history_block = "Previous Conversation:\n" + "\n".join(history_lines) + "\n\n"

    prompt = f"""
You are an intelligent assistant for analyzing college documents.
Use the provided 'Context' to answer the 'Question'.

{history_block}
Rules:
1. **Strict Relevance:** If the user asks for a specific category (e.g., "Books"), look for matches in 'Sheet_Category' or document content. Treat "Book Chapters" as valid for "Books". Do NOT list "Journals" or "Conferences" unless requested.
2. **Conversation:** If the input is a greeting, be polite. If the input is negative feedback (e.g., "wrong answer", "not correct"), apologize and ask the user to rephrase the query with more specific keywords.
3. **Topic Consistency:** Ensure the answer matches the user's intent. Do not select a document just because it shares a generic word (e.g., "Explain") with the question if the specific topic is unrelated.
4. **No Fabrication:** If the answer is NOT in the context and the input is not conversational, you MUST respond with the exact phrase: "Information not available in the provided documents."
5. **Clarity:** Format the output as a clean list if there are multiple items.

Context:
{context}

Question:
{question}

Answer:
"""

    # --- OLLAMA PROVIDER (DISABLED) ---
    # if provider == "ollama":
    #     payload = {
    #         "model": model_name,
    #         "prompt": prompt,
    #         "stream": False
    #     }
    #
    #     try:
    #         print(f"DEBUG: Sending request to Ollama ({model_name})...")
    #         resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
    #         resp.raise_for_status()  # raises HTTPError for 4xx/5xx
    #         data = resp.json()
    #
    #         # Ollama returns {"response": "..."} when stream=False
    #         return data.get("response", "No response from model.")
    #
    #     except requests.exceptions.Timeout:
    #         return "LLM service timed out. Please try again."
    #
    #     except requests.exceptions.ConnectionError:
    #         return "LLM service is not reachable. Is Ollama running?"
    #
    #     except Exception as e:
    #         return f"LLM service unavailable: {str(e)}"

    # --- OPENAI PROVIDER (DISABLED) ---
    # elif provider == "openai":
    #     if not openai:
    #         return "Error: 'openai' library not installed."
    #     api_key = os.getenv("OPENAI_API_KEY")
    #     if not api_key:
    #         return "Error: OPENAI_API_KEY not set."
    #     
    #     try:
    #         client = openai.OpenAI(api_key=api_key)
    #         response = client.chat.completions.create(
    #             model=model_name if model_name else "gpt-4o",
    #             messages=[{"role": "user", "content": prompt}]
    #         )
    #         return response.choices[0].message.content
    #     except Exception as e:
    #         return f"OpenAI Error: {str(e)}"

    # --- GEMINI PROVIDER (ACTIVE) ---
    if provider == "gemini" or True: # Force Gemini
        if not genai:
            return "Error: 'google-genai' library not installed."
        if not GEMINI_API_KEY:
            return "Error: GEMINI_API_KEY not set."

        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            # Retry logic for Rate Limits (429)
            for attempt in range(3):
                try:
                    response = client.models.generate_content(
                        model=model_name,
                        contents=prompt
                    )
                    return response.text
                except Exception as e:
                    if "429" in str(e) or "RESOURCE_EXHAUSTED" in str(e):
                        print(f"DEBUG: Rate limit hit. Retrying in 10s... (Attempt {attempt+1}/3)")
                        time.sleep(10)
                        continue
                    return f"Gemini Error: {str(e)}"
            return "Error: Gemini Rate Limit Exceeded. Please try again later."
        except Exception as e:
            return f"Gemini Error: {str(e)}"

    # --- OPENROUTER PROVIDER (COMMENTED OUT) ---
    # elif provider == "openrouter":
    #     if not openai:
    #         return "Error: 'openai' library not installed."
    #     if not OPENROUTER_API_KEY:
    #         return "Error: OPENROUTER_API_KEY not set."
    #     
    #     try:
    #         client = openai.OpenAI(
    #             base_url="https://openrouter.ai/api/v1",
    #             api_key=OPENROUTER_API_KEY,
    #         )
    #         response = client.chat.completions.create(
    #             model=model_name,
    #             messages=[{"role": "user", "content": prompt}],
    #             extra_headers={
    #                 "HTTP-Referer": "http://localhost:8000",
    #                 "X-Title": "College RAG Chatbot",
    #             }
    #         )
    #         return response.choices[0].message.content
    #     except Exception as e:
    #         print(f"OpenRouter API Error: {e}")
    #         if "429" in str(e):
    #             return "Error: The AI model is currently busy (Rate Limit). Please try again in a few seconds."
    #         return f"OpenRouter Error: {str(e)}"

    return f"Error: Unknown provider '{provider}'"

def extract_metadata_from_text(text: str, model_name: str = None) -> dict:
    """
    Uses the LLM to extract 'themes' and 'entities' from a text chunk.
    Returns a dictionary: {"themes": [...], "entities": [...]}
    """
    # Optimization: Skip extraction for very short texts (like greetings)
    if len(text.strip().split()) < 3:
        return {"themes": [], "entities": []}

    if not model_name:
        # Force default to Gemini model
        model_name = GEMINI_MODEL

    prompt = f"""
    Analyze the following text and extract key 'themes' (broad topics) and 'entities' (specific names, places, organizations).
    Return ONLY a valid JSON object with keys "themes" and "entities". Do not add explanations.
    
    Text:
    {text} 
    """
    
    # --- GEMINI EXTRACTION (ACTIVE) ---
    if True: # Force Gemini
        if not genai or not GEMINI_API_KEY:
            return {"themes": [], "entities": []}
        try:
            client = genai.Client(api_key=GEMINI_API_KEY)
            response = client.models.generate_content(
                model=model_name,
                contents=prompt
            )
            response_text = response.text
            
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                response_text = match.group(0)
            return json.loads(response_text)
        except Exception as e:
            print(f"Extraction Error (Gemini): {e}")
            return {"themes": [], "entities": []}

    # --- OPENROUTER EXTRACTION (COMMENTED OUT) ---
    # if True: # Force OpenRouter
    #     if not openai or not OPENROUTER_API_KEY:
    #         return {"themes": [], "entities": []}
    #     try:
    #         client = openai.OpenAI(
    #             base_url="https://openrouter.ai/api/v1",
    #             api_key=OPENROUTER_API_KEY,
    #         )
    #         response = client.chat.completions.create(
    #             model=model_name,
    #             messages=[{"role": "user", "content": prompt}]
    #         )
    #         response_text = response.choices[0].message.content
    #         match = re.search(r'\{.*\}', response_text, re.DOTALL)
    #         if match:
    #             response_text = match.group(0)
    #         return json.loads(response_text)
    #     except Exception as e:
    #         print(f"Extraction Error (OpenRouter): {e}")
    #         return {"themes": [], "entities": []}

    # payload = {
    #     "model": model_name,
    #     "prompt": prompt,
    #     "stream": False,
    #     "format": "json" # Force Ollama to output JSON
    # }

    # try:
    #     resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
    #     resp.raise_for_status()
    #     data = resp.json()
        
    #     response_text = data.get("response", "{}").strip()
        
    #     # Robust JSON extraction using regex (handles markdown blocks and extra text)
    #     match = re.search(r'\{.*\}', response_text, re.DOTALL)
    #     if match:
    #         response_text = match.group(0)
            
    #     return json.loads(response_text)
    # except Exception as e:
    #     print(f"Extraction Error: {e}")
    #     return {"themes": [], "entities": []}