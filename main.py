import os
from fastapi import FastAPI, Request
from fastapi.responses import StreamingResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import requests
import yaml
import json

app = FastAPI()

# Set the working directory to the project root
os.chdir(os.path.dirname(os.path.abspath(__file__)) + "/..")

# Load configuration from settings.yaml
with open("backend/settings.yaml", "r") as f:
    config = yaml.safe_load(f)

openrouter_api_key = config["openrouter_api_key"]
model = config["model"]
site_url = config.get("site_url", "")
app_name = config.get("app_name", "")

# CORS settings to allow all origins
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Replace with your frontend URL in production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.post("/chat")
async def chat(request: Request):
    data = await request.json()
    user_input = data.get("message")

    headers = {
        "Authorization": f"Bearer {openrouter_api_key}",
        "HTTP-Referer": site_url,
        "X-Title": app_name,
    }

    payload = {
        "model": model,
        "messages": [{"role": "user", "content": user_input}]
    }

    try:
        response = requests.post(
            url="https://openrouter.ai/api/v1/chat/completions",
            headers=headers,
            data=json.dumps(payload),
            stream=True
        )

        response.raise_for_status()

        def generate():
            for chunk in response.iter_content(chunk_size=1024):
                yield chunk

        return StreamingResponse(generate(), media_type="text/plain")

    except requests.exceptions.RequestException as e:
        return JSONResponse(content={"error": str(e)}, status_code=500)

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
