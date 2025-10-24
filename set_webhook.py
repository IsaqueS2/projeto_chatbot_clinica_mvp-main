import requests
import os
from dotenv import load_dotenv

# Carrega as variáveis de ambiente
load_dotenv()
TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN")

def set_webhook():
    if not TELEGRAM_BOT_TOKEN:
        print("Erro: TELEGRAM_BOT_TOKEN não encontrado no arquivo .env")
        return

    # Pede a sua URL pública (do ngrok)
    ngrok_url = input("Por favor, cole a sua URL 'Forwarding' do ngrok (ex: https://abcd-1234.ngrok-free.app): ")

    if not ngrok_url.startswith("https://"):
        print("Erro: A URL deve começar com https://")
        return

    # Monta a URL final do webhook (note o /webhook/telegram)
    webhook_url = f"{ngrok_url}/webhook/telegram"

    # A URL da API do Telegram para configurar o webhook
    api_url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/setWebhook?url={webhook_url}"

    try:
        print(f"Configurando webhook para: {webhook_url}")
        response = requests.get(api_url)
        response_data = response.json()

        if response_data.get("ok"):
            print("\nSUCESSO!")
            print(f"Descrição: {response_data.get('description')}")
        else:
            print("\nERRO AO CONFIGURAR WEBHOOK:")
            print(response_data)

    except Exception as e:
        print(f"Ocorreu um erro de conexão: {e}")

if __name__ == "__main__":
    set_webhook()