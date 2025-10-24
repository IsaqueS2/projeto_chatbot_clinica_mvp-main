# 🤖 Chatbot de Clínica Médica com IA (MVP Funcional - Telegram)

Este é um projeto de MVP (Minimum Viable Product) **funcional** para um chatbot de atendimento de clínica médica, utilizando a **API do Telegram**, FastAPI (Python) e a IA do Google (Gemini) para processamento de linguagem natural e gerenciamento de fluxo de conversa.

O objetivo foi criar um agente de IA capaz de entender solicitações complexas de usuários (agendamentos, cancelamentos, consultas), interagir com um banco de dados (SQLite) para buscar informações e registrar ações, mantendo o contexto da conversa através de múltiplos passos.

## ✅ Status Atual do Projeto: MVP Completo!

O projeto alcançou o status de MVP funcional. Todas as funcionalidades principais planejadas foram implementadas e testadas com sucesso usando a API do Telegram.

### O que Foi Feito (Funcionalidades Implementadas):

* **Canal de Comunicação:** Integração completa com a **API do Telegram** (Webhook para receber mensagens, API para enviar respostas).
    * *(Nota: A integração inicial com a API do WhatsApp foi abandonada devido a bloqueios e instabilidade da conta de teste da Meta).*
* **Processamento de Linguagem Natural (IA):**
    * Uso do **Google Gemini (Flash)** como cérebro do agente.
    * **Prompt de Sistema Detalhado:** Define a persona, regras, ferramentas e fluxos de conversa multi-etapas (agendamento, cancelamento).
    * **Saída Estruturada em JSON:** A IA comunica suas intenções e dados extraídos de forma confiável para o backend Python.
    * **Classificação de Intenção:** Identifica corretamente `agendamento` (consulta/exame), `cancelamento` (consulta/exame), `consulta_info`, `saudacao`, `despedida`, `fora_de_escopo`.
    * **Extração de Entidades:** Extrai dados relevantes como `especialidade`, `topic`, `horario_id`, `nome_paciente`, `agendamento_id`, `tipo_exame`, `horario_exame_id`.
* **Backend e Lógica:**
    * Servidor **FastAPI** robusto e refatorado, separando responsabilidades (Servidor, Agente, Utilitários).
    * **Gerenciamento de Estado (Memória):** Um dicionário em memória (`CONVERSATION_STATE`) mantém o contexto da conversa durante fluxos multi-etapas (ex: lembra o ID do horário enquanto pergunta o nome).
    * **Fluxo RAG (Retrieval-Augmented Generation):** O agente consulta o banco de dados via "ferramentas" e usa a informação obtida para gerar a resposta final com a IA.
* **Banco de Dados (SQLite):**
    * Estrutura de banco de dados definida para `info`, `medicos`, `horarios_disponiveis`, `exames`, `horarios_exames`, `agendamentos`, `agendamentos_exames`.
    * **Ferramentas de Leitura:** Consulta de informações gerais, horários de consulta/exame, listagem de agendamentos/exames do usuário.
    * **Ferramentas de Escrita:** Marcação e cancelamento de agendamentos/exames, com atualização de status dos horários.
* **Organização do Projeto:**
    * Código refatorado em módulos (`config.py`, `telegram_utils.py`, `agent.py`, `main.py`, `database_tools.py`).
    * `requirements.txt` para fácil instalação de dependências.
    * `.gitignore` configurado.
    * Este `README.md` documentando o projeto.

### Funcionalidades Específicas do Chatbot:

* **Consulta de Informações:** Responde sobre endereço, horário de funcionamento e convênios.
* **Agendamento de Consultas:** Guia o usuário na escolha da especialidade, mostra horários disponíveis (com IDs), pede o nome e confirma o agendamento.
* **Cancelamento de Consultas:** Lista os agendamentos do usuário (com IDs), pergunta qual cancelar e confirma o cancelamento, liberando o horário.
* **Agendamento de Exames Simples:** Lista os tipos de exame, ou busca horários para um exame específico, guia na escolha do horário (com IDs), pede o nome e confirma o agendamento.
* **Cancelamento de Exames:** Lista os exames agendados pelo usuário (com IDs), pergunta qual cancelar e confirma o cancelamento, liberando o horário.
* **Tratamento de Perguntas Fora de Escopo.**

## 🛠️ Stack de Tecnologia

* **Backend:** FastAPI (Python)
* **Servidor:** Uvicorn
* **IA (LLM):** Google Gemini Flash (via `google-generativeai`)
* **Canal (API):** API Oficial do Telegram
* **Banco de Dados:** SQLite
* **Túnel (Testes):** ngrok

## 🏁 Como Executar

1.  **Clone o repositório:** `git clone [URL]` e `cd [PASTA]`
2.  **Crie e ative o venv:** `python -m venv venv` e ative (`.\venv\Scripts\activate` ou `source venv/bin/activate`).
3.  **Instale as dependências:** `pip install -r requirements.txt`
4.  **Crie e preencha o `.env`:** Copie o `.env.example`, renomeie para `.env` e adicione suas chaves da API do Google Gemini e do BotFather (Telegram).
5.  **Configure o Banco de Dados (Uma vez):** `python database_setup.py`
6.  **Inicie o servidor FastAPI (Terminal 1):** `uvicorn main:app --reload`
7.  **Inicie o túnel ngrok (Terminal 2):** `ngrok http 8000` (copie a URL `https://...`)
8.  **Configure o Webhook no Telegram (Uma vez por URL do ngrok):** `python set_webhook.py` (cole a URL do ngrok quando pedir).
9.  **Converse com seu bot no Telegram!**

## 🚀 Próximos Passos Possíveis (Pós-MVP)

* **Melhorar a Gestão de Estado:** Usar Redis ou um banco de dados para a memória (`CONVERSATION_STATE`), em vez de um dicionário Python (que se perde ao reiniciar o servidor).
* **Adicionar Autenticação/Identificação do Paciente:** Integrar com o cadastro real de pacientes da clínica (talvez pedindo CPF ou data de nascimento).
* **Gerenciamento de Horários Mais Complexo:** Lidar com durações diferentes de consulta/exame, bloqueio de horários, etc.
* **Interface Administrativa:** Um painel para a clínica ver os agendamentos feitos pelo bot.
* **Deploy:** Publicar o bot em um servidor na nuvem (ex: Railway, Vercel, Google Cloud Run) para que ele funcione 24/7 sem `ngrok`.
* **(Opcional) Tentar Novamente com WhatsApp:** Com um número de telefone *real* e uma conta empresarial *verificada* na Meta, a API do WhatsApp pode ser mais estável.