"""
Módulo de Armazenamento Híbrido - SitiPet
Gerencia persistência no Google Sheets (para produção / Streamlit Cloud) 
e armazenamento local em JSON (modo offline/fallback e testes rápidos).
"""

import os
import json
import uuid
import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.datas import get_today_date_str, get_now_time_str

LOCAL_DB_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "data", "sitipet_db.json")

# Tabelas padrão do sistema
TABLES = ["Agenda", "Banho_Tosa", "Hospedagem", "Caixa", "Servicos_Precos"]

# Profissionais fixos da SitiPet
PROFISSIONAIS = ["Silvaneidy (Groomer)", "Silvania"]

# Tabela Oficial de Serviços e Preços por Porte - SitiPet
DEFAULT_SERVICOS = [
    # BANHO
    {"id": "SRV-001", "categoria": "Banho", "nome": "Banho (Pequeno)", "preco_padrao": 50.0, "ativo": True},
    {"id": "SRV-002", "categoria": "Banho", "nome": "Banho (Médio)", "preco_padrao": 70.0, "ativo": True},
    {"id": "SRV-003", "categoria": "Banho", "nome": "Banho (Grande)", "preco_padrao": 100.0, "ativo": True},
    {"id": "SRV-004", "categoria": "Banho", "nome": "Banho (Gigante)", "preco_padrao": 130.0, "ativo": True},
    
    # BANHO E TOSA HIGIÊNICA
    {"id": "SRV-005", "categoria": "Banho e Tosa Higiênica", "nome": "Banho e Tosa Higiênica (Pequeno)", "preco_padrao": 70.0, "ativo": True},
    {"id": "SRV-006", "categoria": "Banho e Tosa Higiênica", "nome": "Banho e Tosa Higiênica (Médio)", "preco_padrao": 90.0, "ativo": True},
    {"id": "SRV-007", "categoria": "Banho e Tosa Higiênica", "nome": "Banho e Tosa Higiênica (Grande)", "preco_padrao": 130.0, "ativo": True},
    {"id": "SRV-008", "categoria": "Banho e Tosa Higiênica", "nome": "Banho e Tosa Higiênica (Gigante)", "preco_padrao": 150.0, "ativo": True},
    
    # BANHO E TOSA COMPLETA - PEQUENO
    {"id": "SRV-009", "categoria": "Tosa Pequeno", "nome": "Tosa Raspada (Pequeno)", "preco_padrao": 80.0, "ativo": True},
    {"id": "SRV-010", "categoria": "Tosa Pequeno", "nome": "Tosa Bebê (Pequeno)", "preco_padrao": 120.0, "ativo": True},
    {"id": "SRV-011", "categoria": "Tosa Pequeno", "nome": "Tosa Tamanho Único (Pequeno)", "preco_padrao": 100.0, "ativo": True},
    
    # BANHO E TOSA COMPLETA - MÉDIO
    {"id": "SRV-012", "categoria": "Tosa Médio", "nome": "Tosa Raspada (Médio)", "preco_padrao": 100.0, "ativo": True},
    {"id": "SRV-013", "categoria": "Tosa Médio", "nome": "Tosa Bebê (Médio)", "preco_padrao": 150.0, "ativo": True},
    {"id": "SRV-014", "categoria": "Tosa Médio", "nome": "Tosa Tamanho Único (Médio)", "preco_padrao": 130.0, "ativo": True},
    
    # BANHO E TOSA COMPLETA - GRANDE
    {"id": "SRV-015", "categoria": "Tosa Grande", "nome": "Tosa Raspada (Grande)", "preco_padrao": 130.0, "ativo": True},
    {"id": "SRV-016", "categoria": "Tosa Grande", "nome": "Tosa Bebê (Grande)", "preco_padrao": 180.0, "ativo": True},
    {"id": "SRV-017", "categoria": "Tosa Grande", "nome": "Tosa Tamanho Único (Grande)", "preco_padrao": 150.0, "ativo": True},
    
    # CUIDADOS E ADICIONAIS
    {"id": "SRV-018", "categoria": "Adicionais", "nome": "Corte de unhas", "preco_padrao": 10.0, "ativo": True},
    {"id": "SRV-019", "categoria": "Adicionais", "nome": "Higienização de ouvidos", "preco_padrao": 10.0, "ativo": True},
    {"id": "SRV-020", "categoria": "Adicionais", "nome": "Higienização de boca", "preco_padrao": 10.0, "ativo": True},
    
    # HOTELZINHO
    {"id": "SRV-021", "categoria": "Hotel", "nome": "Diária Hotelzinho", "preco_padrao": 80.0, "ativo": True},
]

def get_initial_sample_data() -> dict:
    """Gera dados iniciais de demonstração realistas para teste imediato."""
    hoje = get_today_date_str()
    return {
        "Agenda": [
            {
                "id": "AGD-101",
                "data": hoje,
                "horario": "09:00",
                "pet_nome": "Thor",
                "raca": "Shih-tzu",
                "porte": "Pequeno",
                "tutor_nome": "Mariana Silva",
                "tutor_telefone": "(11) 98765-4321",
                "servicos": "Banho e Tosa Higiênica (Pequeno)",
                "valor_total": 70.0,
                "profissional": "Silvaneidy (Groomer)",
                "status": "Finalizado",
                "observacoes": "Pet calmo e dócil",
                "criado_em": hoje
            },
            {
                "id": "AGD-102",
                "data": hoje,
                "horario": "14:00",
                "pet_nome": "Pipoca",
                "raca": "Poodle",
                "porte": "Médio",
                "tutor_nome": "Lucas Ferreira",
                "tutor_telefone": "(11) 97654-3210",
                "servicos": "Tosa Bebê (Médio) + Corte de unhas",
                "valor_total": 160.0,
                "profissional": "Silvania",
                "status": "Em atendimento",
                "observacoes": "Usar shampoo neutro",
                "criado_em": hoje
            }
        ],
        "Banho_Tosa": [
            {
                "id": "BT-201",
                "data": hoje,
                "horario": "09:00",
                "pet_nome": "Thor",
                "tutor_nome": "Mariana Silva",
                "tutor_telefone": "(11) 98765-4321",
                "raca": "Shih-tzu",
                "porte": "Pequeno",
                "profissional": "Silvaneidy (Groomer)",
                "servicos_detalhados": "Banho e Tosa Higiênica (Pequeno) (R$ 70,00)",
                "valor_total": 70.0,
                "status_pagamento": "Pago (Pix)",
                "lembrete_dias": 15,
                "data_proximo_banho": hoje,
                "lembrete_status": "Pendente",
                "observacoes": "Pelagem escovada",
                "criado_em": hoje
            }
        ],
        "Hospedagem": [
            {
                "id": "HSP-301",
                "pet_nome": "Bob",
                "tutor_nome": "Roberto Mendes",
                "tutor_telefone": "(11) 91234-5678",
                "data_entrada": hoje,
                "data_saida": hoje,
                "diarias": 2,
                "valor_diaria": 80.0,
                "valor_total": 160.0,
                "forma_pagamento": "Pix",
                "status": "Hospedado",
                "alimentacao": "Ração Premier Adulto Raças Médias",
                "refeicoes_dia": "2x ao dia (08h e 18h)",
                "medicacao": "Nenhuma medicação contínua",
                "comportamento": "Sociável com outros cães, adora brincar",
                "restricoes": "Não oferecer petiscos de frango",
                "contato_emergencia": "Esposa Carla: (11) 91111-2222",
                "observacoes": "Trouxe caminha e 2 brinquedos",
                "criado_em": hoje
            }
        ],
        "Caixa": [
            {
                "id": "CX-401",
                "data": hoje,
                "tipo": "Entrada",
                "categoria": "Banho e Tosa",
                "servico_relacionado": "Banho e Tosa",
                "descricao": "Atendimento Thor - Mariana Silva",
                "valor": 70.0,
                "forma_pagamento": "Pix",
                "referencia_id": "AGD-101",
                "observacao": "Finalizado via Agenda",
                "criado_em": hoje
            },
            {
                "id": "CX-402",
                "data": hoje,
                "tipo": "Entrada",
                "categoria": "Hospedagem",
                "servico_relacionado": "Hospedagem",
                "descricao": "Hospedagem Bob (2 diárias) - Roberto Mendes",
                "valor": 160.0,
                "forma_pagamento": "Pix",
                "referencia_id": "HSP-301",
                "observacao": "Entrada hotel",
                "criado_em": hoje
            }
        ],
        "Servicos_Precos": DEFAULT_SERVICOS
    }

def get_google_sheets_client():
    """Tenta autenticar com Google Sheets via st.secrets."""
    try:
        import gspread
        from google.oauth2.service_account import Credentials

        if "gcp_service_account" not in st.secrets:
            return None, "Chave 'gcp_service_account' não configurada nos Secrets do Streamlit."

        scopes = [
            "https://www.googleapis.com/auth/spreadsheets",
            "https://www.googleapis.com/auth/drive"
        ]
        
        credentials_dict = dict(st.secrets["gcp_service_account"])
        credentials = Credentials.from_service_account_info(credentials_dict, scopes=scopes)
        client = gspread.authorize(credentials)
        return client, None
    except Exception as e:
        return None, str(e)

def get_spreadsheet():
    """Obtém ou cria a planilha no Google Sheets."""
    client, err = get_google_sheets_client()
    if not client:
        return None, err
    
    sheet_name = st.secrets.get("spreadsheet_name", "SITIPET - Gestão")
    try:
        spreadsheet = client.open(sheet_name)
        return spreadsheet, None
    except Exception:
        try:
            spreadsheet = client.create(sheet_name)
            target_email = st.secrets.get("google_account_email", "siti.pet01@gmail.com")
            spreadsheet.share(target_email, perm_type="user", role="writer")
            return spreadsheet, None
        except Exception as e:
            return None, str(e)

def get_storage_status() -> dict:
    """Verifica se o sistema está conectado ao Google Sheets ou usando Armazenamento Local."""
    client, err = get_google_sheets_client()
    if client:
        sh, sh_err = get_spreadsheet()
        if sh:
            return {
                "is_google_sheets": True,
                "sheet_name": sh.title,
                "account": st.secrets.get("google_account_email", "siti.pet01@gmail.com"),
                "status_label": "🟢 Conectado ao Google Sheets (Nuvem Ativa)",
                "error": None
            }
        else:
            return {
                "is_google_sheets": False,
                "sheet_name": None,
                "account": st.secrets.get("google_account_email", "siti.pet01@gmail.com"),
                "status_label": "🟠 Modo Local Ativo (Compartilhe a planilha no Drive)",
                "error": sh_err
            }
    return {
        "is_google_sheets": False,
        "sheet_name": None,
        "account": "siti.pet01@gmail.com",
        "status_label": "🔵 Modo Local Ativo (Dados salvos com segurança)",
        "error": err
    }

# ==================== CARREGAMENTO E PERSISTÊNCIA ====================

def _load_local_db() -> dict:
    """Lê a base de dados JSON local ou inicializa caso não exista."""
    if not os.path.exists(LOCAL_DB_PATH):
        os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
        data = get_initial_sample_data()
        with open(LOCAL_DB_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        return data
    
    try:
        with open(LOCAL_DB_PATH, "r", encoding="utf-8") as f:
            db = json.load(f)
            if "Servicos_Precos" not in db or len(db.get("Servicos_Precos", [])) < 15:
                db["Servicos_Precos"] = DEFAULT_SERVICOS
                _save_local_db(db)
            return db
    except Exception:
        data = get_initial_sample_data()
        return data

def _save_local_db(db: dict):
    """Salva a base de dados no arquivo JSON local."""
    os.makedirs(os.path.dirname(LOCAL_DB_PATH), exist_ok=True)
    with open(LOCAL_DB_PATH, "w", encoding="utf-8") as f:
        json.dump(db, f, ensure_ascii=False, indent=2)

def load_table(table_name: str) -> pd.DataFrame:
    """Carrega uma tabela do Google Sheets ou do Local DB."""
    client, _ = get_google_sheets_client()
    if client:
        spreadsheet, _ = get_spreadsheet()
        if spreadsheet:
            try:
                try:
                    worksheet = spreadsheet.worksheet(table_name)
                except Exception:
                    worksheet = spreadsheet.add_worksheet(title=table_name, rows="500", cols="25")
                    db_local = _load_local_db()
                    initial_rows = db_local.get(table_name, [])
                    if initial_rows:
                        df_init = pd.DataFrame(initial_rows)
                        worksheet.update([df_init.columns.values.tolist()] + df_init.astype(str).values.tolist())
                        return df_init
                    return pd.DataFrame()
                
                records = worksheet.get_all_records()
                return pd.DataFrame(records)
            except Exception:
                pass

    db = _load_local_db()
    rows = db.get(table_name, [])
    return pd.DataFrame(rows)

def save_table(table_name: str, df: pd.DataFrame):
    """Salva o DataFrame completo na tabela (Google Sheets e Local)."""
    db = _load_local_db()
    df_clean = df.fillna("")
    db[table_name] = df_clean.to_dict(orient="records")
    _save_local_db(db)

    client, _ = get_google_sheets_client()
    if client:
        spreadsheet, _ = get_spreadsheet()
        if spreadsheet:
            try:
                try:
                    worksheet = spreadsheet.worksheet(table_name)
                except Exception:
                    worksheet = spreadsheet.add_worksheet(title=table_name, rows="500", cols="25")
                
                worksheet.clear()
                if not df_clean.empty:
                    data_to_write = [df_clean.columns.values.tolist()] + df_clean.astype(str).values.tolist()
                    worksheet.update(data_to_write)
            except Exception as e:
                print(f"Aviso ao sincronizar com Google Sheets: {e}")

def insert_record(table_name: str, record: dict) -> str:
    """Insere um novo registro na tabela."""
    df = load_table(table_name)
    if "id" not in record or not record["id"]:
        prefix = table_name[:3].upper()
        record["id"] = f"{prefix}-{str(uuid.uuid4())[:6].upper()}"
    
    if "criado_em" not in record or not record["criado_em"]:
        record["criado_em"] = get_today_date_str()

    df_novo = pd.DataFrame([record])
    if df.empty:
        df_result = df_novo
    else:
        df_result = pd.concat([df, df_novo], ignore_index=True)
    
    save_table(table_name, df_result)
    return record["id"]

def update_record(table_name: str, record_id: str, new_values: dict) -> bool:
    """Atualiza um registro existente pelo seu ID."""
    df = load_table(table_name)
    if df.empty or "id" not in df.columns:
        return False
    
    idx = df[df["id"].astype(str) == str(record_id)].index
    if len(idx) == 0:
        return False
    
    for key, val in new_values.items():
        df.loc[idx[0], key] = val
    
    if "atualizado_em" in df.columns:
        df.loc[idx[0], "atualizado_em"] = get_today_date_str()
        
    save_table(table_name, df)
    return True

def delete_record(table_name: str, record_id: str) -> bool:
    """Remove um registro da tabela pelo seu ID."""
    df = load_table(table_name)
    if df.empty or "id" not in df.columns:
        return False
    
    df_filtrado = df[df["id"].astype(str) != str(record_id)].copy()
    save_table(table_name, df_filtrado)
    return True

# ==================== FLUXOS INTEGRADOS AUTOMÁTICOS COM O CAIXA ====================

def lancar_ou_atualizar_hospedagem_caixa(
    hospedagem_id: str,
    valor: float,
    forma_pagamento: str,
    descricao: str,
    data_lancamento: str = None,
    observacao: str = ""
) -> str:
    """
    Garante que a hospedagem seja contabilizada corretamente no Caixa:
    - Se já existir lançamento vinculado a essa hospedagem (referencia_id == hospedagem_id), atualiza o valor e forma de pagamento.
    - Se não existir, cria uma nova Entrada financeira no Caixa.
    """
    df_caixa = load_table("Caixa")
    dt = data_lancamento or get_today_date_str()
    val_num = float(valor) if valor is not None else 0.0

    if not df_caixa.empty and "referencia_id" in df_caixa.columns:
        match = df_caixa[df_caixa["referencia_id"].astype(str) == str(hospedagem_id)]
        if not match.empty:
            cx_id = match.iloc[0]["id"]
            update_record("Caixa", cx_id, {
                "valor": val_num,
                "forma_pagamento": forma_pagamento,
                "descricao": descricao,
                "data": dt,
                "observacao": observacao
            })
            return str(cx_id)

    # Não existe no Caixa ainda -> Criar nova entrada
    novo_cx_id = f"CX-{str(uuid.uuid4())[:6].upper()}"
    novo_cx = {
        "id": novo_cx_id,
        "data": dt,
        "tipo": "Entrada",
        "categoria": "Hospedagem",
        "servico_relacionado": "Hospedagem",
        "descricao": descricao,
        "valor": val_num,
        "forma_pagamento": forma_pagamento,
        "referencia_id": str(hospedagem_id),
        "observacao": observacao,
        "criado_em": get_today_date_str()
    }
    insert_record("Caixa", novo_cx)
    return novo_cx_id

def verificar_hospedagem_no_caixa(hospedagem_id: str) -> dict:
    """Verifica se a hospedagem já foi lançada no Caixa e retorna os detalhes."""
    df_caixa = load_table("Caixa")
    if not df_caixa.empty and "referencia_id" in df_caixa.columns:
        match = df_caixa[df_caixa["referencia_id"].astype(str) == str(hospedagem_id)]
        if not match.empty:
            item = match.iloc[0]
            return {
                "lancado": True,
                "caixa_id": item.get("id"),
                "valor": float(item.get("valor", 0.0)),
                "forma_pagamento": item.get("forma_pagamento")
            }
    return {"lancado": False, "caixa_id": None, "valor": 0.0, "forma_pagamento": ""}

def excluir_hospedagem_e_caixa(hospedagem_id: str, excluir_tambem_caixa: bool = True):
    """Exclui a hospedagem e opcionalmente o lançamento vinculado no Caixa."""
    delete_record("Hospedagem", hospedagem_id)
    if excluir_tambem_caixa:
        df_caixa = load_table("Caixa")
        if not df_caixa.empty and "referencia_id" in df_caixa.columns:
            match = df_caixa[df_caixa["referencia_id"].astype(str) == str(hospedagem_id)]
            for _, r in match.iterrows():
                delete_record("Caixa", r.get("id"))

def concluir_atendimento_agenda(
    agenda_id: str,
    forma_pagamento: str = "Pix",
    criar_registro_banho_tosa: bool = True,
    criar_registro_caixa: bool = True
) -> bool:
    """Fluxo Integrado 1: Conclui agenda, registra em Banho/Tosa e lança no Caixa."""
    df_agenda = load_table("Agenda")
    if df_agenda.empty:
        return False
    
    reg_list = df_agenda[df_agenda["id"].astype(str) == str(agenda_id)].to_dict(orient="records")
    if not reg_list:
        return False
    
    item = reg_list[0]
    update_record("Agenda", agenda_id, {"status": "Finalizado"})
    
    if criar_registro_banho_tosa:
        bt_record = {
            "id": f"BT-{str(uuid.uuid4())[:6].upper()}",
            "data": item.get("data", get_today_date_str()),
            "horario": item.get("horario", get_now_time_str()),
            "pet_nome": item.get("pet_nome", ""),
            "tutor_nome": item.get("tutor_nome", ""),
            "tutor_telefone": item.get("tutor_telefone", ""),
            "raca": item.get("raca", "Não informada"),
            "porte": item.get("porte", "Pequeno"),
            "profissional": item.get("profissional", "Silvaneidy (Groomer)"),
            "servicos_detalhados": item.get("servicos", "Banho e Tosa"),
            "valor_total": float(item.get("valor_total", 0.0)),
            "status_pagamento": f"Pago ({forma_pagamento})",
            "lembrete_dias": 15,
            "data_proximo_banho": get_today_date_str(),
            "lembrete_status": "Pendente",
            "observacoes": f"Finalizado da Agenda. Obs: {item.get('observacoes', '')}",
            "criado_em": get_today_date_str()
        }
        insert_record("Banho_Tosa", bt_record)

    if criar_registro_caixa:
        valor = float(item.get("valor_total", 0.0))
        if valor > 0:
            cx_record = {
                "id": f"CX-{str(uuid.uuid4())[:6].upper()}",
                "data": get_today_date_str(),
                "tipo": "Entrada",
                "categoria": "Banho e Tosa",
                "servico_relacionado": "Banho e Tosa",
                "descricao": f"Atendimento {item.get('pet_nome', '')} - Tutor(a) {item.get('tutor_nome', '')}",
                "valor": valor,
                "forma_pagamento": forma_pagamento,
                "referencia_id": str(agenda_id),
                "observacao": f"Serviços: {item.get('servicos', '')} | Profissional: {item.get('profissional', '')}",
                "criado_em": get_today_date_str()
            }
            insert_record("Caixa", cx_record)
            
    return True

def concluir_hospedagem(
    hospedagem_id: str,
    forma_pagamento: str = "Pix",
    valor_adicionais: float = 0.0,
    criar_registro_caixa: bool = True
) -> bool:
    """Fluxo Integrado 2: Realiza check-out do pet na Hospedagem e atualiza/lança no Caixa."""
    df_hosp = load_table("Hospedagem")
    if df_hosp.empty:
        return False
    
    reg_list = df_hosp[df_hosp["id"].astype(str) == str(hospedagem_id)].to_dict(orient="records")
    if not reg_list:
        return False
    
    item = reg_list[0]
    valor_base = float(item.get("valor_total", 0.0))
    valor_final = valor_base + float(valor_adicionais)

    # 1. Atualizar Hospedagem
    update_record("Hospedagem", hospedagem_id, {
        "status": "Concluído",
        "valor_total": float(valor_final),
        "data_saida_real": get_today_date_str(),
        "forma_pagamento": forma_pagamento
    })
    
    # 2. Lançar / Atualizar no Caixa
    if criar_registro_caixa and valor_final > 0:
        desc = f"Check-out Hotel {item.get('pet_nome', '')} ({item.get('diarias', 1)} diárias) - Tutor: {item.get('tutor_nome', '')}"
        obs = f"Entrada: {item.get('data_entrada')} | Saída: {item.get('data_saida')}"
        if valor_adicionais > 0:
            obs += f" | Adicionais: {formatar_moeda(valor_adicionais)}"
        lancar_ou_atualizar_hospedagem_caixa(hospedagem_id, valor_final, forma_pagamento, desc, observacao=obs)
            
    return True
