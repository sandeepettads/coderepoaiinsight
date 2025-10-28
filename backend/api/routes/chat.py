from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from typing import List, Optional, Dict, Any
import logging
from openai import AsyncOpenAI
import os

logger = logging.getLogger(__name__)
router = APIRouter()

class Message(BaseModel):
    role: str
    content: str

class FileContext(BaseModel):
    name: str
    path: str
    content: str
    language: str

class ChatRequest(BaseModel):
    message: str
    file_context: Optional[FileContext] = None
    conversation_history: List[Dict[str, Any]] = []

class ChatResponse(BaseModel):
    response: str

@router.post("/chat", response_model=ChatResponse)
async def chat_with_code(request: ChatRequest):
    """
    Chat endpoint that provides context-aware assistance for code files.
    """
    try:
        client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        
        # Build system prompt with file context
        system_prompt = """You are an expert code assistant helping developers understand and work with their code files. You have access to the current file they're viewing and can provide detailed explanations, suggestions, and answer questions about the code.

Guidelines:
1. Be concise but thorough in your explanations
2. Focus on the specific file context provided
3. Explain code functionality, patterns, and potential improvements
4. Help with debugging, refactoring suggestions, and best practices
5. If asked about specific lines or functions, reference them directly
6. For COBOL code, explain mainframe concepts and business logic
7. For other languages, focus on modern development practices
8. Always be helpful and educational

Current file context will be provided with each message."""

        # Build user prompt with file context
        user_prompt = f"""Current file: {request.file_context.name} ({request.file_context.language})
Path: {request.file_context.path}

File content:
```{request.file_context.language.lower()}
{request.file_context.content[:8000]}  # Limit content to avoid token limits
```

User question: {request.message}

Please provide a helpful response about this code file."""

        # Build conversation messages
        messages = [{"role": "system", "content": system_prompt}]
        
        # Add recent conversation history for context
        for msg in request.conversation_history[-6:]:  # Last 6 messages for context
            if msg.get("role") in ["user", "assistant"]:
                messages.append({
                    "role": msg["role"],
                    "content": msg["content"]
                })
        
        # Add current user message
        messages.append({"role": "user", "content": user_prompt})

        # Call OpenAI
        response = await client.chat.completions.create(
            model="gpt-4-turbo-preview",
            messages=messages,
            temperature=0.1,
            max_tokens=1000
        )

        return ChatResponse(response=response.choices[0].message.content)

    except Exception as e:
        logger.error(f"Chat error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Chat failed: {str(e)}")
