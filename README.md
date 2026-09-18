# 🧠 Cortex Chat 2.0

> Aplicação Fullstack conversacional moderna com IA, inspirada no design system da Lumina, com backend FastAPI, autenticação segura (JWT + bcrypt), persistência em banco de dados e integração com OpenRouter.

---

## ✨ Funcionalidades

- **🎨 Interface Moderna**: Baseada no design system de alto contraste, com glassmorphism, partículas flutuantes, feixes de luz animados e fontes estilizadas (*Geist* e *Instrument Serif*).
- **🔒 Autenticação Completa**:
  - Cadastro e Login com validação robusta.
  - Senhas criptografadas com `bcrypt`.
  - Tokens `JWT` com controle de sessão (`localStorage` / `sessionStorage`).
  - Proteção total de rotas (`/send_message`, `/chat/history`, `/auth/me`).
- **💬 Workspace de Chat Interativo**:
  - Renderização fluida de Markdown com destaque para blocos de código.
  - Botão de cópia rápida para respostas e códigos.
  - Histórico de mensagens persistido por usuário e por sessão.
  - Indicador de digitação e feedback de status da API em tempo real.
- **⚡ Arquitetura Unificada (Fullstack)**:
  - O próprio servidor FastAPI serve os arquivos estáticos do frontend (`backend/static/index.html`) e os endpoints de API na mesma porta.
  - Zero problemas de CORS em produção e facilidade máxima de deploy.
- **🗄️ Banco de Dados Flexível**:
  - **Local**: SQLite (`cortex.db`).
  - **Produção**: Compatibilidade nativa com PostgreSQL via SQLAlchemy (troca por variável `DATABASE_URL`).

---

## 📁 Estrutura do Repositório

```text
cortex-chat/
├── Dockerfile                  # Build Docker para deploy automatizado na nuvem
├── README.md                   # Documentação do projeto
├── backend/
│   ├── static/                 # Frontend SPA unificado
│   │   ├── index.html          # Aplicação web completa (HTML/CSS/JS)
│   │   └── lumina-video/       # Assets visuais do design system
│   ├── auth.py                 # Lógica de senhas (bcrypt), tokens (JWT) e dependências de rotas
│   ├── database.py             # Configuração SQLAlchemy (SQLite / PostgreSQL)
│   ├── models.py               # Modelos de dados (User, ChatMessage)
│   ├── main.py                 # Servidor FastAPI e rotas de autenticação, chat e estáticos
│   ├── requirements.txt        # Dependências Python para produção
│   ├── pyproject.toml          # Gerenciamento de projeto com uv / pip
│   └── Dockerfile              # Dockerfile interno do backend
```

---

## 🚀 Como Executar Localmente

### Pré-requisitos
- Python 3.11+
- Gerenciador [uv](https://docs.astral.sh/uv/) ou `pip` tradicional

### 1. Clonar o repositório
```bash
git clone https://github.com/sidneysimas/cortex-chat.git
cd cortex-chat/backend
```

### 2. Configurar variáveis de ambiente
Crie um arquivo `.env` dentro da pasta `backend`:
```env
OPENROUTER_API_KEY=sua-chave-openrouter-aqui
JWT_SECRET_KEY=cortex-super-secret-jwt-key-2026-production-ready
```

### 3. Instalar dependências e iniciar
Com **uv**:
```bash
uv sync
uv run python main.py
```

Ou com **pip**:
```bash
pip install -r requirements.txt
python main.py
```

Acesse a aplicação no navegador:
👉 **`http://localhost:8001/`**

---

## ☁️ Deploy em Produção (Railway)

Este repositório está pronto para deploy com 1 clique no [Railway.app](https://railway.app):

1. No Railway, clique em **+ New Project** -> **Deploy from GitHub repo**.
2. Selecione o repositório **`sidneysimas/cortex-chat`**.
3. No mesmo projeto, clique em **+ New** -> **Database** -> **Add PostgreSQL**.
4. No card da aplicação, acesse a aba **Variables** e configure:
   - `DATABASE_URL` = `${{Postgres.DATABASE_URL}}`
   - `OPENROUTER_API_KEY` = *Sua chave da OpenRouter*
   - `ENVIRONMENT` = `production`
5. Na aba **Settings** -> **Networking**, clique em **Generate Domain** para obter a URL pública com SSL/HTTPS.

---

## 📄 Licença
Distribuído sob a licença MIT. Desenvolvido por **Sidney Simas**.
