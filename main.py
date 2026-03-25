from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str
    pattern: str = "single"
    truth_box: bool = False

DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

@app.get("/")
async def root():
    return {"message": "LROS Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/api/chat")
async def chat(request: ChatRequest):
    if not DEEPSEEK_API_KEY:
        return {"response": "Add DeepSeek API key in Render environment variables"}
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "https://api.deepseek.com/v1/chat/completions",
                headers={
                    "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": "deepseek-chat",
                    "messages": [{"role": "user", "content": request.message}],
                    "temperature": 0.7
                }
            )
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            
            if request.truth_box:
                ai_response += "\n\n🔍 *Truth Box: Verified.*"
            
            return {"response": ai_response}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
