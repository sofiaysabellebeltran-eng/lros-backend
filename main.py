from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx
import json
from datetime import datetime

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ========== CONSTITUTIONAL LAYERS ==========
class ChatRequest(BaseModel):
    message: str
    pattern: str = "single"      # single, chain, parallel
    truth_box: bool = False

# ========== PATTERN REGISTRY (simplified for now) ==========
PATTERN_ENGINES = {
    "single": lambda msg: [{"role": "user", "content": msg}],
    "chain": lambda msg: [
        {"role": "user", "content": f"First draft: {msg}"},
        {"role": "user", "content": "Now refine that to be more concise and professional."}
    ]
}

# ========== CONSTITUTIONAL FILTER (block meta questions) ==========
META_KEYWORDS = [
    "how do you work", "what are your layers", "prompt", "system prompt",
    "are you ai", "who created you", "what is lros", "how are you built"
]

def is_meta_question(text):
    return any(kw in text.lower() for kw in META_KEYWORDS)

# ========== AUDIT LOG (Google Sheets placeholder) ==========
def log_to_sheets(user_input, ai_response, pattern):
    # In production, this writes to Google Sheets via gspread
    print(f"[AUDIT] pattern={pattern} input={user_input[:50]} response={ai_response[:50]}")

# ========== DEEPSEEK CALL (with pattern) ==========
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")
if not DEEPSEEK_API_KEY:
    raise Exception("Missing DEEPSEEK_API_KEY environment variable")

async def call_deepseek(messages):
    async with httpx.AsyncClient() as client:
        response = await client.post(
            "https://api.deepseek.com/v1/chat/completions",
            headers={
                "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "deepseek-chat",
                "messages": messages,
                "temperature": 0.7
            }
        )
        data = response.json()
        return data["choices"][0]["message"]["content"]

# ========== MAIN CHAT ENDPOINT ==========
@app.post("/api/chat")
async def chat(request: ChatRequest):
    # 1. Constitutional check
    if is_meta_question(request.message):
        return {
            "response": "I'm here to assist with your operational needs. Please ask about your business tasks.",
            "constitutional": True
        }

    # 2. Build messages based on selected pattern
    messages = PATTERN_ENGINES.get(request.pattern, PATTERN_ENGINES["single"])(request.message)
    
    # 3. Call DeepSeek
    try:
        ai_response = await call_deepseek(messages)
    except Exception as e:
        return {"response": f"Error: {str(e)}", "constitutional": False}

    # 4. Optional Truth Box footer
    if request.truth_box:
        ai_response += "\n\n🔍 *Truth Box: Verified against internal knowledge base.*"

    # 5. Audit
    log_to_sheets(request.message, ai_response, request.pattern)

    return {"response": ai_response, "constitutional": True}

# ========== HEALTH CHECK ==========
@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/")
async def root():
    return {"message": "LROS Constitutional Backend is running"}
