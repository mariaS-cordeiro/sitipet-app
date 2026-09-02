"""
Visão: Configurações & Google Sheets - SitiPet
Gerenciamento de conexão com o Google Drive/Sheets (siti.pet01@gmail.com), edição de tabela de preços e backup.
"""

import streamlit as st
import pandas as pd
import json
import io
from utils.storage import get_storage_status, load_table, save_table, LOCAL_DB_PATH
from utils.financeiro import formatar_moeda

def render_config():
    st.markdown("## ⚙️ Configurações & Conexão Google Drive / Sheets")
    st.markdown("Gerencie a persistência na nuvem (`siti.pet01@gmail.com`), tabela de preços dos serviços e backups do sistema.")

    status_storage = get_storage_status()

    # ==================== STATUS DA CONEXÃO ====================
    st.markdown("### 📡 Status da Persistência de Dados")
    if status_storage["is_google_sheets"]:
        st.success(f"""
            **{status_storage['status_label']}**  
            - **Planilha Ativa no Google Drive:** `{status_storage['sheet_name']}`  
            - **Conta Vinculada:** `siti.pet01@gmail.com`  
            - Todos os lançamentos, atendimentos e hospedagens estão sendo sincronizados continuamente com o seu Google Sheets na nuvem!
        """)
    else:
        st.info(f"""
            **{status_storage['status_label']}**  
            - O aplicativo está funcionando com persistência local segura (`data/sitipet_db.json`).  
            - Para salvar permanentemente na planilha do **Google Drive (`siti.pet01@gmail.com`)**, siga o passo a passo abaixo.
        """)

    # ==================== GUIA DE INTEGRAÇÃO GOOGLE SHEETS ====================
    with st.expander("📖 **Passo a Passo: Como Conectar com o Google Sheets (siti.pet01@gmail.com)**", expanded=not status_storage["is_google_sheets"]):
        st.markdown("""
        ### Passo a Passo para Ativar a Planilha Google:

        1. **Acesse o Google Cloud Console:**
           - Acesse [console.cloud.google.com](https://console.cloud.google.com) conectado na conta `siti.pet01@gmail.com`.
           - Crie um novo projeto chamado **`SitiPet`**.

        2. **Ative as 2 APIs necessárias:**
           - No menu lateral, vá em **APIs e Serviços > Biblioteca**.
           - Pesquise e clique em **Ativar** para:
             - **Google Sheets API**
             - **Google Drive API**

        3. **Crie a Chave de Serviço (Service Account):**
           - Vá em **IAM e administração > Contas de serviço**.
           - Clique em **Criar conta de serviço** (ex: nome: `sitipet-bot`).
           - Clique em **Concluir**.
           - Clique no e-mail da conta de serviço criada > Vá na aba **Chaves** > **Adicionar chave > Criar nova chave (JSON)**.
           - Um arquivo `.json` será baixado no seu computador com a chave secreta.

        4. **Crie a Planilha no Google Drive:**
           - No seu Google Drive (`siti.pet01@gmail.com`), crie uma nova planilha chamada **`SITIPET - Gestão`**.
           - Clique no botão **Compartilhar** da planilha.
           - Cole o e-mail da conta de serviço (o e-mail que termina em `@...iam.gserviceaccount.com` que você criou no passo 3) e marque como **Editor**.

        5. **Cole nos Secrets do Streamlit Cloud:**
           - No painel do seu app no [share.streamlit.io](https://share.streamlit.io), clique em **Settings > Secrets**.
           - Cole o modelo preenchido com os dados do seu arquivo JSON:
        """)

        st.code("""
spreadsheet_name = "SITIPET - Gestão"
google_account_email = "siti.pet01@gmail.com"

[gcp_service_account]
type = "service_account"
project_id = "seu-projeto-gcp"
private_key_id = "sua-key-id"
private_key = "-----BEGIN PRIVATE KEY-----\\nMIIEvgIBADANBgk...\\n-----END PRIVATE KEY-----\\n"
client_email = "sitipet-bot@seu-projeto-gcp.iam.gserviceaccount.com"
client_id = "1234567890"
auth_uri = "https://accounts.google.com/o/oauth2/auth"
token_uri = "https://oauth2.googleapis.com/token"
auth_provider_x509_cert_url = "https://www.googleapis.com/oauth2/v1/certs"
client_x509_cert_url = "https://www.googleapis.com/robot/v1/metadata/x509/sitipet-bot..."
        """, language="toml")

    # ==================== GERENCIADOR DE TABELA DE PREÇOS ====================
    st.markdown("---")
    st.markdown("### 🏷️ Tabela de Preços Oficial dos Serviços")
    st.caption("Edite os valores padrão caso deseje alterar preços no futuro.")

    df_srv = load_table("Servicos_Precos")
    if not df_srv.empty:
        edited_df = st.data_editor(
            df_srv,
            column_config={
                "id": st.column_config.TextColumn("Código", disabled=True),
                "categoria": st.column_config.SelectboxColumn("Categoria", options=["Banho", "Banho e Tosa Higiênica", "Tosa Pequeno", "Tosa Médio", "Tosa Grande", "Adicionais", "Hotel"]),
                "nome": st.column_config.TextColumn("Nome do Serviço"),
                "preco_padrao": st.column_config.NumberColumn("Preço Padrão (R$)", format="R$ %.2f", min_value=0.0, step=5.0),
                "ativo": st.column_config.CheckboxColumn("Ativo?")
            },
            num_rows="dynamic",
            use_container_width=True,
            key="editor_servicos"
        )

        if st.button("💾 Salvar Alterações na Tabela de Preços", type="primary"):
            save_table("Servicos_Precos", edited_df)
            st.success("✅ Tabela de preços atualizada com sucesso!")
            st.rerun()

    # ==================== BACKUP E DOWNLOAD DOS DADOS ====================
    st.markdown("---")
    st.markdown("### 💾 Backup e Exportação Completa")
    st.caption("Faça o download de todos os dados do sistema em formato JSON ou relatórios Excel.")

    col_bk1, col_bk2 = st.columns(2)

    with col_bk1:
        try:
            with open(LOCAL_DB_PATH, "r", encoding="utf-8") as f:
                json_data = f.read()
            st.download_button(
                "📥 Baixar Backup Geral (JSON)",
                data=json_data,
                file_name="sitipet_backup_completo.json",
                mime="application/json",
                use_container_width=True
            )
        except Exception:
            st.info("Arquivo de banco local não encontrado.")

    with col_bk2:
        excel_buffer = io.BytesIO()
        with pd.ExcelWriter(excel_buffer, engine="openpyxl") as writer:
            for tbl in ["Agenda", "Banho_Tosa", "Hospedagem", "Caixa", "Servicos_Precos"]:
                df_t = load_table(tbl)
                if not df_t.empty:
                    df_t.to_excel(writer, sheet_name=tbl, index=False)
        st.download_button(
            "📊 Baixar Todas as Planilhas (Excel .xlsx)",
            data=excel_buffer.getvalue(),
            file_name="sitipet_dados_completos.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            use_container_width=True
        )
