import sqlite3

DATABASE_FILE = 'clinic.db'

def tool_obter_info_clinica(topic: str) -> str:
    """
    Busca no banco de dados a informação com base no tópico.
    """
    if not topic:
        return "Tópico não fornecido."

    print(f"--- FERRAMENTA DB: Buscando pelo tópico: {topic} ---")

    try:
        # Conecta ao DB
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Busca o valor (usamos 'topic = ?' para evitar SQL Injection)
        cursor.execute("SELECT value FROM info WHERE topic = ?", (topic,))
        result = cursor.fetchone() # Pega o primeiro resultado

        conn.close()

        if result:
            # result é uma tupla (ex: ('Rua das Flores...',)), 
            # então pegamos o primeiro item
            print(f"--- FERRAMENTA DB: Informação encontrada: {result[0]} ---")
            return result[0]
        else:
            print("--- FERRAMENTA DB: Tópico não encontrado no banco. ---")
            return f"Informação sobre '{topic}' não encontrada."

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao acessar o SQLite: {e} ---")
        return "Ocorreu um erro ao consultar o banco de dados."
    
def tool_consultar_horarios_disponiveis(especialidade: str) -> str:
    """
    Busca horários disponíveis por especialidade, juntando com os nomes dos médicos.
    Retorna uma string formatada ou uma mensagem de "não encontrado".
    """
    if not especialidade:
        return "Especialidade não fornecida."

    print(f"--- FERRAMENTA DB: Buscando horários para: {especialidade} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Query SQL que junta medicos e horarios, filtrando por especialidade e status
        query = """
        SELECT h.id, m.nome, h.data_hora_inicio
        FROM horarios_disponiveis h
        JOIN medicos m ON h.medico_id = m.id
        WHERE m.especialidade LIKE ? AND h.status = 'disponivel'
        ORDER BY h.data_hora_inicio;
        """

        # Usamos '%' para permitir buscas parciais (ex: 'Cardio' encontra 'Cardiologia')
        cursor.execute(query, ('%' + especialidade + '%',))
        resultados = cursor.fetchall()
        conn.close()

        if not resultados:
            print("--- FERRAMENTA DB: Nenhum horário encontrado. ---")
            return f"Desculpe, não encontramos horários disponíveis para a especialidade '{especialidade}'."

        # Formata a saída para a IA ler
        # Ex: "ID 1: Dra. Ana Silva - 2025-10-24 09:00:00; ID 2: ..."
        horarios_formatados = []
        for (id, nome, data_hora) in resultados:
            horarios_formatados.append(f"[ID {id}: {nome} - {data_hora}]")

        resposta = "; ".join(horarios_formatados)
        print(f"--- FERRAMENTA DB: Horários encontrados: {resposta} ---")
        return resposta

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao consultar horários: {e} ---")
        return "Ocorreu um erro ao consultar os horários."
    

def tool_marcar_agendamento(horario_id: int, nome_paciente: str, telegram_chat_id: str) -> str:
    """
    Marca um agendamento.
    1. Atualiza o status do horário para 'agendado'.
    2. Insere o agendamento na tabela 'agendamentos'.
    Retorna uma mensagem de sucesso ou erro.
    """
    if not horario_id or not nome_paciente or not telegram_chat_id:
        return "Erro: ID do horário, nome do paciente e ID do chat são obrigatórios."

    print(f"--- FERRAMENTA DB: Tentando agendar ID {horario_id} para {nome_paciente} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Etapa 1: Verificar se o horário ainda está 'disponivel'
        cursor.execute("SELECT status FROM horarios_disponiveis WHERE id = ?", (horario_id,))
        result = cursor.fetchone()

        if not result:
            conn.close()
            print("--- FERRAMENTA DB: Erro - Horário ID não encontrado. ---")
            return f"Erro: O ID de horário {horario_id} não existe."

        if result[0] != 'disponivel':
            conn.close()
            print("--- FERRAMENTA DB: Erro - Horário não está mais disponível. ---")
            return f"Desculpe, o horário {horario_id} não está mais disponível. Alguém pode ter agendado."

        # Etapa 2: Atualizar o status do horário
        cursor.execute("UPDATE horarios_disponiveis SET status = 'agendado' WHERE id = ?", (horario_id,))

        # Etapa 3: Inserir na tabela de agendamentos
        cursor.execute(
            "INSERT INTO agendamentos (horario_id, nome_paciente, telegram_chat_id) VALUES (?, ?, ?)",
            (horario_id, nome_paciente, telegram_chat_id)
        )

        conn.commit()
        conn.close()

        print("--- FERRAMENTA DB: Agendamento realizado com sucesso. ---")
        return "Agendamento confirmado com sucesso!"

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao marcar agendamento: {e} ---")
        return f"Ocorreu um erro de banco de dados ao tentar marcar o agendamento: {e}"
    
 

def tool_listar_meus_agendamentos(telegram_chat_id: str) -> str:
    """
    Busca os agendamentos futuros confirmados de um usuário específico.
    Retorna uma string formatada com os IDs dos agendamentos ou "nenhum encontrado".
    """
    if not telegram_chat_id:
        return "Erro: ID do chat do Telegram não fornecido."

    print(f"--- FERRAMENTA DB: Listando agendamentos para Chat ID: {telegram_chat_id} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Query que busca agendamentos confirmados futuros do usuário,
        # juntando com médicos e horários
        query = """
        SELECT a.id, m.nome, h.data_hora_inicio
        FROM agendamentos a
        JOIN horarios_disponiveis h ON a.horario_id = h.id
        JOIN medicos m ON h.medico_id = m.id
        WHERE a.telegram_chat_id = ? AND a.status = 'confirmado' AND h.data_hora_inicio > datetime('now', 'localtime')
        ORDER BY h.data_hora_inicio;
        """
        # Nota: datetime('now', 'localtime') pega a data/hora atual no fuso horário do servidor

        cursor.execute(query, (telegram_chat_id,))
        resultados = cursor.fetchall()
        conn.close()

        if not resultados:
            print("--- FERRAMENTA DB: Nenhum agendamento futuro encontrado. ---")
            return "Você não possui agendamentos futuros confirmados."

        # Formata a saída para a IA ler, incluindo o ID do AGENDAMENTO (a.id)
        agendamentos_formatados = []
        for (id_agendamento, nome_medico, data_hora) in resultados:
            agendamentos_formatados.append(f"[ID {id_agendamento}: {nome_medico} - {data_hora}]")

        resposta = "; ".join(agendamentos_formatados)
        print(f"--- FERRAMENTA DB: Agendamentos encontrados: {resposta} ---")
        return resposta

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao listar agendamentos: {e} ---")
        return f"Ocorreu um erro ao consultar seus agendamentos: {e}"

def tool_cancelar_agendamento(agendamento_id: int, telegram_chat_id: str) -> str:
    """
    Cancela um agendamento específico do usuário.
    1. Verifica se o agendamento pertence ao usuário.
    2. Atualiza o status do agendamento para 'cancelado'.
    3. Atualiza o status do horário correspondente de volta para 'disponivel'.
    Retorna uma mensagem de sucesso ou erro.
    """
    if not agendamento_id or not telegram_chat_id:
        return "Erro: ID do agendamento e ID do chat são obrigatórios."

    print(f"--- FERRAMENTA DB: Tentando cancelar agendamento ID {agendamento_id} para Chat ID {telegram_chat_id} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Etapa 1: Verificar se o agendamento existe, pertence ao usuário e está confirmado
        cursor.execute(
            "SELECT horario_id, status FROM agendamentos WHERE id = ? AND telegram_chat_id = ?",
            (agendamento_id, telegram_chat_id)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            print("--- FERRAMENTA DB: Erro - Agendamento não encontrado ou não pertence ao usuário. ---")
            return f"Erro: Agendamento com ID {agendamento_id} não encontrado ou não pertence a você."

        horario_id, status_agendamento = result

        if status_agendamento != 'confirmado':
            conn.close()
            print(f"--- FERRAMENTA DB: Erro - Agendamento já está '{status_agendamento}'. ---")
            return f"Este agendamento (ID {agendamento_id}) não está confirmado (status atual: {status_agendamento}), portanto não pode ser cancelado."

        # Etapa 2: Atualizar o status do agendamento para 'cancelado'
        cursor.execute("UPDATE agendamentos SET status = 'cancelado' WHERE id = ?", (agendamento_id,))

        # Etapa 3: Atualizar o status do horário de volta para 'disponivel'
        cursor.execute("UPDATE horarios_disponiveis SET status = 'disponivel' WHERE id = ?", (horario_id,))

        conn.commit()
        conn.close()

        print("--- FERRAMENTA DB: Agendamento cancelado com sucesso. Horário liberado. ---")
        return "Agendamento cancelado com sucesso!"

    except Exception as e:
        conn.rollback() # Desfaz as alterações se der erro
        conn.close()
        print(f"--- FERRAMENTA DB: ERRO ao cancelar agendamento: {e} ---")
        return f"Ocorreu um erro de banco de dados ao tentar cancelar o agendamento: {e}"
    
def tool_consultar_exames_disponiveis() -> str:
    """
    Lista os tipos de exames simples disponíveis para agendamento.
    """
    print(f"--- FERRAMENTA DB: Listando tipos de exames disponíveis ---")
    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()
        cursor.execute("SELECT nome_exame FROM exames ORDER BY nome_exame;")
        resultados = cursor.fetchall()
        conn.close()

        if not resultados:
            return "Não há tipos de exames cadastrados no momento."

        nomes_exames = [r[0] for r in resultados]
        resposta = "; ".join(nomes_exames)
        print(f"--- FERRAMENTA DB: Exames encontrados: {resposta} ---")
        return resposta

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao listar exames: {e} ---")
        return f"Ocorreu um erro ao consultar os tipos de exames: {e}"

def tool_consultar_horarios_exames(tipo_exame: str) -> str:
    """
    Busca horários disponíveis para um tipo específico de exame.
    Retorna uma string formatada com IDs ou "não encontrado".
    """
    if not tipo_exame:
        return "Tipo de exame não fornecido."

    print(f"--- FERRAMENTA DB: Buscando horários para exame: {tipo_exame} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        query = """
        SELECT h.id, h.data_hora_inicio
        FROM horarios_exames h
        JOIN exames e ON h.exame_id = e.id
        WHERE e.nome_exame LIKE ? AND h.status = 'disponivel'
        ORDER BY h.data_hora_inicio;
        """
        cursor.execute(query, ('%' + tipo_exame + '%',))
        resultados = cursor.fetchall()
        conn.close()

        if not resultados:
            print("--- FERRAMENTA DB: Nenhum horário encontrado para este exame. ---")
            return f"Desculpe, não encontramos horários disponíveis para '{tipo_exame}'."

        horarios_formatados = []
        for (id_horario, data_hora) in resultados:
            horarios_formatados.append(f"[ID {id_horario}: {data_hora}]")

        resposta = "; ".join(horarios_formatados)
        print(f"--- FERRAMENTA DB: Horários de exame encontrados: {resposta} ---")
        return resposta

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao consultar horários de exame: {e} ---")
        return f"Ocorreu um erro ao consultar os horários para '{tipo_exame}': {e}"

def tool_marcar_exame(horario_exame_id: int, nome_paciente: str, telegram_chat_id: str) -> str:
    """
    Marca um agendamento de exame.
    1. Verifica se o horário está disponível.
    2. Atualiza o status do horário para 'agendado'.
    3. Insere o agendamento na tabela 'agendamentos_exames'.
    Retorna uma mensagem de sucesso ou erro.
    """
    if not horario_exame_id or not nome_paciente or not telegram_chat_id:
        return "Erro: ID do horário do exame, nome do paciente e ID do chat são obrigatórios."

    print(f"--- FERRAMENTA DB: Tentando agendar exame (Horário ID {horario_exame_id}) para {nome_paciente} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Etapa 1: Verificar disponibilidade
        cursor.execute("SELECT status FROM horarios_exames WHERE id = ?", (horario_exame_id,))
        result = cursor.fetchone()

        if not result:
            conn.close(); return f"Erro: O ID de horário de exame {horario_exame_id} não existe."
        if result[0] != 'disponivel':
            conn.close(); return f"Desculpe, o horário {horario_exame_id} não está mais disponível."

        # Etapa 2: Atualizar status do horário
        cursor.execute("UPDATE horarios_exames SET status = 'agendado' WHERE id = ?", (horario_exame_id,))

        # Etapa 3: Inserir na tabela de agendamentos de exames
        cursor.execute(
            "INSERT INTO agendamentos_exames (horario_exame_id, nome_paciente, telegram_chat_id) VALUES (?, ?, ?)",
            (horario_exame_id, nome_paciente, telegram_chat_id)
        )

        conn.commit()
        conn.close()

        print("--- FERRAMENTA DB: Agendamento de exame realizado com sucesso. ---")
        return "Agendamento de exame confirmado com sucesso!"

    except Exception as e:
        conn.rollback()
        conn.close()
        print(f"--- FERRAMENTA DB: ERRO ao marcar agendamento de exame: {e} ---")
        return f"Ocorreu um erro de banco de dados ao tentar marcar o exame: {e}"
    
def tool_listar_meus_exames_agendados(telegram_chat_id: str) -> str:
    """
    Busca os agendamentos de exames futuros confirmados de um usuário específico.
    Retorna uma string formatada com os IDs dos agendamentos de exame ou "nenhum encontrado".
    """
    if not telegram_chat_id:
        return "Erro: ID do chat do Telegram não fornecido."

    print(f"--- FERRAMENTA DB: Listando agendamentos de EXAMES para Chat ID: {telegram_chat_id} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Query que busca agendamentos de exames confirmados futuros do usuário,
        # juntando com exames (nome) e horários (data/hora)
        query = """
        SELECT ae.id, e.nome_exame, he.data_hora_inicio
        FROM agendamentos_exames ae
        JOIN horarios_exames he ON ae.horario_exame_id = he.id
        JOIN exames e ON he.exame_id = e.id
        WHERE ae.telegram_chat_id = ? AND ae.status = 'confirmado' AND he.data_hora_inicio > datetime('now', 'localtime')
        ORDER BY he.data_hora_inicio;
        """

        cursor.execute(query, (telegram_chat_id,))
        resultados = cursor.fetchall()
        conn.close()

        if not resultados:
            print("--- FERRAMENTA DB: Nenhum agendamento de exame futuro encontrado. ---")
            return "Você não possui agendamentos de exames futuros confirmados."

        # Formata a saída para a IA ler, incluindo o ID do AGENDAMENTO DE EXAME (ae.id)
        agendamentos_formatados = []
        for (id_agendamento_exame, nome_exame, data_hora) in resultados:
            agendamentos_formatados.append(f"[ID {id_agendamento_exame}: {nome_exame} - {data_hora}]")

        resposta = "; ".join(agendamentos_formatados)
        print(f"--- FERRAMENTA DB: Agendamentos de exame encontrados: {resposta} ---")
        return resposta

    except Exception as e:
        print(f"--- FERRAMENTA DB: ERRO ao listar agendamentos de exames: {e} ---")
        return f"Ocorreu um erro ao consultar seus agendamentos de exames: {e}"

def tool_cancelar_exame(agendamento_exame_id: int, telegram_chat_id: str) -> str:
    """
    Cancela um agendamento de exame específico do usuário.
    1. Verifica se o agendamento de exame pertence ao usuário.
    2. Atualiza o status do agendamento de exame para 'cancelado'.
    3. Atualiza o status do horário de exame correspondente de volta para 'disponivel'.
    Retorna uma mensagem de sucesso ou erro.
    """
    if not agendamento_exame_id or not telegram_chat_id:
        return "Erro: ID do agendamento de exame e ID do chat são obrigatórios."

    print(f"--- FERRAMENTA DB: Tentando cancelar agendamento de EXAME ID {agendamento_exame_id} para Chat ID {telegram_chat_id} ---")

    try:
        conn = sqlite3.connect(DATABASE_FILE)
        cursor = conn.cursor()

        # Etapa 1: Verificar se o agendamento existe, pertence ao usuário e está confirmado
        cursor.execute(
            "SELECT horario_exame_id, status FROM agendamentos_exames WHERE id = ? AND telegram_chat_id = ?",
            (agendamento_exame_id, telegram_chat_id)
        )
        result = cursor.fetchone()

        if not result:
            conn.close()
            print("--- FERRAMENTA DB: Erro - Agendamento de exame não encontrado ou não pertence ao usuário. ---")
            return f"Erro: Agendamento de exame com ID {agendamento_exame_id} não encontrado ou não pertence a você."

        horario_exame_id, status_agendamento = result

        if status_agendamento != 'confirmado':
            conn.close()
            print(f"--- FERRAMENTA DB: Erro - Agendamento de exame já está '{status_agendamento}'. ---")
            return f"Este agendamento de exame (ID {agendamento_exame_id}) não está confirmado (status atual: {status_agendamento}), portanto não pode ser cancelado."

        # Etapa 2: Atualizar o status do agendamento de exame para 'cancelado'
        cursor.execute("UPDATE agendamentos_exames SET status = 'cancelado' WHERE id = ?", (agendamento_exame_id,))

        # Etapa 3: Atualizar o status do horário de exame de volta para 'disponivel'
        # (Certifique-se que a tabela é horarios_exames)
        cursor.execute("UPDATE horarios_exames SET status = 'disponivel' WHERE id = ?", (horario_exame_id,))

        conn.commit()
        conn.close()

        print("--- FERRAMENTA DB: Agendamento de exame cancelado com sucesso. Horário liberado. ---")
        return "Agendamento de exame cancelado com sucesso!"

    except Exception as e:
        conn.rollback() # Desfaz as alterações se der erro
        conn.close()
        print(f"--- FERRAMENTA DB: ERRO ao cancelar agendamento de exame: {e} ---")
        return f"Ocorreu um erro de banco de dados ao tentar cancelar o agendamento do exame: {e}"