import json
from typing import List, Dict, Any

# --- Importações do Projeto ---
# Importamos 'model' e 'generation_config' (configuração do Gemini)
from config import model, generation_config 

# Nota: send_telegram_message não é usado no agente web, mas é mantido 
# para as ferramentas do banco de dados que foram projetadas para o Telegram.
# Para este caso de uso, as ferramentas de DB são mantidas como estão.
# from telegram_utils import send_telegram_message 

from database_tools import (
    tool_obter_info_clinica, 
    tool_consultar_horarios_disponiveis, 
    tool_marcar_agendamento,
    tool_listar_meus_agendamentos,
    tool_cancelar_agendamento,
    tool_consultar_exames_disponiveis, 
    tool_consultar_horarios_exames,  
    tool_marcar_exame,
    tool_listar_meus_exames_agendados,
    tool_cancelar_exame
)

# --- Mapeamento de Ferramentas (Idêntico) ---
AVAILABLE_TOOLS = {
    "tool_obter_info_clinica": tool_obter_info_clinica,
    "tool_consultar_horarios_disponiveis": tool_consultar_horarios_disponiveis,
    "tool_marcar_agendamento": tool_marcar_agendamento,
    "tool_listar_meus_agendamentos": tool_listar_meus_agendamentos,
    "tool_cancelar_agendamento": tool_cancelar_agendamento,
    "tool_consultar_exames_disponiveis": tool_consultar_exames_disponiveis, 
    "tool_consultar_horarios_exames": tool_consultar_horarios_exames,  
    "tool_marcar_exame": tool_marcar_exame,
    "tool_listar_meus_exames_agendados": tool_listar_meus_exames_agendados,
    "tool_cancelar_exame": tool_cancelar_exame
}

# ---------------------------------------------------------------------------------------
# ALTERAÇÃO CRÍTICA: Função para ser usada pela API Web
# ---------------------------------------------------------------------------------------
def process_web_message(user_message: str, chat_history: List[Dict[str, str]] | None = None) -> str:
    """
    Processa a mensagem do usuário (via API web, como Wix) usando o Gemini.
    Retorna a resposta do bot como uma string.
    Não depende de chat_id nem da função de envio do Telegram.
    
    chat_history (opcional): Lista de mensagens passadas para manter o contexto.
    Exemplo de formato: [{"role": "user", "text": "Mensagem 1"}, {"role": "model", "text": "Resposta 1"}]
    """
    if not model:
        return "Desculpe, a chave GEMINI_API_KEY não está configurada e o serviço de IA não está disponível."
        
    print(f"--- Processando Nova Mensagem Web: {user_message} (Histórico recebido: {len(chat_history) if chat_history else 0} mensagens) ---")

    # 1. Configurar o histórico e a mensagem atual
    # O histórico do Gemini deve ser no formato: [{"role": "user", "parts": [{"text": "..."}]}]
    contents = []
    
    if chat_history:
        for message in chat_history:
            # Garante que 'user' e 'model' são os papéis corretos
            role = "user" if message.get("role") == "user" else "model" 
            contents.append({
                "role": role, 
                "parts": [{"text": message.get("text", "")}]
            })

    # Adiciona a nova mensagem do usuário
    contents.append({"role": "user", "parts": [{"text": user_message}]})

    # 2. PROMPT DE SISTEMA
    # (O seu prompt original deve ser inserido aqui para definir a persona e as regras)
    # Como não tenho seu prompt completo, usarei um placeholder, mas você deve 
    # MANTÊ-LO O MAIS FIEL POSSÍVEL AO ORIGINAL, apenas removendo referências ao Telegram.
    SYSTEM_INSTRUCTION = """
    Você é a "Assistente Virtual Clara", um agente de IA para uma clínica médica.
    Sua única função é gerenciar a interação com os pacientes.
    - Personalidade: Profissional, amigável, clara e objetiva.
    - Objetivo Principal: Marcar, cancelar ou consultar informações de consultas e exames.
    - Regras de Saída: SEMPRE retorne sua resposta final em uma string JSON válida, formatada de acordo com o Schema_AI_Response.
    - FERRAMENTAS: Você tem acesso às funções de banco de dados disponíveis.
    - Fluxo de Ferramentas: Se precisar de uma ferramenta, responda com action: 'CHAMAR_FERRAMENTA' e o payload JSON da ferramenta. Depois, use o resultado da ferramenta para responder ao usuário (action: 'RESPONDER_AO_USUARIO').
    """
    
    # Adicionar o prompt de sistema ao início
    system_instruction_part = {"role": "system", "parts": [{"text": SYSTEM_INSTRUCTION}]}
    # O Gemini SDK não usa 'role: system' em contents para tool calling, usa `config.system_instruction`. 
    # Como estamos mantendo a estrutura original, usaremos a config.
    
    # 3. CHAMADA DO GEMINI (Primeira Etapa)
    ai_response = model.generate_content(
        contents=contents,
        config={
            "system_instruction": SYSTEM_INSTRUCTION,
            "tools": list(AVAILABLE_TOOLS.values()), # Passa as funções como ferramentas
            "response_mime_type": "application/json"
        }
    )

    ai_json_response_str = ai_response.text.strip()
    
    try:
        # Analisa a resposta JSON da IA
        ai_data = json.loads(ai_json_response_str)
        action = ai_data.get("action", "RESPONDER_AO_USUARIO")

        # --- Lógica de Ferramentas ---
        if action == "RESPONDER_AO_USUARIO":
            final_response_text = ai_data.get("payload_acao", {}).get("resposta_para_usuario", 
                "Desculpe, a IA não conseguiu gerar uma resposta final.")
            print(f"--- Ação: Responder ao Usuário ---")
            return final_response_text # RETORNA A RESPOSTA
        
        elif action == "CHAMAR_FERRAMENTA":
            tool_name = ai_data.get("payload_acao", {}).get("nome_ferramenta")
            tool_args = ai_data.get("payload_acao", {}).get("parametros_ferramenta", {})

            if tool_name in AVAILABLE_TOOLS:
                tool_function = AVAILABLE_TOOLS[tool_name]
                print(f"--- Ação: Chamando Ferramenta {tool_name} com {tool_args} ---")
                
                # Executa a função do banco de dados (o 'user_chat_id' é obrigatório em algumas)
                # Como a API web não fornece um chat_id, usamos um valor fixo para a Web.
                # Nota: Isso pode causar problemas em 'tool_listar_meus_agendamentos' e 'tool_cancelar_agendamento'
                # pois elas dependem de um ID real para buscar agendamentos do usuário.
                # Se o Wix não enviar um ID de usuário, essas ferramentas falharão.
                # Para MVP, usaremos um placeholder:
                WEB_CHAT_ID = "WIX_WEB_API_USER"
                
                # Adapta a chamada da função para incluir o chat_id, se necessário
                if tool_name in ["tool_marcar_agendamento", "tool_listar_meus_agendamentos", "tool_cancelar_agendamento",
                                 "tool_marcar_exame", "tool_listar_meus_exames_agendados", "tool_cancelar_exame"]:
                    # As funções de agendamento/listagem/cancelamento precisam do ID do usuário.
                    # As ferramentas devem ser adaptadas para usar um ID de usuário REAL do Wix.
                    # Por simplicidade, assumimos que 'nome_paciente' é suficiente ou que o ID do Wix será adicionado.
                    # Para não quebrar o código, forçamos o chat_id na chamada.
                    if 'telegram_chat_id' not in tool_args:
                        tool_args['telegram_chat_id'] = WEB_CHAT_ID
                    
                    # Se 'nome_paciente' estiver faltando, o agendamento/cancelamento falhará, 
                    # mas o erro virá da ferramenta DB, que o Gemini processará.
                    
                
                try:
                    tool_result = tool_function(**tool_args)
                except TypeError as e:
                    tool_result = f"ERRO: Parâmetros faltando ou incorretos para {tool_name}. Detalhes: {e}"
                    print(f"ERRO DE PARÂMETROS: {e}")

                # 4. CHAMADA DO GEMINI (Segunda Etapa: Com o Resultado da Ferramenta)
                # Adiciona o resultado da ferramenta ao histórico para o Gemini
                contents.append({"role": "tool", "parts": [{"text": tool_result}]})
                
                final_ai_response = model.generate_content(
                    contents=contents,
                    config={
                        "system_instruction": SYSTEM_INSTRUCTION,
                        "tools": list(AVAILABLE_TOOLS.values()),
                        "response_mime_type": "application/json"
                    }
                )
                
                final_ai_data = json.loads(final_ai_response.text.strip())
                action = final_ai_data.get("action", "RESPONDER_AO_USUARIO")
                
                # A IA deve agora sempre responder
                if action == "RESPONDER_AO_USUARIO":
                    final_response_text = final_ai_data.get("payload_acao", {}).get("resposta_para_usuario", 
                        "Desculpe, a IA não gerou uma resposta final, mesmo após os dados do DB.")
                    print(f"--- Ação: Responder com dados do DB ---")
                    return final_response_text # RETORNA A RESPOSTA
                else:
                    print("ERRO RAG: A IA não gerou uma resposta final, mesmo após os dados do DB.")
                    return "Desculpe, tive um problema ao processar sua solicitação após consultar os dados." # RETORNA ERRO
            else:
                print(f"ERRO: A IA solicitou uma ferramenta desconhecida: {tool_name}")
                return "Desculpe, a IA pediu uma ferramenta que eu não conheço." # RETORNA ERRO
        else:
            print(f"Ação desconhecida recebida da IA: {action}")
            return f"Desculpe, recebi uma ação desconhecida ({action}) e não sei o que fazer." # RETORNA ERRO

    except json.JSONDecodeError:
        print("ERRO FATAL: Gemini retornou um JSON inválido.")
        print(ai_json_response_str) 
        return "Desculpe, a resposta da IA veio em um formato inválido." # RETORNA ERRO

    except Exception as e:
        print(f"Erro inesperado na função process_web_message: {e}")
        return "Desculpe, ocorreu um erro interno grave. Tente novamente mais tarde." # RETORNA ERRO