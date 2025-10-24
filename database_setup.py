import sqlite3

def setup_database():
    conn = sqlite3.connect('clinic.db')
    cursor = conn.cursor()

    # --- Tabela de Informações (Já existe) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS info (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        topic TEXT NOT NULL UNIQUE,
        value TEXT NOT NULL
    )
    ''')
    info_data = [
        ('endereco', 'Nosso endereço é Rua das Flores, 123 - Centro.'),
        ('horario_funcionamento', 'Atendemos de Segunda a Sexta, das 08:00 às 18:00.'),
        ('convenios_aceitos', 'Aceitamos os convênios Unimed, Bradesco Saúde e SulAmérica.')
    ]
    cursor.executemany("INSERT OR IGNORE INTO info (topic, value) VALUES (?, ?)", info_data)

    # --- NOVO: Tabela de Médicos ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS medicos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome TEXT NOT NULL,
        especialidade TEXT NOT NULL
    )
    ''')
    medicos_data = [
        (1, 'Dra. Ana Silva', 'Cardiologia'),
        (2, 'Dr. Bruno Costa', 'Dermatologia'),
        (3, 'Dr. Carlos Dias', 'Cardiologia')
    ]
    cursor.executemany("INSERT OR IGNORE INTO medicos (id, nome, especialidade) VALUES (?, ?, ?)", medicos_data)
    print("Tabela 'medicos' e dados de exemplo inseridos.")

    # --- NOVO: Tabela de Horários Disponíveis (Para Consultas) ---
    # No futuro, o 'status' mudará para 'agendado'
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS horarios_disponiveis (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        medico_id INTEGER NOT NULL,
        data_hora_inicio DATETIME NOT NULL,
        status TEXT NOT NULL DEFAULT 'disponivel',
        FOREIGN KEY (medico_id) REFERENCES medicos (id)
    )
    ''')
    # Vamos usar datas relativas ao dia que você está testando (23/10/2025)
    horarios_data = [
        # Horários para Dra. Ana Silva (Cardiologia)
        (1, 1, '2025-10-24 09:00:00', 'disponivel'),
        (2, 1, '2025-10-24 10:00:00', 'disponivel'),
        # Horários para Dr. Bruno Costa (Dermatologia)
        (3, 2, '2025-10-24 14:00:00', 'disponivel'),
        # Horários para Dr. Carlos Dias (Cardiologia)
        (4, 3, '2025-10-24 09:00:00', 'disponivel')
    ]
    cursor.executemany("INSERT OR IGNORE INTO horarios_disponiveis (id, medico_id, data_hora_inicio, status) VALUES (?, ?, ?, ?)", horarios_data)
    print("Tabela 'horarios_disponiveis' e dados de exemplo inseridos.")

    # --- NOVO: Tabela de Tipos de Exames ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS exames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        nome_exame TEXT NOT NULL UNIQUE,
        descricao TEXT 
    )
    ''')
    exames_data = [
        ('Check-up Geral', 'Exames de rotina para avaliação geral da saúde.'),
        ('Exame de Sangue', 'Coleta de sangue para análise laboratorial.'),
        ('Eletrocardiograma (ECG)', 'Exame que avalia a atividade elétrica do coração.')
    ]
    cursor.executemany("INSERT OR IGNORE INTO exames (nome_exame, descricao) VALUES (?, ?)", exames_data)
    print("Tabela 'exames' e dados de exemplo inseridos.")

   # --- NOVO: Tabela de Horários Disponíveis para Exames ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS horarios_exames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        exame_id INTEGER NOT NULL,
        data_hora_inicio DATETIME NOT NULL,
        status TEXT NOT NULL DEFAULT 'disponivel', 
        FOREIGN KEY (exame_id) REFERENCES exames (id)
    )
    ''')
    # Exemplo: Check-up (ID 1), Sangue (ID 2), ECG (ID 3)
    horarios_exames_data = [
        # Horários para Check-up Geral
        (1, 1, '2025-10-25 08:00:00', 'disponivel'), 
        (2, 1, '2025-10-25 08:30:00', 'disponivel'),
        # Horários para Exame de Sangue (geralmente pela manhã)
        (3, 2, '2025-10-25 07:00:00', 'disponivel'),
        (4, 2, '2025-10-25 07:30:00', 'disponivel'),
        # Horários para ECG
        (5, 3, '2025-10-25 10:00:00', 'disponivel') 
    ]
    cursor.executemany("INSERT OR IGNORE INTO horarios_exames (id, exame_id, data_hora_inicio, status) VALUES (?, ?, ?, ?)", horarios_exames_data)
    print("Tabela 'horarios_exames' e dados de exemplo inseridos.")

    # --- NOVO: Tabela de Agendamentos de Exames ---
    # (Poderíamos usar a tabela 'agendamentos', mas separar pode ser mais claro)
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos_exames (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horario_exame_id INTEGER NOT NULL,
        nome_paciente TEXT NOT NULL,
        telegram_chat_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'confirmado',
        FOREIGN KEY (horario_exame_id) REFERENCES horarios_exames (id)
    )
    ''')
    print("Tabela 'agendamentos_exames' criada.")

    # --- NOVO: Tabela de Agendamentos (Vazia por enquanto) ---
    cursor.execute('''
    CREATE TABLE IF NOT EXISTS agendamentos (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        horario_id INTEGER NOT NULL,
        nome_paciente TEXT NOT NULL,
        telegram_chat_id TEXT NOT NULL,
        status TEXT NOT NULL DEFAULT 'confirmado',
        FOREIGN KEY (horario_id) REFERENCES horarios_disponiveis (id)
    )
    ''')
    print("Tabela 'agendamentos' criada.")

    conn.commit()
    conn.close()

if __name__ == "__main__":
    print("Iniciando setup do banco de dados (Fase 5 - Exames)...")
    # --- Certifique-se de que o código das tabelas anteriores está colado acima ---
    # setup_database() # Removido temporariamente para evitar duplicação se o código acima não foi colado
    print("ATENÇÃO: Cole o código das tabelas info, medicos, etc., acima antes de rodar.")
    # Quando o código estiver completo, descomente a linha abaixo:
    setup_database() 
    print("Banco de dados 'clinic.db' está pronto com tabelas de exames.")