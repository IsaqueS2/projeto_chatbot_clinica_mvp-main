import google.generativeai as genai
import os
from dotenv import load_dotenv

# Carregar a chave da API
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")

if not GEMINI_API_KEY:
    print("Erro: GEMINI_API_KEY não encontrada no arquivo .env")
else:
    try:
        genai.configure(api_key=GEMINI_API_KEY)

        print("--- Modelos disponíveis para sua Chave de API (que suportam 'generateContent') ---")

        # Itera sobre todos os modelos
        for m in genai.list_models():
            # Verifica se o modelo suporta o método que estamos usando
            if 'generateContent' in m.supported_generation_methods:
                print(m.name) # ex: models/gemini-pro

        print("-------------------------------------------------")
        print("Copie um dos nomes de modelo da lista acima (ex: models/gemini-pro) e cole no seu main.py")

    except Exception as e:
        print(f"Ocorreu um erro ao listar os modelos: {e}")
        print("Verifique se sua GEMINI_API_KEY está correta.")