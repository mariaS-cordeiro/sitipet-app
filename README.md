# 🐾 SitiPet - Aplicativo de Gestão para Pet Shop e Hotelzinho

Sistema completo e integrado para gestão diária de Pet Shop e Hotelzinho desenvolvido em Python com **Streamlit**, compatível com **Streamlit Cloud**, **GitHub** e **Google Sheets / Google Drive** (`sitipet01@gmail.com`).

---

## 🌟 Funcionalidades Principais

1. **📊 Painel Geral (Dashboard):**
   - Indicadores rápidos: Atendimentos de hoje, cães hospedados agora, faturamento do mês e saldo em caixa.
   - Central de alertas inteligentes para atendimentos em breve (< 45 min), atrasados e check-outs do dia.

2. **📅 Aba 1 – Agenda Diária:**
   - Cadastro e visualização de atendimentos ordenados por horário.
   - Alertas visuais de status (🟢 No horário, 🟡 Em breve, 🔴 Atrasado, 🔵 Em atendimento, ✅ Finalizado).
   - Botão **"Concluir & Enviar ao Caixa"** com fluxo integrado direto para Banho/Tosa e fluxo financeiro.
   - Botão direto para contato via WhatsApp com o tutor.

3. **✂️ Aba 2 – Banho e Tosa:**
   - Cadastro completo de atendimentos com dados do pet, tutor, raça, porte e profissional.
   - Seleção múltipla de serviços de tosa (raspada, bebê, tesoura, higiênica, completa, da raça, etc.) e banho/adicionais (simples, hidratação, unhas, ouvidos, dentes).
   - Valores individuais editáveis e cálculo automático do total.
   - Histórico pesquisável por pet, tutor ou profissional.

4. **🏨 Aba 3 – Hospedagem / Hotel:**
   - Registro de check-in e check-out com cálculo automático de diárias e valor total.
   - Ficha de cuidados: alimentação, refeições/dia, medicação, comportamento, restrições e contato de emergência.
   - Duas visualizações: **Animais Atualmente Hospedados** (com botão de check-out) e **Histórico Completo**.

5. **💰 Aba 4 – Caixa e Gestão Financeira:**
   - Lançamento de Entradas, Saídas e Descontos.
   - Totalizadores automáticos de Entradas, Saídas, Descontos e Saldo.
   - Filtro por Mês e Ano preservando todo o histórico de anos anteriores.
   - **Gráfico de Pizza Interativo (Plotly)** com a participação percentual de cada serviço no faturamento.
   - **Indicadores Estratégicos:**
     - 🏆 *Serviço Mais Realizado* (Volume de atendimentos).
     - 💰 *Serviço com Maior Faturamento* (Receita gerada em R$).
   - Extrato financeiro com exportação para CSV e Excel.

6. **☁️ Persistência Híbrida Google Sheets + Local:**
   - Funciona imediatamente em modo local (`sitipet_db.json`).
   - Sincronização em nuvem contínua com a planilha `SITIPET - Gestão` compartilhada com `sitipet01@gmail.com`.

---

## 🚀 Como Executar o Projeto Localmente

### 1. Pré-requisitos
- Ter o **Python 3.10+** instalado no computador.

### 2. Instalar as dependências
Abra o terminal na pasta do projeto e execute:
```bash
pip install -r requirements.txt
```

### 3. Rodar a aplicação Streamlit
```bash
streamlit run app.py
```
O navegador abrirá automaticamente no endereço `http://localhost:8501`.

---

## 🌐 Como Publicar no GitHub e Streamlit Cloud (Gratuito)

### 1. Subir o código para o GitHub
1. Crie um novo repositório no seu GitHub (ex: `sitipet-app`).
2. No terminal da pasta do projeto, execute:
```bash
git init
git add .
git commit -m "Versao inicial do SitiPet App"
git branch -M main
git remote add origin https://github.com/SEU_USUARIO/sitipet-app.git
git push -u origin main
```

### 2. Publicar no Streamlit Cloud
1. Acesse [share.streamlit.io](https://share.streamlit.io) e faça login com sua conta do GitHub.
2. Clique em **"New app"**.
3. Selecione o repositório `SEU_USUARIO/sitipet-app`, Branch `main` e Main file path `app.py`.
4. Clique em **"Deploy"**.

---

## 🔒 Como Conectar com o Google Sheets (`sitipet01@gmail.com`)

1. **Ativar APIs no Google Cloud Console:**
   - Acesse [console.cloud.google.com](https://console.cloud.google.com).
   - Crie um projeto (ex: `SitiPet`).
   - Ative a **Google Sheets API** e a **Google Drive API**.
2. **Criar Chave da Conta de Serviço (Service Account):**
   - Vá em **IAM e administração > Contas de serviço > Criar conta de serviço**.
   - Crie uma chave no formato **JSON** e baixe o arquivo.
3. **Criar a Planilha no Google Drive:**
   - No Google Drive da conta `sitipet01@gmail.com`, crie uma planilha chamada `SITIPET - Gestão`.
   - Compartilhe a planilha com o e-mail da conta de serviço (ex: `sitipet-bot@projeto.iam.gserviceaccount.com`) com permissão de **Editor**.
4. **Configurar os Secrets no Streamlit Cloud:**
   - No painel do app no Streamlit Cloud, acesse **Settings > Secrets**.
   - Cole as credenciais conforme o modelo contido em `.streamlit/secrets.toml.template`.

---

## 📁 Estrutura de Diretórios

```
sitipet-app/
│
├── app.py                      # Arquivo principal do Streamlit
├── requirements.txt            # Dependências Python
├── README.md                   # Documentação do sistema
│
├── assets/
│   └── logo.png                # Logotipo oficial SitiPet
│
├── utils/
│   ├── storage.py              # Camada de dados (Google Sheets + JSON Local)
│   ├── financeiro.py           # Cálculos, métricas e gráficos Plotly
│   └── datas.py                # Formatações de datas e alertas de horários
│
├── views/
│   ├── dashboard_view.py       # Indicadores rápidos e alertas
│   ├── agenda_view.py          # Aba 1: Agenda Diária
│   ├── banho_tosa_view.py      # Aba 2: Banho e Tosa
│   ├── hospedagem_view.py      # Aba 3: Hotelzinho
│   ├── caixa_view.py           # Aba 4: Caixa e Finanças
│   └── config_view.py          # Aba 5: Configurações e Backup
│
├── data/
│   └── sitipet_db.json         # Base de dados local (modo offline/fallback)
│
└── .streamlit/
    ├── config.toml             # Configurações de tema visual
    └── secrets.toml.template   # Modelo de credenciais do Google
```
