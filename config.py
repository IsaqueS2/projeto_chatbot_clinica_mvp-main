import os
import google.generativeai as genai
from dotenv import load_dotenv

# Carrega as variáveis de ambiente do .env
load_dotenv()

# --- Carrega e Limpa os Tokens ---
_gemini_key_bruto = os.getenv("GEMINI_API_KEY")
_telegram_token_bruto = os.getenv("TELEGRAM_BOT_TOKEN")

GEMINI_API_KEY = _gemini_key_bruto.strip() if _gemini_key_bruto else None
TELEGRAM_BOT_TOKEN = _telegram_token_bruto.strip() if _telegram_token_bruto else None

# --- Inicializa o Modelo da IA (só uma vez) ---
model = None
if GEMINI_API_KEY:
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        model = genai.GenerativeModel('models/gemini-flash-latest')
        print("API do Gemini configurada com sucesso (usando gemini-flash-latest).")
    except Exception as e:
        print(f"ERRO: Falha ao configurar a API do Gemini. Erro: {e}")
else:
    print("ERRO: GEMINI_API_KEY não encontrada no .env. A IA não vai funcionar.")

if not TELEGRAM_BOT_TOKEN:
    print("ERRO: TELEGRAM_BOT_TOKEN não encontrado no .env. O bot não vai funcionar.")

# Configuração de geração do Gemini
generation_config = { "response_mime_type": "application/json" }

print("--------------------------------------------------")