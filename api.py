# ISAQUE DE OLIVEIRA DOS SANTOS
from flask import Flask, request, jsonify
# ----------------------------------------------------------------------------------------
# ALTERAÇÃO CRÍTICA: Corrigido o erro de importação e alterado para a nova função web
# ----------------------------------------------------------------------------------------
from agent import process_web_message 
# (A função handle_message original foi renomeada no agent.py para process_web_message)

app = Flask(__name__)

@app.route('/')
def home():
    return "API do Chatbot da Clínica está online ✅"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()
        
        # ----------------------------------------------------------------------------------------
        # NOVO: Recebe o histórico de conversas do front-end (Wix)
        # ----------------------------------------------------------------------------------------
        chat_history = data.get('chat_history', []) # Espera uma lista de dicts

        if not user_message:
            return jsonify({"error": "Mensagem vazia"}), 400

        # Aqui chamamos a nova função que processa a mensagem com o histórico
        bot_reply = process_web_message(user_message, chat_history)

        return jsonify({"reply": bot_reply})
    except Exception as e:
        # Se for um erro que a IA não conseguiu tratar, retorna um erro 500
        print(f"Erro na rota /chat: {e}")
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    # Nota: No Render, o gunicorn vai rodar o 'gunicorn api:app', então este if __name__ é ignorado.
    app.run(host='0.0.0.0', port=5000)