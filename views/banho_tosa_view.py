"""
Visão: Aba 2 – Banho e Tosa - SitiPet
Cadastro e gerenciamento completo dos serviços de banho, tosa e adicionais com cálculo automático.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
from utils.storage import load_table, insert_record, delete_record
from utils.datas import get_today_date, get_today_date_str, format_date_br
from utils.financeiro import formatar_moeda

TOSAS_PADRAO = [
    ("Tosa raspada", 60.0),
    ("Tosa tamanho único", 70.0),
    ("Tosa bebê", 80.0),
    ("Tosa na tesoura", 90.0),
    ("Tosa higiênica", 35.0),
    ("Tosa da raça", 85.0),
    ("Tosa completa", 95.0),
    ("Aparagem", 40.0),
    ("Desembolo", 30.0),
    ("Outros tipos de tosa", 50.0)
]

BANHOS_ADICIONAIS_PADRAO = [
    ("Banho simples", 50.0),
    ("Banho com hidratação", 75.0),
    ("Banho medicamentoso", 65.0),
    ("Corte de unhas", 15.0),
    ("Limpeza de ouvidos", 15.0),
    ("Escovação de dentes", 15.0),
    ("Hidratação profunda", 30.0),
    ("Desembolo extra", 35.0),
    ("Outros serviços adicionais", 25.0)
]

def render_banho_tosa():
    st.markdown("## ✂️ Aba 2 – Banho e Tosa")
    st.markdown("Cadastre e gerencie atendimentos de estética animal, combinando serviços com valores individuais e cálculo automático.")

    df_bt = load_table("Banho_Tosa")

    # ==================== FORMULÁRIO DE CADASTRO ====================
    with st.expander("➕ **Registrar Novo Atendimento de Banho e Tosa**", expanded=False):
        st.markdown("#### 1. Dados do Animal e Tutor")
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_nome = st.text_input("🐶 Nome do Pet *", key="bt_pet_nome", placeholder="Ex: Bob, Mel, Luna")
            raca = st.text_input("Raça", key="bt_raca", placeholder="Ex: Poodle, Shih-tzu, Golden")
        with col2:
            tutor_nome = st.text_input("👤 Nome do Tutor *", key="bt_tutor_nome", placeholder="Ex: Marcelo Albuquerque")
            tutor_telefone = st.text_input("📱 Telefone / WhatsApp", key="bt_tutor_tel", placeholder="(11) 98888-7777")
        with col3:
            porte = st.selectbox("Porte do Pet", ["Pequeno", "Médio", "Grande", "Gigante"], key="bt_porte")
            profissional = st.selectbox("Profissional Responsável", ["Carlos (Tosa)", "Ana Paula (Banho)", "Mariana", "Outro"], key="bt_prof")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_atend = st.date_input("📅 Data do Atendimento", value=get_today_date(), key="bt_data")
        with col_d2:
            horario_atend = st.time_input("⏰ Horário", value=datetime.now().time(), key="bt_hora")

        st.markdown("---")
        st.markdown("#### 2. Seleção de Serviços & Valores Individuais")
        st.caption("Selecione um ou mais serviços de tosa, banho e adicionais. Os valores podem ser ajustados individualmente.")

        col_tosa, col_banho = st.columns(2)

        servicos_selecionados_com_valores = []

        with col_tosa:
            st.markdown("##### ✂️ Serviços de Tosa")
            for nome_tosa, preco_sug in TOSAS_PADRAO:
                col_chk, col_val = st.columns([3, 2])
                with col_chk:
                    sel = st.checkbox(nome_tosa, key=f"chk_tosa_{nome_tosa}")
                with col_val:
                    if sel:
                        v = st.number_input(f"R$ ({nome_tosa})", min_value=0.0, value=float(preco_sug), step=5.0, key=f"val_tosa_{nome_tosa}", label_visibility="collapsed")
                        servicos_selecionados_com_valores.append((nome_tosa, v))

        with col_banho:
            st.markdown("##### 🛁 Banho e Cuidados Adicionais")
            for nome_banho, preco_sug in BANHOS_ADICIONAIS_PADRAO:
                col_chk, col_val = st.columns([3, 2])
                with col_chk:
                    sel = st.checkbox(nome_banho, key=f"chk_banho_{nome_banho}")
                with col_val:
                    if sel:
                        v = st.number_input(f"R$ ({nome_banho})", min_value=0.0, value=float(preco_sug), step=5.0, key=f"val_banho_{nome_banho}", label_visibility="collapsed")
                        servicos_selecionados_com_valores.append((nome_banho, v))

        # Cálculo Total
        valor_total_calculado = sum(v for _, v in servicos_selecionados_com_valores)

        st.markdown("---")
        st.markdown("#### 3. Totalização e Pagamento")
        col_tot1, col_tot2, col_tot3 = st.columns([2, 2, 2])

        with col_tot1:
            st.markdown(f"""
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 10px; padding: 10px 16px; text-align: center;">
                    <span style="font-size: 13px; color: #15803d; font-weight: 600;">VALOR TOTAL CALCULADO</span>
                    <h3 style="margin: 2px 0; color: #166534;">{formatar_moeda(valor_total_calculado)}</h3>
                </div>
            """, unsafe_allow_html=True)

        with col_tot2:
            forma_pag = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pendente"], key="bt_formapag")
        
        with col_tot3:
            lancar_caixa = st.checkbox("💰 Lançar automaticamente no Caixa", value=True, help="Se marcado, cria o registro de entrada financeira imediatamente.")

        observacoes = st.text_area("📝 Observações do Atendimento", placeholder="Ex: Pet apresentou nós nas orelhas, necessitou desembolo cuidadoso...", key="bt_obs")

        if st.button("💾 Salvar Atendimento em Banho e Tosa", type="primary", use_container_width=True):
            if not pet_nome or not tutor_nome:
                st.error("Por favor, preencha os campos obrigatórios (Nome do Pet e Nome do Tutor).")
            elif not servicos_selecionados_com_valores:
                st.error("Por favor, selecione pelo menos 1 serviço de banho ou tosa.")
            else:
                desc_servicos = ", ".join([f"{n} ({formatar_moeda(v)})" for n, v in servicos_selecionados_com_valores])
                rec_id = f"BT-{str(uuid.uuid4())[:6].upper()}"
                
                novo_reg = {
                    "id": rec_id,
                    "data": data_atend.strftime("%Y-%m-%d"),
                    "horario": horario_atend.strftime("%H:%M"),
                    "pet_nome": pet_nome.strip(),
                    "tutor_nome": tutor_nome.strip(),
                    "tutor_telefone": tutor_telefone.strip(),
                    "raca": raca.strip() if raca else "SRD",
                    "porte": porte,
                    "profissional": profissional,
                    "servicos_detalhados": desc_servicos,
                    "valor_total": float(valor_total_calculado),
                    "status_pagamento": f"Pago ({forma_pag})" if forma_pag != "Pendente" else "Pendente",
                    "observacoes": observacoes.strip(),
                    "criado_em": get_today_date_str()
                }
                
                insert_record("Banho_Tosa", novo_reg)

                if lancar_caixa and valor_total_calculado > 0 and forma_pag != "Pendente":
                    cx_reg = {
                        "id": f"CX-{str(uuid.uuid4())[:6].upper()}",
                        "data": data_atend.strftime("%Y-%m-%d"),
                        "tipo": "Entrada",
                        "categoria": "Banho e Tosa",
                        "servico_relacionado": "Banho e Tosa",
                        "descricao": f"Banho/Tosa {pet_nome.strip()} - {tutor_nome.strip()}",
                        "valor": float(valor_total_calculado),
                        "forma_pagamento": forma_pag,
                        "referencia_id": rec_id,
                        "observacao": desc_servicos,
                        "criado_em": get_today_date_str()
                    }
                    insert_record("Caixa", cx_reg)

                st.success(f"✅ Atendimento de **{pet_nome}** registrado com sucesso! Total: **{formatar_moeda(valor_total_calculado)}**.")
                st.rerun()

    # ==================== HISTÓRICO E GESTÃO ====================
    st.markdown("---")
    st.markdown("### 📋 Histórico de Atendimentos Realizados")

    if df_bt.empty:
        st.info("Nenhum registro de banho e tosa encontrado.")
        return

    col_s1, col_s2 = st.columns([3, 2])
    with col_s1:
        busca = st.text_input("🔍 Buscar por Pet, Tutor ou Profissional", placeholder="Digite para filtrar...", key="busca_bt")
    with col_s2:
        filtro_porte = st.selectbox("Filtrar por Porte", ["Todos", "Pequeno", "Médio", "Grande", "Gigante"], key="flt_porte")

    df_filtrado = df_bt.copy()
    if busca:
        busca_lower = busca.lower()
        df_filtrado = df_filtrado[
            df_filtrado["pet_nome"].astype(str).str.lower().str.contains(busca_lower) |
            df_filtrado["tutor_nome"].astype(str).str.lower().str.contains(busca_lower) |
            df_filtrado["profissional"].astype(str).str.lower().str.contains(busca_lower)
        ]
    if filtro_porte != "Todos":
        df_filtrado = df_filtrado[df_filtrado["porte"] == filtro_porte]

    # Ordenar por data decrescente
    df_filtrado = df_filtrado.sort_values(by=["data", "horario"], ascending=[False, False])

    st.caption(f"Mostrando **{len(df_filtrado)}** registro(s)")

    for _, row in df_filtrado.iterrows():
        rec_id = row.get("id")
        pet = row.get("pet_nome")
        tutor = row.get("tutor_nome")
        tel = row.get("tutor_telefone")
        raca = row.get("raca")
        porte = row.get("porte")
        data_s = row.get("data")
        hora_s = row.get("horario")
        prof = row.get("profissional")
        servs = row.get("servicos_detalhados")
        val = float(row.get("valor_total", 0.0))
        status_pag = row.get("status_pagamento", "Pago")
        obs = row.get("observacoes", "")

        with st.container():
            st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-left: 5px solid #d82678;">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 17px; font-weight: 700; color: #1e293b;">🐶 {pet} ({raca} • {porte})</span>
                            <span style="color: #64748b; font-size: 13px;"> | Tutor: <b>{tutor}</b> ({tel})</span>
                        </div>
                        <div>
                            <span style="background: #fdf2f8; color: #d82678; border: 1px solid #fbcfe8; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 14px;">
                                {formatar_moeda(val)}
                            </span>
                        </div>
                    </div>
                    <div style="margin-top: 8px; font-size: 13px; color: #334155;">
                        ✂️ <b>Serviços:</b> {servs} <br>
                        📅 <b>Data:</b> {format_date_br(data_s)} às {hora_s} &nbsp;|&nbsp; 👤 <b>Profissional:</b> {prof} &nbsp;|&nbsp; 💳 <b>Status:</b> {status_pag}
                        {f'<br>📝 <i>Obs: {obs}</i>' if obs else ''}
                    </div>
                </div>
            """, unsafe_allow_html=True)
            
            col_act1, col_act2 = st.columns([5, 1])
            with col_act2:
                if st.button("🗑️ Excluir", key=f"del_bt_{rec_id}", help="Excluir este atendimento"):
                    delete_record("Banho_Tosa", rec_id)
                    st.rerun()
