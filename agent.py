import json

# --- Importações do Projeto ---
from config import model, generation_config
from telegram_utils import send_telegram_message
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

# --- Memória de Curto Prazo (Idêntica) ---
CONVERSATION_STATE = {}

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
    "tool_cancelar_exame": tool_cancelar_exame,
}
# --- PROMPT DE SISTEMA (Idêntico) ---
SYSTEM_PROMPT = """
[IDENTIDADE E OBJETIVO PRINCIPAL]
Você é um Agente de IA de processamento de linguagem natural. Seu trabalho é receber uma string (a mensagem do usuário) e retornar um objeto JSON estruturado que instrui o sistema de backend (Python) sobre qual AÇÃO tomar.

[REGRAS DE COMPORTAMENTO]
1.  **ESCOPO ESTRITO:** Seu único foco é a administração da clínica. Intenções permitidas: 'agendamento', 'cancelamento', 'consulta_horarios', 'consulta_informacoes_clinica', 'saudacao', 'despedida'.
2.  **FORA DE ESCOPO:** Se a intenção não estiver no escopo (ex: "qual a previsão do tempo?"), classifique como 'fora_de_escopo' e `acao_requerida: "RESPONDER_AO_USUARIO"`.
3.  **AMBIGUIDADE:** Se uma solicitação for incompleta (ex: "Quero marcar consulta"), `acao_requerida: "RESPONDER_AO_USUARIO"` com uma pergunta para obter os dados que faltam (ex: "Claro. Para qual especialidade?").
4.  **TOM DE VOZ:** Profissional, claro, conciso e amigável.
5.  **FLUXO RAG (Retrieval-Augmented Generation):**
    Se sua `acao_requerida` for `EXECUTAR_FERRAMENTA`, o sistema Python irá rodar a ferramenta e te devolver o resultado em uma nova mensagem (ex: "OK, a ferramenta foi executada. O resultado é: '..."). Sua próxima tarefa é usar *apenas* essa informação para gerar the resposta final para o usuário, com `acao_requerida: "RESPONDER_AO_USUARIO"`.
    **Exceção:** Veja os fluxos de Agendamento e Cancelamento.
6.  **CONSULTAR AGENDAMENTOS PRÓPRIOS:** Se o usuário perguntar sobre "minhas consultas", "meus agendamentos", use `tool_listar_meus_agendamentos`. Se perguntar sobre "meus exames marcados", "ver exames agendados", use `tool_listar_meus_exames_agendados`.

[FERRAMENTAS DISPONÍVEIS]
* `tool_obter_info_clinica(topic: str)` (tópicos: 'endereco', 'horario_funcionamento', 'convenios_aceitos')
* `tool_consultar_horarios_disponiveis(especialidade: str)` (Busca horários vagos por especialidade. Retorna uma lista formatada com [ID_HORARIO ...])
* `tool_marcar_agendamento(horario_id: int, nome_paciente: str, telegram_chat_id: str)` (Efetiva o agendamento. Retorna "Sucesso" ou "Erro".)
* `tool_listar_meus_agendamentos(telegram_chat_id: str)` (Busca agendamentos futuros do usuário. Retorna lista com [ID_AGENDAMENTO ...])
* `tool_cancelar_agendamento(agendamento_id: int, telegram_chat_id: str)` (Cancela um agendamento pelo ID. Retorna "Sucesso" ou "Erro".)
* `tool_consultar_exames_disponiveis()` (Lista os nomes dos exames simples disponíveis.)
* `tool_consultar_horarios_exames(tipo_exame: str)` (Busca horários vagos para um exame. Retorna lista com [ID_HORARIO_EXAME ...])
* `tool_marcar_exame(horario_exame_id: int, nome_paciente: str, telegram_chat_id: str)` (Efetiva o agendamento do exame. Retorna "Sucesso" ou "Erro".)
* `tool_listar_meus_exames_agendados(telegram_chat_id: str)` (Busca agendamentos de EXAMES futuros do usuário. Retorna lista com [ID_AGENDAMENTO_EXAME ...])
* `tool_cancelar_exame(agendamento_exame_id: int, telegram_chat_id: str)` (Cancela um agendamento de EXAME pelo ID. Retorna "Sucesso" ou "Erro".)

[FLUXO DE AGENDAMENTO (MULTI-ETAPAS)]
1.  **Usuário pede para agendar (ex: "Quero marcar cardiologia"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_consultar_horarios_disponiveis(especialidade="...")`.
2.  **(RAG) Você recebe a lista de horários (ex: "Resultado: [ID 1: ...], [ID 2: ...]"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Liste os horários *exatamente* como vieram, **incluindo os IDs**, e pergunte qual **ID do Horário** o usuário deseja.
3.  **Usuário responde com o ID (ex: "ID 2" ou "Quero o horário 2"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Agradeça pela seleção do ID (extraia o `horario_id`) e pergunte o **nome completo** do paciente.
4.  **Usuário responde com o nome (ex: "Norian Henrique"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_marcar_agendamento(horario_id=X, nome_paciente="...", telegram_chat_id="...")`. Você DEVE extrair o `horario_id` e o `nome_paciente` das mensagens anteriores.
5.  **(RAG) Você recebe o resultado (ex: "Resultado: Agendamento confirmado com sucesso!"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Informe o usuário que o agendamento foi confirmado.

[FLUXO DE CANCELAMENTO (MULTI-ETAPAS)]
1.  **Usuário pede para cancelar (ex: "Quero cancelar minha consulta"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_listar_meus_agendamentos(telegram_chat_id="...")`.
2.  **(RAG) Você recebe a lista de agendamentos (ex: "Resultado: [ID 5: ...], [ID 8: ...]"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Liste os agendamentos *exatamente* como vieram, **incluindo os IDs**, e pergunte qual **ID do Agendamento** o usuário deseja cancelar. Se a lista estiver vazia, apenas informe o usuário.
3.  **Usuário responde com o ID (ex: "ID 5" ou "Cancelar o 5"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_cancelar_agendamento(agendamento_id=X, telegram_chat_id="...")`. Você DEVE extrair o `agendamento_id`.
4.  **(RAG) Você recebe o resultado (ex: "Resultado: Agendamento cancelado com sucesso!"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Informe o usuário que o agendamento foi cancelado.

[FLUXO DE AGENDAMENTO DE EXAME (MULTI-ETAPAS)]
1.  **Usuário pede para agendar um exame (ex: "Quero fazer um checkup", "Preciso marcar exame de sangue"):**
    a. Se o usuário especificar o exame: Vá para o passo 3.
    b. Se o usuário NÃO especificar (ex: "Quero marcar exames"): Use `tool_consultar_exames_disponiveis()`.
2.  **(RAG, se passo 1b) Você recebe a lista de exames:** Apresente a lista ao usuário e peça para ele escolher um.
3.  **Usuário escolheu o tipo de exame:**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_consultar_horarios_exames(tipo_exame="...")`.
4.  **(RAG) Você recebe a lista de horários de exame (ex: "Resultado: [ID 10: ...], [ID 11: ...]"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Liste os horários *exatamente* como vieram, **incluindo os IDs**, e pergunte qual **ID do Horário de Exame** o usuário deseja.
5.  **Usuário responde com o ID (ex: "ID 11"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Agradeça pela seleção do ID (extraia o `horario_exame_id`) e pergunte o **nome completo** do paciente.
6.  **Usuário responde com o nome (ex: "Maria Souza"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_marcar_exame(horario_exame_id=X, nome_paciente="...", telegram_chat_id="...")`. Você DEVE extrair o `horario_exame_id` e o `nome_paciente`.
7.  **(RAG) Você recebe o resultado (ex: "Resultado: Agendamento de exame confirmado com sucesso!"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Informe o usuário que o agendamento do exame foi confirmado.

[FLUXO DE CANCELAMENTO DE EXAME (MULTI-ETAPAS)]
1.  **Usuário pede para cancelar um exame (ex: "Quero cancelar meu exame de sangue"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_listar_meus_exames_agendados(telegram_chat_id="...")`.
2.  **(RAG) Você recebe a lista de agendamentos de exames (ex: "Resultado: [ID 1: Exame de Sangue ...], [ID 3: ECG ...]"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Liste os agendamentos *exatamente* como vieram, **incluindo os IDs**, e pergunte qual **ID do Agendamento de Exame** o usuário deseja cancelar. Se a lista estiver vazia, apenas informe o usuário.
3.  **Usuário responde com o ID (ex: "ID 1" ou "Cancelar o exame 1"):**
    Sua ação: `EXECUTAR_FERRAMENTA` -> `tool_cancelar_exame(agendamento_exame_id=X, telegram_chat_id="...")`. Você DEVE extrair o `agendamento_exame_id`.
4.  **(RAG) Você recebe o resultado da ferramenta (ex: "Resultado: Agendamento de exame cancelado com sucesso!"):**
    Sua ação: `RESPONDER_AO_USUARIO` -> Informe o usuário que o agendamento do exame foi cancelado.
    

[FORMATO DE SAÍDA OBRATÓRIO (JSON)]
{
  "status_processamento": "...",
  "intencao_detectada": "...",
  "entidades_extraidas": { "especialidade": null, "topico": null, "horario_id": null, "nome_paciente": null, "agendamento_id": null, "tipo_exame": null, "horario_exame_id": null,"agendamento_exame_id": null },
  "acao_requerida": "...",
  "payload_acao": {
    "resposta_para_usuario": "...",
    "ferramenta_solicitada": {
      "nome": null,
      "parametros": {}
    }
  },
  "log_para_desenvolvedor": "..."
}
"""

# --- FUNÇÃO PRINCIPAL DO AGENTE ---

def handle_message(user_chat_id: str, user_message: str):
    """
    Esta é a função principal que processa a mensagem do usuário.
    Contém toda a lógica de memória, IA e RAG.
    """
    try:
        # --- LÓGICA DE MEMÓRIA (FINAL) ---
        state_key = str(user_chat_id)
        current_state = CONVERSATION_STATE.get(state_key)
        
        augmented_message = user_message
        
        if current_state:
            print(f"--- MEMÓRIA: Estado encontrado: {current_state['state']} ---")
            state = current_state['state']
            context = current_state.get('context', {})

            if state == 'AWAITING_NAME': 
                horario_id = context.get('horario_id')
                augmented_message = f"[CONTEXTO: O usuário já escolheu o horario_id de consulta: {horario_id}. Esta mensagem é o NOME dele para o agendamento.] MENSAGEM DO USUÁRIO: {user_message}"
                del CONVERSATION_STATE[state_key]
            
            elif state == 'AWAITING_SLOT_CHOICE':
                horarios_mostrados = context.get('horarios_mostrados')
                augmented_message = f"[CONTEXTO: O usuário está escolhendo um ID da lista de horários de consulta que você acabou de mostrar: '{horarios_mostrados}'.] MENSAGEM DO USUÁRIO: {user_message}"

            elif state == 'AWAITING_CANCELLATION_CHOICE':
                agendamentos_mostrados = context.get('agendamentos_mostrados')
                augmented_message = f"[CONTEXTO: O usuário está escolhendo um ID da lista de agendamentos para cancelar que você acabou de mostrar: '{agendamentos_mostrados}'.] MENSAGEM DO USUÁRIO: {user_message}"
                del CONVERSATION_STATE[state_key]
            
            elif state == 'AWAITING_EXAM_TYPE':
                exames_mostrados = context.get('exames_mostrados')
                augmented_message = f"[CONTEXTO: O usuário está escolhendo um tipo de exame da lista que você acabou de mostrar: '{exames_mostrados}'.] MENSAGEM DO USUÁRIO: {user_message}"

            elif state == 'AWAITING_EXAM_SLOT_CHOICE':
                horarios_exame_mostrados = context.get('horarios_exame_mostrados')
                tipo_exame_escolhido = context.get('tipo_exame')
                augmented_message = f"[CONTEXTO: O usuário já escolheu o tipo de exame '{tipo_exame_escolhido}' e está escolhendo um ID da lista de horários de exame que você mostrou: '{horarios_exame_mostrados}'.] MENSAGEM DO USUÁRIO: {user_message}"

            elif state == 'AWAITING_NAME_FOR_EXAM':
                horario_exame_id = context.get('horario_exame_id')
                tipo_exame_escolhido = context.get('tipo_exame')
                augmented_message = f"[CONTEXTO: O usuário já escolheu o tipo de exame '{tipo_exame_escolhido}' e o horario_exame_id: {horario_exame_id}. Esta mensagem é o NOME dele para o agendamento do exame.] MENSAGEM DO USUÁRIO: {user_message}"
                del CONVERSATION_STATE[state_key]

           
            elif state == 'AWAITING_EXAM_CANCELLATION_CHOICE':
                agendamentos_exames_mostrados = context.get('agendamentos_exames_mostrados')
                augmented_message = f"[CONTEXTO: O usuário está escolhendo um ID da lista de agendamentos de EXAME para cancelar que você acabou de mostrar: '{agendamentos_exames_mostrados}'.] MENSAGEM DO USUÁRIO: {user_message}"
                del CONVERSATION_STATE[state_key] 


        print(f"--- Mensagem do Usuário Extraída (com contexto se houver) ---")
        print(f"De Chat ID: {user_chat_id}")
        print(f"Texto: {augmented_message}")
        print("-----------------------------------")
        
        # --- CÉREBRO (IDÊNTICO) ---
        if not model:
            print("ERRO: Modelo do Gemini não foi carregado.")
            return

        print("Enviando para o Gemini (Chamada 1)...")
        chat = model.start_chat(history=[
            {"role": "user", "parts": [SYSTEM_PROMPT]},
            {"role": "model", "parts": ["OK. Estou pronto para receber a mensagem do usuário."]}
        ])
        response = chat.send_message(augmented_message, generation_config=generation_config)
        ai_json_response_str = response.text
        print("--- Resposta JSON (Chamada 1) do Gemini Recebida ---")
        print(ai_json_response_str)
        print("--------------------------------------------------")
        
        # --- LÓGICA DE AÇÃO (RAG) (FINAL) ---
        try:
            ai_data = json.loads(ai_json_response_str)
            action = ai_data.get("acao_requerida")
            entidades = ai_data.get("entidades_extraidas", {})
            payload_acao = ai_data.get("payload_acao", {})
            resposta_texto = payload_acao.get("resposta_para_usuario")

            if action == "RESPONDER_AO_USUARIO":
                print(f"--- Ação: Responder Diretamente ---")
                
                # --- LÓGICA DE MEMÓRIA PÓS-RESPOSTA (FINAL) ---
                if "horario_id" in entidades and entidades["horario_id"] is not None and current_state and current_state['state'] == 'AWAITING_SLOT_CHOICE':
                    horario_id_selecionado = entidades["horario_id"]
                    CONVERSATION_STATE[state_key] = {
                        "state": "AWAITING_NAME",
                        "context": { "horario_id": horario_id_selecionado }
                    }
                    print(f"--- MEMÓRIA: Salvo estado 'AWAITING_NAME' para ID Consulta: {horario_id_selecionado} ---")
                
                elif "horario_exame_id" in entidades and entidades["horario_exame_id"] is not None and current_state and current_state['state'] == 'AWAITING_EXAM_SLOT_CHOICE':
                    horario_exame_id_selecionado = entidades["horario_exame_id"]
                    tipo_exame_context = current_state.get('context', {}).get('tipo_exame') 
                    CONVERSATION_STATE[state_key] = {
                        "state": "AWAITING_NAME_FOR_EXAM",
                        "context": { 
                            "horario_exame_id": horario_exame_id_selecionado,
                            "tipo_exame": tipo_exame_context 
                        }
                    }
                    print(f"--- MEMÓRIA: Salvo estado 'AWAITING_NAME_FOR_EXAM' para ID Exame: {horario_exame_id_selecionado} ---")
                
                
                send_telegram_message(user_chat_id, resposta_texto)
                    
            elif action == "EXECUTAR_FERRAMENTA":
                print("--- Ação: Executar Ferramenta (RAG) ---")
                tool_request = payload_acao.get("ferramenta_solicitada", {})
                tool_name = tool_request.get("nome")
                tool_params = tool_request.get("parametros", {})

                if tool_name and tool_name in AVAILABLE_TOOLS:
                    
                    # --- INJEÇÃO DE PARÂMETROS (FINAL) ---
                    if tool_name in ["tool_marcar_agendamento", "tool_listar_meus_agendamentos", 
                                     "tool_cancelar_agendamento", "tool_marcar_exame", 
                                     "tool_listar_meus_exames_agendados", "tool_cancelar_exame"]: 
                        tool_params["telegram_chat_id"] = state_key
                    
                    print(f"--- Executando Ferramenta: {tool_name} com params: {tool_params} ---")
                    tool_function = AVAILABLE_TOOLS[tool_name]
                    db_result = tool_function(**tool_params)
                    
                    # --- LÓGICA DE MEMÓRIA PÓS-FERRAMENTA (FINAL) ---
                    if tool_name == "tool_consultar_horarios_disponiveis":
                        CONVERSATION_STATE[state_key] = {"state": "AWAITING_SLOT_CHOICE", "context": { "horarios_mostrados": db_result }}
                        print(f"--- MEMÓRIA: Salvo estado 'AWAITING_SLOT_CHOICE' ---")
                    elif tool_name == "tool_listar_meus_agendamentos":
                        if "Você não possui agendamentos" not in db_result:
                            CONVERSATION_STATE[state_key] = {"state": "AWAITING_CANCELLATION_CHOICE", "context": { "agendamentos_mostrados": db_result }}
                            print(f"--- MEMÓRIA: Salvo estado 'AWAITING_CANCELLATION_CHOICE' ---")
                    elif tool_name == "tool_consultar_exames_disponiveis":
                         if "Não há tipos de exames cadastrados" not in db_result:
                            CONVERSATION_STATE[state_key] = {"state": "AWAITING_EXAM_TYPE", "context": { "exames_mostrados": db_result }}
                            print(f"--- MEMÓRIA: Salvo estado 'AWAITING_EXAM_TYPE' ---")
                    elif tool_name == "tool_consultar_horarios_exames":
                         if "não encontramos horários disponíveis" not in db_result:
                            tipo_exame_escolhido = tool_params.get("tipo_exame", "Desconhecido") 
                            CONVERSATION_STATE[state_key] = {"state": "AWAITING_EXAM_SLOT_CHOICE", "context": { "horarios_exame_mostrados": db_result, "tipo_exame": tipo_exame_escolhido }}
                            print(f"--- MEMÓRIA: Salvo estado 'AWAITING_EXAM_SLOT_CHOICE' para o exame '{tipo_exame_escolhido}' ---")
                    # --- NOVO ESTADO PARA CANCELAR EXAME ---
                    elif tool_name == "tool_listar_meus_exames_agendados":
                         if "Você não possui agendamentos de exames" not in db_result:
                            CONVERSATION_STATE[state_key] = {"state": "AWAITING_EXAM_CANCELLATION_CHOICE", "context": { "agendamentos_exames_mostrados": db_result }}
                            print(f"--- MEMÓRIA: Salvo estado 'AWAITING_EXAM_CANCELLATION_CHOICE' ---")

                    # --- CHAMADA 2 RAG (IDÊNTICO) ---
                    print("--- Enviando para o Gemini (Chamada 2 - RAG)... ---")
                    rag_prompt = f"OK, a ferramenta {tool_name} foi executada. O resultado é: '{db_result}'. Com base *apenas* nesse resultado, gere a resposta final para o usuário."
                    response_rag = chat.send_message(rag_prompt, generation_config=generation_config)
                    final_ai_json_str = response_rag.text
                    print("--- Resposta JSON Final (RAG) do Gemini Recebida ---")
                    print(final_ai_json_str)
                    print("--------------------------------------------------")
                    
                    final_ai_data = json.loads(final_ai_json_str)
                    
                    if final_ai_data.get("acao_requerida") == "RESPONDER_AO_USUARIO":
                        final_response_text = final_ai_data["payload_acao"]["resposta_para_usuario"]
                        print(f"--- Ação: Responder com dados do DB ---")
                        send_telegram_message(user_chat_id, final_response_text)
                    else:
                        print("ERRO RAG: A IA não gerou uma resposta final, mesmo após os dados do DB.")
                        send_telegram_message(user_chat_id, "Desculpe, tive um problema ao processar sua solicitação após consultar os dados.")
                else:
                    print(f"ERRO: A IA solicitou uma ferramenta desconhecida: {tool_name}")
                    send_telegram_message(user_chat_id, "Desculpe, a IA pediu uma ferramenta que eu não conheço.")
            else:
                print(f"Ação desconhecida recebida da IA: {action}")
                send_telegram_message(user_chat_id, f"Desculpe, recebi uma ação desconhecida ({action}) e não sei o que fazer.")

        except json.JSONDecodeError:
            print("ERRO FATAL: Gemini retornou um JSON inválido.")
            print(ai_json_response_str) 
            send_telegram_message(user_chat_id, "Desculpe, a resposta da IA veio em um formato inválido.")

    except Exception as e:
        print(f"Erro inesperado na função handle_message: {e}")
        if user_chat_id:
            send_telegram_message(user_chat_id, "Desculpe, ocorreu um erro interno grave ao processar sua mensagem.")