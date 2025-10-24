from fastapi import FastAPI, Request, HTTPException, BackgroundTasks
import json

# Importa nossas novas funções refatoradas
from agent import handle_message
from telegram_utils import parse_webhook_data

# Inicializa o FastAPI
app = FastAPI()

# --- ROTA DE WEBHOOK (Agora muito mais limpa!) ---
@app.post("/webhook/telegram")
async def receive_message(request: Request, background_tasks: BackgroundTasks):
    """
    Recebe o webhook do Telegram.
    Responde 'ok' imediatamente e processa a lógica em segundo plano.
    """
    request_data = {}
    try:
        request_data = await request.json()
        print("--- Nova Mensagem Recebida (Payload Bruto) ---")
        print(json.dumps(request_data, indent=2, ensure_ascii=False))

        # Analisa o payload para encontrar dados úteis
        user_chat_id, user_message = parse_webhook_data(request_data)

        if user_chat_id and user_message:
            # Se for uma mensagem de texto válida...
            print(f"--- Delegando para o Agente em Segundo Plano (Chat ID: {user_chat_id}) ---")

            # --- A MÁGICA DA REFATORAÇÃO ---
            # 1. Adiciona a tarefa (lenta) para rodar em background
            background_tasks.add_task(handle_message, user_chat_id, user_message)

            # 2. Responde IMEDIATAMENTE para o Telegram (evita timeouts)
            return {"status": "ok, processando em segundo plano"}

        else:
            # Se for outro tipo de update (ex: 'usuário entrou no grupo'), ignoramos
            print("Webhook recebido, mas não é uma mensagem de texto do usuário. Ignorando.")
            return {"status": "ok, ignorado"}

    except json.JSONDecodeError:
        print("Erro: Não foi possível decodificar o JSON recebido.")
        raise HTTPException(status_code=400, detail="Payload inválido.")
    except Exception as e:
        print(f"Erro inesperado na Rota Principal: {e}")
        # Retorna ok mesmo se der erro, para o Telegram não ficar reenviando
        return {"status": "ok, erro interno no processamento"}

# ---
# ROTA 3: Health check (Idêntica)
# ---
@app.get("/")
async def root():
    return {"status": "Servidor do Chatbot (Refatorado) está rodando!"}