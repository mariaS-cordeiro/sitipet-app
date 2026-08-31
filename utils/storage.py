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

# Lista padrão de serviços e preços iniciais
DEFAULT_SERVICOS = [
    {"id": "SRV-001", "categoria": "Tosa", "nome": "Tosa raspada", "preco_padrao": 60.0, "ativo": True},
    {"id": "SRV-002", "categoria": "Tosa", "nome": "Tosa tamanho único", "preco_padrao": 70.0, "ativo": True},
    {"id": "SRV-003", "categoria": "Tosa", "nome": "Tosa bebê", "preco_padrao": 80.0, "ativo": True},
    {"id": "SRV-004", "categoria": "Tosa", "nome": "Tosa na tesoura", "preco_padrao": 90.0, "ativo": True},
    {"id": "SRV-005", "categoria": "Tosa", "nome": "Tosa higiênica", "preco_padrao": 35.0, "ativo": True},
    {"id": "SRV-006", "categoria": "Tosa", "nome": "Tosa da raça", "preco_padrao": 85.0, "ativo": True},
    {"id": "SRV-007", "categoria": "Tosa", "nome": "Tosa completa", "preco_padrao": 95.0, "ativo": True},
    {"id": "SRV-008", "categoria": "Tosa", "nome": "Aparagem", "preco_padrao": 40.0, "ativo": True},
    {"id": "SRV-009", "categoria": "Tosa", "nome": "Desembolo", "preco_padrao": 30.0, "ativo": True},
    {"id": "SRV-010", "categoria": "Tosa", "nome": "Outros tipos de tosa", "preco_padrao": 50.0, "ativo": True},
    {"id": "SRV-011", "categoria": "Banho", "nome": "Banho simples", "preco_padrao": 50.0, "ativo": True},
    {"id": "SRV-012", "categoria": "Banho", "nome": "Banho com hidratação", "preco_padrao": 75.0, "ativo": True},
    {"id": "SRV-013", "categoria": "Banho", "nome": "Banho medicamentoso", "preco_padrao": 65.0, "ativo": True},
    {"id": "SRV-014", "categoria": "Adicionais", "nome": "Corte de unhas", "preco_padrao": 15.0, "ativo": True},
    {"id": "SRV-015", "categoria": "Adicionais", "nome": "Limpeza de ouvidos", "preco_padrao": 15.0, "ativo": True},
    {"id": "SRV-016", "categoria": "Adicionais", "nome": "Escovação de dentes", "preco_padrao": 15.0, "ativo": True},
    {"id": "SRV-017", "categoria": "Adicionais", "nome": "Hidratação profunda", "preco_padrao": 30.0, "ativo": True},
    {"id": "SRV-018", "categoria": "Hotel", "nome": "Diária Hotelzinho", "preco_padrao": 80.0, "ativo": True},
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
                "tutor_nome": "Mariana Silva",
                "tutor_telefone": "(11) 98765-4321",
                "servicos": "Banho simples + Tosa higiênica",
                "valor_total": 85.0,
                "profissional": "Carlos (Tosa)",
                "status": "Finalizado",
                "observacoes": "Pet calmo e dócil",
                "criado_em": hoje
            },
            {
                "id": "AGD-102",
                "data": hoje,
                "horario": "14:00",
                "pet_nome": "Pipoca",
                "tutor_nome": "Lucas Ferreira",
                "tutor_telefone": "(11) 97654-3210",
                "servicos": "Banho com hidratação + Tosa bebê",
                "valor_total": 155.0,
                "profissional": "Ana Paula",
                "status": "Em atendimento",
                "observacoes": "Usar shampoo hipoalergênico",
                "criado_em": hoje
            },
            {
                "id": "AGD-103",
                "data": hoje,
                "horario": "16:30",
                "pet_nome": "Mel",
                "tutor_nome": "Beatriz Souza",
                "tutor_telefone": "(11) 99123-4567",
                "servicos": "Banho simples + Corte de unhas",
                "valor_total": 65.0,
                "profissional": "Carlos (Tosa)",
                "status": "Confirmado",
                "observacoes": "Tutor trará guia própria",
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
                "raca": "Golden Retriever",
                "porte": "Grande",
                "profissional": "Carlos (Tosa)",
                "servicos_detalhados": "Banho simples (R$ 50,00), Tosa higiênica (R$ 35,00)",
                "valor_total": 85.0,
                "status_pagamento": "Pago (Pix)",
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
                "diarias": 3,
                "valor_diaria": 80.0,
                "valor_total": 240.0,
                "forma_pagamento": "Cartão de Crédito",
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
                "valor": 85.0,
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
                "descricao": "Hospedagem Bob (3 diárias) - Roberto Mendes",
                "valor": 240.0,
                "forma_pagamento": "Cartão de Crédito",
                "referencia_id": "HSP-301",
                "observacao": "Entrada hotel",
                "criado_em": hoje
            },
            {
                "id": "CX-403",
                "data": hoje,
                "tipo": "Saída",
                "categoria": "Produtos e Materiais",
                "servico_relacionado": "Banho e Tosa",
                "descricao": "Shampoo Neutro 5L e Condicionador",
                "valor": 95.0,
                "forma_pagamento": "Pix",
                "referencia_id": "",
                "observacao": "Distribuidora PetClean",
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
            return None, "Chave 'gcp_service_account' não encontrada nos Secrets do Streamlit."

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
            # Tentar criar a planilha e compartilhar com sitipet01@gmail.com
            spreadsheet = client.create(sheet_name)
            target_email = st.secrets.get("google_account_email", "sitipet01@gmail.com")
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
                "account": st.secrets.get("google_account_email", "sitipet01@gmail.com"),
                "status_label": "🟢 Conectado ao Google Sheets",
                "error": None
            }
        else:
            return {
                "is_google_sheets": False,
                "sheet_name": None,
                "account": st.secrets.get("google_account_email", "sitipet01@gmail.com"),
                "status_label": "🟠 Modo Local Ativo (Erro ao abrir planilha)",
                "error": sh_err
            }
    return {
        "is_google_sheets": False,
        "sheet_name": None,
        "account": "sitipet01@gmail.com",
        "status_label": "🔵 Modo Local / Fallback Ativo (Pronto para Uso)",
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
            return json.load(f)
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
    # Tentar via Google Sheets se disponível
    client, _ = get_google_sheets_client()
    if client:
        spreadsheet, _ = get_spreadsheet()
        if spreadsheet:
            try:
                try:
                    worksheet = spreadsheet.worksheet(table_name)
                except Exception:
                    # Criar aba se não existir
                    worksheet = spreadsheet.add_worksheet(title=table_name, rows="500", cols="20")
                    db_local = _load_local_db()
                    initial_rows = db_local.get(table_name, [])
                    if initial_rows:
                        df_init = pd.DataFrame(initial_rows)
                        worksheet.update([df_init.columns.values.tolist()] + df_init.values.tolist())
                        return df_init
                    return pd.DataFrame()
                
                records = worksheet.get_all_records()
                return pd.DataFrame(records)
            except Exception:
                pass # Em caso de erro na conexão, faz fallback para local

    # Fallback Local
    db = _load_local_db()
    rows = db.get(table_name, [])
    return pd.DataFrame(rows)

def save_table(table_name: str, df: pd.DataFrame):
    """Salva o DataFrame completo na tabela (Google Sheets e Local)."""
    # 1. Salvar no Local DB
    db = _load_local_db()
    # Limpar NaN para compatibilidade JSON
    df_clean = df.fillna("")
    db[table_name] = df_clean.to_dict(orient="records")
    _save_local_db(db)

    # 2. Salvar no Google Sheets se conectado
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

# ==================== FLUXOS INTEGRADOS AUTOMÁTICOS ====================

def concluir_atendimento_agenda(
    agenda_id: str,
    forma_pagamento: str = "Pix",
    criar_registro_banho_tosa: bool = True,
    criar_registro_caixa: bool = True
) -> bool:
    """
    Fluxo Integrado 1:
    - Marca o agendamento como 'Finalizado' na Agenda
    - Insere no histórico de Banho e Tosa
    - Lança automaticamente a receita no Caixa
    """
    df_agenda = load_table("Agenda")
    if df_agenda.empty:
        return False
    
    reg_list = df_agenda[df_agenda["id"].astype(str) == str(agenda_id)].to_dict(orient="records")
    if not reg_list:
        return False
    
    item = reg_list[0]
    
    # 1. Atualizar Agenda
    update_record("Agenda", agenda_id, {"status": "Finalizado"})
    
    # 2. Inserir em Banho e Tosa se solicitado
    if criar_registro_banho_tosa:
        bt_record = {
            "id": f"BT-{str(uuid.uuid4())[:6].upper()}",
            "data": item.get("data", get_today_date_str()),
            "horario": item.get("horario", get_now_time_str()),
            "pet_nome": item.get("pet_nome", ""),
            "tutor_nome": item.get("tutor_nome", ""),
            "tutor_telefone": item.get("tutor_telefone", ""),
            "raca": item.get("raca", "Não informada"),
            "porte": item.get("porte", "Médio"),
            "profissional": item.get("profissional", "Geral"),
            "servicos_detalhados": item.get("servicos", "Banho e Tosa"),
            "valor_total": float(item.get("valor_total", 0.0)),
            "status_pagamento": f"Pago ({forma_pagamento})",
            "observacoes": f"Finalizado da Agenda. Obs: {item.get('observacoes', '')}",
            "criado_em": get_today_date_str()
        }
        insert_record("Banho_Tosa", bt_record)

    # 3. Inserir no Caixa
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
                "observacao": f"Serviços: {item.get('servicos', '')}",
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
    """
    Fluxo Integrado 2:
    - Realiza check-out do pet na Hospedagem (muda status para 'Concluído')
    - Lança o valor total (diárias + adicionais) no Caixa
    """
    df_hosp = load_table("Hospedagem")
    if df_hosp.empty:
        return False
    
    reg_list = df_hosp[df_hosp["id"].astype(str) == str(hospedagem_id)].to_dict(orient="records")
    if not reg_list:
        return False
    
    item = reg_list[0]
    
    # 1. Atualizar Hospedagem
    update_record("Hospedagem", hospedagem_id, {
        "status": "Concluído",
        "data_saida_real": get_today_date_str(),
        "forma_pagamento": forma_pagamento
    })
    
    # 2. Inserir no Caixa
    if criar_registro_caixa:
        valor_base = float(item.get("valor_total", 0.0))
        valor_final = valor_base + float(valor_adicionais)
        
        if valor_final > 0:
            cx_record = {
                "id": f"CX-{str(uuid.uuid4())[:6].upper()}",
                "data": get_today_date_str(),
                "tipo": "Entrada",
                "categoria": "Hospedagem",
                "servico_relacionado": "Hospedagem",
                "descricao": f"Check-out Hotel {item.get('pet_nome', '')} ({item.get('diarias', 1)} diárias) - Tutor(a) {item.get('tutor_nome', '')}",
                "valor": valor_final,
                "forma_pagamento": forma_pagamento,
                "referencia_id": str(hospedagem_id),
                "observacao": f"Entrada: {item.get('data_entrada')} | Saída: {item.get('data_saida')}",
                "criado_em": get_today_date_str()
            }
            insert_record("Caixa", cx_record)
            
    return True
