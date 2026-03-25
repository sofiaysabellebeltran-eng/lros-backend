from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import os
import httpx

app = FastAPI()

# Allow all origins for testing
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class ChatRequest(BaseModel):
    message: str

# Get API key from environment variable
DEEPSEEK_API_KEY = os.getenv("DEEPSEEK_API_KEY", "")

@app.get("/")
async def root():
    return {"message": "LROS Backend is running!"}

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.post("/chat")
async def chat(request: ChatRequest):
    # If no API key, return simple response
    if not DEEPSEEK_API_KEY:
        return {"response": f"You said: {request.message} (Add DeepSeek API key to enable AI)"}
    
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
                    "messages": [
                        {"role": "user", "content": request.message}
                    ],
                    "temperature": 0.7
                }
            )
            data = response.json()
            ai_response = data["choices"][0]["message"]["content"]
            return {"response": ai_response}
    except Exception as e:
        return {"response": f"Error: {str(e)}"}
