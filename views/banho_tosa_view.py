"""
Visão: Aba 2 – Banho e Tosa - SitiPet
Cadastro e gerenciamento completo dos serviços de banho, tosa e adicionais com cálculo automático e emissão de notas.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
from utils.storage import load_table, insert_record, delete_record, PROFISSIONAIS
from utils.datas import get_today_date, get_today_date_str, format_date_br
from utils.financeiro import formatar_moeda
from utils.comprovante import renderizar_modal_comprovante

# Preços base por porte
PRECOS_BANHO = {
    "Pequeno": 50.0,
    "Médio": 70.0,
    "Grande": 100.0,
    "Gigante": 130.0
}

PRECOS_BANHO_TOSA_HIGIENICA = {
    "Pequeno": 70.0,
    "Médio": 90.0,
    "Grande": 130.0,
    "Gigante": 150.0
}

PRECOS_TOSA = {
    "Pequeno": [("Tosa raspada", 80.0), ("Tosa bebê", 120.0), ("Tosa tamanho único", 100.0)],
    "Médio": [("Tosa raspada", 100.0), ("Tosa bebê", 150.0), ("Tosa tamanho único", 130.0)],
    "Grande": [("Tosa raspada", 130.0), ("Tosa bebê", 180.0), ("Tosa tamanho único", 150.0)],
    "Gigante": [("Tosa raspada", 160.0), ("Tosa bebê", 210.0), ("Tosa tamanho único", 180.0)]
}

ADICIONAIS = [
    ("Corte de unhas", 10.0),
    ("Higienização de ouvidos", 10.0),
    ("Higienização de boca", 10.0)
]

def render_banho_tosa():
    st.markdown("## ✂️ Aba 2 – Banho e Tosa")
    st.markdown("Cadastre e gerencie atendimentos de estética animal com tabela de preços por porte, cálculo automático e emissão de comprovantes.")

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
            porte = st.selectbox("Porte do Pet *", ["Pequeno", "Médio", "Grande", "Gigante"], key="bt_porte")
            profissional = st.selectbox("Profissional Responsável *", PROFISSIONAIS, key="bt_prof")

        col_d1, col_d2 = st.columns(2)
        with col_d1:
            data_atend = st.date_input("📅 Data do Atendimento", value=get_today_date(), key="bt_data")
        with col_d2:
            horario_atend = st.time_input("⏰ Horário", value=datetime.now().time(), key="bt_hora")

        st.markdown("---")
        st.markdown(f"#### 2. Seleção de Serviços para Porte: **{porte}**")
        st.caption("Os valores são carregados automaticamente de acordo com a tabela oficial de preços da SitiPet.")

        col_banho, col_tosa, col_adic = st.columns(3)

        servicos_selecionados_com_valores = []

        # 1. BANHO & TOSA HIGIÊNICA
        with col_banho:
            st.markdown("##### 🛁 Banhos")
            # Banho Simples
            preco_banho_sug = PRECOS_BANHO.get(porte, 50.0)
            sel_banho = st.checkbox(f"Banho ({formatar_moeda(preco_banho_sug)})", key=f"chk_banho_{porte}")
            if sel_banho:
                val_b = st.number_input(f"Valor Banho (R$)", min_value=0.0, value=float(preco_banho_sug), step=5.0, key=f"val_b_{porte}")
                servicos_selecionados_com_valores.append((f"Banho ({porte})", val_b))

            # Banho e Tosa Higiênica
            preco_bth_sug = PRECOS_BANHO_TOSA_HIGIENICA.get(porte, 70.0)
            sel_bth = st.checkbox(f"Banho e Tosa Higiênica ({formatar_moeda(preco_bth_sug)})", key=f"chk_bth_{porte}")
            if sel_bth:
                val_bth = st.number_input(f"Valor Banho + Tosa Hig. (R$)", min_value=0.0, value=float(preco_bth_sug), step=5.0, key=f"val_bth_{porte}")
                servicos_selecionados_com_valores.append((f"Banho e Tosa Higiênica ({porte})", val_bth))

        # 2. TOSAS COMPLETAS POR PORTE
        with col_tosa:
            st.markdown(f"##### ✂️ Tosas ({porte})")
            lista_tosas = PRECOS_TOSA.get(porte, PRECOS_TOSA["Pequeno"])
            for nome_tosa, preco_sug in lista_tosas:
                sel_t = st.checkbox(f"{nome_tosa} ({formatar_moeda(preco_sug)})", key=f"chk_t_{porte}_{nome_tosa}")
                if sel_t:
                    val_t = st.number_input(f"Valor {nome_tosa} (R$)", min_value=0.0, value=float(preco_sug), step=5.0, key=f"val_t_{porte}_{nome_tosa}")
                    servicos_selecionados_com_valores.append((f"{nome_tosa} ({porte})", val_t))

        # 3. CUIDADOS ADICIONAIS (R$ 10,00)
        with col_adic:
            st.markdown("##### 💅 Cuidados Adicionais")
            for nome_adic, preco_adic in ADICIONAIS:
                sel_ad = st.checkbox(f"{nome_adic} ({formatar_moeda(preco_adic)})", key=f"chk_ad_{nome_adic}")
                if sel_ad:
                    val_ad = st.number_input(f"Valor {nome_adic} (R$)", min_value=0.0, value=float(preco_adic), step=2.0, key=f"val_ad_{nome_adic}")
                    servicos_selecionados_com_valores.append((nome_adic, val_ad))

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
            lancar_caixa = st.checkbox("💰 Lançar automaticamente no Caixa", value=True)

        observacoes = st.text_area("📝 Observações do Atendimento", placeholder="Ex: Pet tranquilo, pelagem hidratada...", key="bt_obs")

        if st.button("💾 Salvar Atendimento em Banho e Tosa", type="primary", use_container_width=True):
            if not pet_nome or not tutor_nome:
                st.error("Por favor, preencha o Nome do Pet e o Nome do Tutor.")
            elif not servicos_selecionados_com_valores:
                st.error("Por favor, selecione pelo menos 1 serviço.")
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
                        "observacao": f"{desc_servicos} | Profissional: {profissional}",
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
        prof = row.get("profissional", "Silvaneidy (Groomer)")
        servs = row.get("servicos_detalhados", "")
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
            
            col_act1, col_act2, col_act3 = st.columns([3, 2, 1])
            with col_act2:
                with st.popover("🖨️ Imprimir Nota / Comprovante", use_container_width=True):
                    itens_rec = []
                    for pedaco in servs.split(","):
                        p = pedaco.strip()
                        if p:
                            itens_rec.append({"nome": p, "valor": val / max(1, len(servs.split(",")))})
                    
                    renderizar_modal_comprovante(
                        titulo="Nota de Banho e Tosa",
                        cliente_nome=tutor,
                        cliente_telefone=tel,
                        pet_nome=pet,
                        raca=raca,
                        porte=porte,
                        profissional=prof,
                        data_servico=data_s,
                        itens=itens_rec,
                        valor_total=val,
                        forma_pagamento=status_pag,
                        observacoes=obs,
                        codigo_recibo=str(rec_id)
                    )

            with col_act3:
                if st.button("🗑️", key=f"del_bt_{rec_id}", help="Excluir este atendimento"):
                    delete_record("Banho_Tosa", rec_id)
                    st.rerun()
