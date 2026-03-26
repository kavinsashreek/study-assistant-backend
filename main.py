from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
import uvicorn

from routers import upload, chat, summary, flashcards, study_guide, quiz

app = FastAPI(
    title="AI Study Assistant API",
    description="A RAG-powered study assistant using Claude AI",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(upload.router)
app.include_router(chat.router)
app.include_router(summary.router)
app.include_router(flashcards.router)
app.include_router(study_guide.router)
app.include_router(quiz.router)


@app.get("/")
async def root():
    return {
        "status": "🟢 Server is running!",
        "message": "AI Study Assistant API is ready",
        "endpoints": {
            "upload": "POST /api/upload",
            "chat": "POST /api/chat",
            "summarize": "POST /api/summarize",
            "flashcards": "POST /api/flashcards",
            "study_guide": "POST /api/study-guide",
            "quiz": "POST /api/quiz",
            "docs": "GET /docs"
        }
    }


@app.get("/health")
async def health_check():
    return {"status": "healthy"}


if __name__ == "__main__":
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True
    )