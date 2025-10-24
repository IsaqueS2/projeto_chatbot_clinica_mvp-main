import requests
from config import TELEGRAM_BOT_TOKEN # Importa o token do nosso novo config

def send_telegram_message(chat_id, message_text):
    """
    Envia uma mensagem de texto simples para o usuário via API do Telegram.
    (Esta é a mesma função que estava no main.py)
    """
    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    headers = {"Content-Type": "application/json"}
    payload = {"chat_id": chat_id, "text": message_text}

    try:
        response = requests.post(url, headers=headers, json=payload)
        response.raise_for_status() 
        print(f"--- Mensagem enviada para o Chat ID {chat_id} ---")
        print(f"Conteúdo: {message_text}")
        print(f"Resposta do Telegram: {response.json()}")
        print("-----------------------------------------")
    except requests.exceptions.RequestException as e:
        print(f"================================================================")
        print(f"ERRO FATAL AO TENTAR ENVIAR MENSAGEM (Telegram):")
        print(f"Tipo exato do Erro: {type(e)}")
        print(f"Mensagem de Erro completa: {e}")
        print(f"================================================================")

def parse_webhook_data(request_data: dict) -> tuple[str | None, str | None]:
    """
    Analisa o JSON bruto do Telegram e extrai o ID do chat e o texto.
    Retorna (None, None) se não for uma mensagem de texto válida.
    """
    user_message = None
    user_chat_id = None

    if "message" in request_data and "text" in request_data["message"]:
        user_message = request_data["message"]["text"]
        user_chat_id = request_data["message"]["chat"]["id"]

    return user_chat_id, user_message