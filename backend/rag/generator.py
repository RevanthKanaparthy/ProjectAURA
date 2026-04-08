import requests
import os
import json
import re
import time
from config import OLLAMA_URL, OLLAMA_MODEL, LLM_PROVIDER, NEBIUS_API_KEY, LLM_CHAT_MODEL, GEMINI_API_KEY, GEMINI_MODEL, OPENROUTER_API_KEY, OPENROUTER_MODEL

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
    
    if not model_name and provider == "gemini":
        model_name = GEMINI_MODEL

    history_block = ""
    if history:
        # Format last few turns to provide context
        recent_history = history[-3:]
        history_lines = [f"{msg.get('role', 'user').title()}: {msg.get('content', '')}" for msg in recent_history]
        history_block = "Previous Conversation:\n" + "\n".join(history_lines) + "\n\n"

    prompt = f"""
You are an intelligent data assistant analyzing records from an Excel-based academic database.

The database contains structured information about:
• Faculty
• Departments
• Publications
• Journals
• Conferences
• Books
• Patents
• Research work

----------------------------
DATABASE CONTEXT
----------------------------
{context}

{history_block}
----------------------------
USER QUESTION
----------------------------
{question}

----------------------------
INSTRUCTIONS
----------------------------
1. Answer ONLY using the information present in the database context above, unless the user is just saying a simple greeting.
2. Do NOT invent, infer, or hallucinate information that is not explicitly present.
3. If the question asks for counts or totals: Count all relevant records in the context.
4. If the question asks for lists: List the relevant items clearly.
5. If the question includes filters (year, faculty, department, publication type), ensure the answer only includes matching records.
6. If the user asks a specific question and the answer cannot be found in the provided context, respond with: "I do not have that information in the available database records."
7. If the user input is a standard greeting (like "hi", "hello", "good morning"), respond politely and ask how you can help them search the academic database.
8. Present the answer in a clear structured format.

----------------------------
Answer:
----------------------------
"""

    if provider == "ollama":
        if not model_name:
            model_name = OLLAMA_MODEL
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False
        }
        try:
            print(f"DEBUG: Sending request to Ollama ({model_name})...")
            resp = requests.post(OLLAMA_URL, json=payload, timeout=600)
            
            # Gracefully handle missing models
            if resp.status_code == 404:
                try:
                    err_msg = resp.json().get("error", "")
                    if "not found" in err_msg.lower():
                        return f"Ollama Error: Model '{model_name}' is not installed. Please open your terminal and run 'ollama pull {model_name}'."
                except:
                    pass
                    
            resp.raise_for_status()
            data = resp.json()
            return data.get("response", "No response from model.")
        except Exception as e:
            return f"Ollama Error: {str(e)}"

    elif provider == "nebius":
        if not openai:
            return "Error: 'openai' library not installed."
        if not NEBIUS_API_KEY:
            return "Error: NEBIUS_API_KEY not set."
        try:
            client = openai.OpenAI(
                api_key=NEBIUS_API_KEY,
                base_url="https://api.nebius.ai/v1"
            )
            response = client.chat.completions.create(
                model=model_name if model_name else LLM_CHAT_MODEL,
                messages=[
                    {"role": "system", "content": "Answer only using the provided context."},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.0,
                max_tokens=1024
            )
            return response.choices[0].message.content
        except Exception as e:
            return f"Nebius Error: {str(e)}"

    elif provider == "openrouter":
        if not openai:
            return "Error: 'openai' library not installed."
        if not OPENROUTER_API_KEY:
            return "Error: OPENROUTER_API_KEY not set in your .env file."
        try:
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
            )
            response = client.chat.completions.create(
                model=model_name if model_name else OPENROUTER_MODEL,
                messages=[
                    {"role": "system", "content": "Answer only using the provided context."},
                    {"role": "user", "content": prompt}
                ],
                extra_headers={
                    "HTTP-Referer": "http://localhost:8000",
                    "X-Title": "College RAG Chatbot",
                }
            )
            return response.choices[0].message.content
        except Exception as e:
            if "429" in str(e):
                return "Error: The AI model is currently busy (Rate Limit). Please try again in a few seconds."
            return f"OpenRouter Error: {str(e)}"

    elif provider == "gemini":
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

    return f"Error: Unknown provider '{provider}'"

def extract_metadata_from_text(text: str, model_name: str = None, provider: str = LLM_PROVIDER) -> dict:
    """
    Uses the LLM to extract 'themes' and 'entities' from a text chunk.
    Returns a dictionary: {"themes": [...], "entities": [...]}
    """
    # Optimization: Skip extraction for very short texts (like greetings)
    if len(text.strip().split()) < 3:
        return {"themes": [], "entities": []}

    prompt = f"""
    Analyze the following text and extract key 'themes' (broad topics) and 'entities' (specific names, places, organizations).
    Return ONLY a valid JSON object with keys "themes" and "entities". Do not add explanations.
    
    Text:
    {text} 
    """
    
    if provider == "ollama":
        if not model_name:
            model_name = OLLAMA_MODEL
        payload = {
            "model": model_name,
            "prompt": prompt,
            "stream": False,
            "format": "json"
        }
        try:
            resp = requests.post(OLLAMA_URL, json=payload, timeout=120)
            
            # Gracefully handle missing models
            if resp.status_code == 404:
                try:
                    err_msg = resp.json().get("error", "")
                    if "not found" in err_msg.lower():
                        print(f"Extraction Error: Model '{model_name}' not found. Run 'ollama pull {model_name}'.")
                        return {"themes": [], "entities": []}
                except:
                    pass
                    
            resp.raise_for_status()
            data = resp.json()
            response_text = data.get("response", "{}").strip()
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                response_text = match.group(0)
            return json.loads(response_text)
        except Exception as e:
            print(f"Extraction Error (Ollama): {e}")
            return {"themes": [], "entities": []}

    elif provider == "gemini":
        if not model_name:
            model_name = GEMINI_MODEL
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

    elif provider == "openrouter":
        if not openai or not OPENROUTER_API_KEY:
            return {"themes": [], "entities": []}
        try:
            client = openai.OpenAI(
                base_url="https://openrouter.ai/api/v1",
                api_key=OPENROUTER_API_KEY,
            )
            response = client.chat.completions.create(
                model=model_name if model_name else OPENROUTER_MODEL,
                messages=[{"role": "user", "content": prompt}]
            )
            response_text = response.choices[0].message.content
            match = re.search(r'\{.*\}', response_text, re.DOTALL)
            if match:
                response_text = match.group(0)
            return json.loads(response_text)
        except Exception as e:
            print(f"Extraction Error (OpenRouter): {e}")
            return {"themes": [], "entities": []}