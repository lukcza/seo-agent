# pyrefly: ignore [missing-import]
from fastapi import FastAPI
# pyrefly: ignore [missing-import]
from fastapi.middleware.cors import CORSMiddleware
# pyrefly: ignore [missing-import]
from fastapi.staticfiles import StaticFiles
from app.api.v1.api import api_router
import os

app = FastAPI(
    title="Interactive SEO Agent & Website Auditor API",
    description="Zaawansowany interaktywny system audytowania SEO i doprecyzowywania promptów oparty o Gemini 2.5 Flash",
    version="2.0.0"
)

# CORS Configurations
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include v1 API endpoints
app.include_router(api_router, prefix="/api/v1")

# Mount static web dashboard
static_path = os.path.join(os.path.dirname(__file__), "static")
if not os.path.exists(static_path):
    os.makedirs(static_path)

# Mount the static files so it serves index.html at root "/"
app.mount("/", StaticFiles(directory=static_path, html=True), name="static")
