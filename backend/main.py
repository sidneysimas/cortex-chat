import os
import sys
from datetime import datetime
from pathlib import Path
from typing import Optional, List

import requests
import uvicorn
from dotenv import load_dotenv
from fastapi import FastAPI, HTTPException, Depends, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel, EmailStr
from sqlalchemy.orm import Session

# Carrega o .env da pasta backend ou da raiz
env_path = Path(__file__).resolve().parent / ".env"
if env_path.exists():
    load_dotenv(dotenv_path=env_path)
load_dotenv()

sys.stdout.reconfigure(encoding="utf-8")

# Importações locais do banco e autenticação
from database import engine, Base, get_db
from models import User, ChatMessage
from auth import (
    hash_password,
    verify_password,
    create_access_token,
    get_current_user,
    get_optional_user,
)

# Cria as tabelas no banco de dados automaticamente caso não existam
Base.metadata.create_all(bind=engine)

app = FastAPI(title="Lumina API — OpenRouter & Auth")

# Habilitar CORS para permitir conexão com frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

STATIC_DIR = Path(__file__).resolve().parent / "static"
if STATIC_DIR.exists():
    app.mount("/static", StaticFiles(directory=str(STATIC_DIR)), name="static")
    lumina_dir = STATIC_DIR / "lumina-video"
    if lumina_dir.exists():
        app.mount("/lumina-video", StaticFiles(directory=str(lumina_dir)), name="lumina-video")

MODEL = "liquid/lfm-2.5-2.6b:free"


# ==================== SCHEMAS PYDANTIC ====================

class RegisterRequest(BaseModel):
    username: str
    email: str
    password: str


class LoginRequest(BaseModel):
    username_or_email: str
    password: str


class UserResponse(BaseModel):
    id: int
    username: str
    email: str
    created_at: datetime

    class Config:
        from_attributes = True


class AuthResponse(BaseModel):
    access_token: str
    token_type: str = "bearer"
    user: UserResponse


class MessageRequest(BaseModel):
    message: str
    session_id: Optional[str] = "default"


class ChatMessageResponse(BaseModel):
    id: int
    session_id: str
    role: str
    content: str
    created_at: datetime

    class Config:
        from_attributes = True


# ==================== ROTA DO FRONTEND & STATUS ====================

@app.get("/", response_class=FileResponse)
def render_frontend():
    """Renderiza a aplicação frontend Lumina Chat diretamente na raiz"""
    index_file = STATIC_DIR / "index.html"
    if not index_file.exists():
        raise HTTPException(status_code=404, detail="Frontend (static/index.html) não encontrado")
    return FileResponse(str(index_file))


@app.get("/api/health")
def api_health():
    """Endpoint de verificação de status da API e banco de dados"""
    return {
        "status": "ok",
        "message": "Lumina API ativa",
        "database": "SQLite (Pronto para migrar para PostgreSQL em produção)",
        "model": MODEL
    }


# ==================== ROTAS DE AUTENTICAÇÃO ====================

@app.post("/auth/register", response_model=AuthResponse, status_code=status.HTTP_201_CREATED)
def register(req: RegisterRequest, db: Session = Depends(get_db)):
    username = req.username.strip()
    email = req.email.strip().lower()

    if len(username) < 3:
        raise HTTPException(status_code=400, detail="O nome de usuário deve ter pelo menos 3 caracteres.")
    if "@" not in email or "." not in email:
        raise HTTPException(status_code=400, detail="Por favor, forneça um e-mail válido.")
    if len(req.password) < 6:
        raise HTTPException(status_code=400, detail="A senha deve conter no mínimo 6 caracteres.")

    # Verifica duplicidade
    if db.query(User).filter(User.username == username).first():
        raise HTTPException(status_code=400, detail="Nome de usuário já está em uso.")
    if db.query(User).filter(User.email == email).first():
        raise HTTPException(status_code=400, detail="E-mail já está cadastrado.")

    # Criação do usuário com senha criptografada via bcrypt
    new_user = User(
        username=username,
        email=email,
        hashed_password=hash_password(req.password),
    )
    db.add(new_user)
    db.commit()
    db.refresh(new_user)

    # Gera token JWT
    token = create_access_token({"sub": str(new_user.id), "username": new_user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": new_user,
    }


@app.post("/auth/login", response_model=AuthResponse)
def login(req: LoginRequest, db: Session = Depends(get_db)):
    identifier = req.username_or_email.strip()
    # Permite login tanto por username quanto por e-mail
    user = (
        db.query(User)
        .filter((User.username == identifier) | (User.email == identifier.lower()))
        .first()
    )

    if not user or not verify_password(req.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Credenciais incorretas. Verifique seu usuário/e-mail e senha.",
        )

    token = create_access_token({"sub": str(user.id), "username": user.username})
    return {
        "access_token": token,
        "token_type": "bearer",
        "user": user,
    }


@app.get("/auth/me", response_model=UserResponse)
def get_profile(current_user: User = Depends(get_current_user)):
    return current_user


# ==================== ROTAS DO CHAT & OPENROUTER ====================

@app.post("/send_message")
def send_message(
    req: MessageRequest,
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        raise HTTPException(status_code=500, detail="OPENROUTER_API_KEY não encontrada no .env")

    # Salva a mensagem do usuário no banco
    user_msg = ChatMessage(
        user_id=user.id,
        session_id=req.session_id or "default",
        role="user",
        content=req.message,
    )
    db.add(user_msg)
    db.commit()

    # Chamada para o modelo na OpenRouter
    response = requests.post(
        url="https://openrouter.ai/api/v1/chat/completions",
        headers={"Authorization": f"Bearer {api_key}"},
        json={
            "model": MODEL,
            "messages": [{"role": "user", "content": req.message}],
        },
    )

    data = response.json()
    if not response.ok:
        print(f"[Erro OpenRouter]: {data}")
        raise HTTPException(status_code=response.status_code, detail=data)

    bot_reply = data["choices"][0]["message"]["content"]
    print(f"\n--- Resposta ({MODEL}) ---\n{bot_reply}\n-------------------------")

    # Salva a resposta da IA no banco
    bot_msg = ChatMessage(
        user_id=user.id,
        session_id=req.session_id or "default",
        role="assistant",
        content=bot_reply,
    )
    db.add(bot_msg)
    db.commit()

    return {"response": bot_reply}


@app.get("/chat/history", response_model=List[ChatMessageResponse])
def get_chat_history(
    session_id: Optional[str] = None,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
):
    query = db.query(ChatMessage).filter(ChatMessage.user_id == current_user.id)
    if session_id:
        query = query.filter(ChatMessage.session_id == session_id)
    return query.order_by(ChatMessage.created_at.asc()).all()


if __name__ == "__main__":
    current_dir = str(Path(__file__).resolve().parent)
    if current_dir not in sys.path:
        sys.path.insert(0, current_dir)
    uvicorn.run("main:app", host="0.0.0.0", port=8001, reload=True, app_dir=current_dir)
