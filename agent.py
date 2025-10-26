import json
from typing import List, Dict, Any

from config import model, generation_config 

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

FULL_SYSTEM_PROMPT_TEMPLATE = """
Você é o agente de atendimento ao paciente da Clínica Zenith, um especialista em agendamentos de consultas e exames.
Seu objetivo é extrair o máximo de informação relevante do usuário e usar a ferramenta apropriada.
O nome do usuário para fins de agendamento é "Paciente Web" e o ID de chat é fixo como "WEB_CHAT_ID".

Siga a regra de OURO do Agente:
1. Sempre responda no formato JSON no final de CADA passo da conversa.
2. Seu JSON DEVE ter o campo "acao" e, se for para o usuário, "payload_acao".
3. Se a informação não for suficiente para usar a ferramenta, peça o dado FALTANTE.

Regras de Ferramentas:
- A ferramenta "tool_marcar_agendamento" ou "tool_marcar_exame" SÓ deve ser chamada quando você tiver o Nome, Especialidade/Exame e o ID do horário.
- A ferramenta "tool_cancelar_agendamento" ou "tool_cancelar_exame" SÓ deve ser chamada quando você tiver o ID do agendamento/exame.
- Use a ferramenta "tool_obter_info_clinica" para perguntas sobre endereço, convênios ou horário de funcionamento.

Regras de Resposta FINAL (Após usar uma ferramenta):
- Depois de chamar uma ferramenta e receber o 'tool_result', você deve fazer uma SEGUNDA chamada à IA (RAG) para gerar a resposta final com base no resultado.
- A resposta final deve ser sempre a ação: "RESPONDER_AO_USUARIO".

Estrutura de JSON de Resposta (Sua Saída):

1. Se você for chamar uma **ferramenta**:
   {{
     "acao": "CHAMAR_FERRAMENTA",
     "payload_acao": {{
       "tool_name": "nome_da_funcao_aqui",
       "tool_args": {{
         "argumento1": "valor1",
         "argumento2": "valor2"
       }}
     }}
   }}

2. Se você precisar de **mais informações** do usuário:
   {{
     "acao": "PEDIR_MAIS_INFO",
     "payload_acao": {{
       "pergunta_para_usuario": "Qual informação específica está faltando? (ex: Qual a especialidade desejada?)"
     }}
   }}

3. Se você for **responder ao usuário** (geralmente após a segunda chamada RAG):
   {{
     "acao": "RESPONDER_AO_USUARIO",
     "payload_acao": {{
       "resposta_para_usuario": "Sua resposta formatada e amigável aqui."
     }}
   }}

4. Para perguntas simples que **não precisam de ferramenta** (saudações, etc.):
   {{
     "acao": "RESPONDER_AO_USUARIO",
     "payload_acao": {{
       "resposta_para_usuario": "Olá! Em que posso ajudar com agendamentos ou informações da clínica?"
     }}
   }}
"""


def process_web_message(user_message: str, chat_history: List[Dict[str, Any]]) -> str:
    if not model:
        return "Desculpe, a IA não está configurada corretamente (GEMINI_API_KEY ausente)."

    full_system_prompt = FULL_SYSTEM_PROMPT_TEMPLATE
    
    # 1. CRÍTICO: Monta o conteúdo da conversa, injetando o System Prompt como o primeiro item.
    # Isso contorna o erro 'unexpected keyword argument system_instruction' em versões antigas.
    
    # Primeiro item: O System Prompt
    contents_for_api = [{
        "role": "user",
        "parts": [{"text": full_system_prompt}]
    }]
    
    # Adiciona o histórico de conversas anterior
    contents_for_api.extend(chat_history)
    
    # Adiciona a mensagem atual do usuário
    contents_for_api.append({
        "role": "user",
        "parts": [{"text": user_message}]
    })

    print(f"--- Processando Nova Mensagem Web: {user_message} (Histórico recebido: {len(chat_history)} mensagens) ---")

    try:
        # --- PRIMEIRA CHAMADA À IA (Decisão: Chamada de Ferramenta, Pedido de Info ou Resposta Simples) ---
        ai_response = model.generate_content(
            contents=contents_for_api,                  # Usa a lista com o System Prompt injetado
            # system_instruction=full_system_prompt,    # REMOVIDO PARA COMPATIBILIDADE COM VERSÕES ANTIGAS
            tools=list(AVAILABLE_TOOLS.values()),   
            config=generation_config                
        )

        ai_json_response_str = ai_response.text.strip()
        ai_data = json.loads(ai_json_response_str)
        action = ai_data.get("acao")
        payload = ai_data.get("payload_acao", {})

        # 2. Lógica da Ação
        if action == "RESPONDER_AO_USUARIO":
            return payload.get("resposta_para_usuario", "Desculpe, a IA não gerou uma resposta.")
        
        elif action == "PEDIR_MAIS_INFO":
            return payload.get("pergunta_para_usuario", "Qual informação específica você gostaria de saber?")
        
        elif action == "CHAMAR_FERRAMENTA":
            tool_name = payload.get("tool_name")
            tool_args = payload.get("tool_args", {})
            
            if tool_name in AVAILABLE_TOOLS:
                tool_function = AVAILABLE_TOOLS[tool_name]
                
                # Para agendamentos e cancelamentos, forçamos os IDs de usuário
                if tool_name in ["tool_marcar_agendamento", "tool_listar_meus_agendamentos", "tool_cancelar_agendamento",
                                 "tool_marcar_exame", "tool_listar_meus_exames_agendados", "tool_cancelar_exame"]:
                    tool_args['telegram_chat_id'] = "WEB_CHAT_ID"
                    if tool_name in ["tool_marcar_agendamento", "tool_marcar_exame"] and 'nome_paciente' not in tool_args:
                        tool_args['nome_paciente'] = "Paciente Web"

                # 3. Executa a ferramenta
                print(f"--- Chamando Ferramenta: {tool_name} com args: {tool_args} ---")
                tool_result = tool_function(**tool_args)
                print(f"--- Resultado da Ferramenta: {tool_result} ---")

                # 4. Monta o RAG (Round de Resposta) para a Segunda Chamada
                # Usamos contents_for_api (que tem o histórico e o system prompt)
                tool_response_content = [
                    {"role": "user", "parts": [{"text": "O usuário enviou uma nova mensagem."}]},
                    {"role": "model", "parts": [{"text": ai_json_response_str}]}, # Resultado da 1a IA
                    {"role": "tool", "parts": [{"functionResponse": {"name": tool_name, "response": tool_result}}]}
                ]
                
                # Conteúdo completo para a 2a chamada: contents_for_api + Chamada de Ferramenta + Resultado da Ferramenta
                final_rag_content = contents_for_api + tool_response_content

                # --- SEGUNDA CHAMADA À IA (RAG: Gerar a Resposta Final Amigável) ---
                final_ai_response = model.generate_content(
                    contents=final_rag_content,
                    # system_instruction=full_system_prompt,  # REMOVIDO PARA COMPATIBILIDADE COM VERSÕES ANTIGAS
                    tools=list(AVAILABLE_TOOLS.values()),   
                    config=generation_config                
                )

                final_ai_json_str = final_ai_response.text.strip()
                final_ai_data = json.loads(final_ai_json_str)
                action = final_ai_data.get("acao")
                
                # A IA deve agora sempre responder
                if action == "RESPONDER_AO_USUARIO":
                    final_response_text = final_ai_data.get("payload_acao", {}).get("resposta_para_usuario", 
                        "Desculpe, a IA não gerou uma resposta final, mesmo após os dados do DB.")
                    print(f"--- Ação: Responder com dados do DB ---")
                    return final_response_text
                else:
                    print("ERRO RAG: A IA não gerou uma resposta final, mesmo após os dados do DB.")
                    return "Desculpe, tive um problema ao processar sua solicitação após consultar os dados."
            else:
                print(f"ERRO: A IA solicitou uma ferramenta desconhecida: {tool_name}")
                return "Desculpe, a IA pediu uma ferramenta que eu não conheço."
        else:
            print(f"Ação desconhecida recebida da IA: {action}")
            return f"Desculpe, recebi uma ação desconhecida ({action}) e não sei o que fazer."

    except json.JSONDecodeError:
        print("ERRO FATAL: Gemini retornou um JSON inválido.")
        # Printa a string para debug
        # print(ai_json_response_str) 
        return "Desculpe, a resposta da IA veio em um formato inválido."

    except Exception as e:
        print(f"Erro inesperado na função process_web_message: {e}")
        return "Desculpe, ocorreu um erro interno grave. Tente novamente ou verifique os logs no Render."