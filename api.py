# ISAQUE DE OLIVEIRA DOS SANTOS
from flask import Flask, request, jsonify
from agent import process_message  # Importa sua lógica do bot

app = Flask(__name__)

@app.route('/')
def home():
    return "API do Chatbot da Clínica está online ✅"

@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.get_json()
        user_message = data.get('message', '').strip()

        if not user_message:
            return jsonify({"error": "Mensagem vazia"}), 400

        # Aqui chamamos a função que gera a resposta do bot
        bot_reply = process_message(user_message)

        return jsonify({"reply": bot_reply})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
