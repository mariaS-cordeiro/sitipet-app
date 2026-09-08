"""
Visão: Aba 2 – Banho e Tosa - SitiPet
Cadastro, edição completa de registros, lembretes de próximo banho (8, 15, 30 dias), emissão de notas e pós-venda.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
from utils.storage import load_table, insert_record, update_record, delete_record, PROFISSIONAIS
from utils.datas import (
    get_today_date, get_today_date_str, format_date_br,
    calcular_data_proximo_banho, avaliar_lembrete_banho, format_whatsapp_lembrete_banho, parse_date
)
from utils.financeiro import formatar_moeda
from utils.comprovante import renderizar_modal_comprovante, extrair_itens_servicos

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

OPCOES_LEMBRETE_DIAS = {
    "15 dias (Recomendado)": 15,
    "8 dias (Semanal)": 8,
    "30 dias (Mensal)": 30,
    "Sem lembrete": 0
}

def render_banho_tosa():
    st.markdown("## ✂️ Aba 2 – Banho e Tosa")
    st.markdown("Cadastre atendimentos, edite informações, defina lembretes de retorno (8, 15, 30 dias) e emita notas de serviço.")

    df_bt = load_table("Banho_Tosa")

    # Garantir compatibilidade de colunas caso venha de registros antigos
    if not df_bt.empty:
        if "data_proximo_banho" not in df_bt.columns:
            df_bt["data_proximo_banho"] = ""
        if "lembrete_status" not in df_bt.columns:
            df_bt["lembrete_status"] = "Sem Lembrete"
        if "lembrete_dias" not in df_bt.columns:
            df_bt["lembrete_dias"] = 0

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
        st.caption("Valores calculados automaticamente de acordo com o porte do pet.")

        col_banho, col_tosa, col_adic = st.columns(3)
        servicos_selecionados_com_valores = []

        # 1. BANHO & TOSA HIGIÊNICA
        with col_banho:
            st.markdown("##### 🛁 Banhos")
            preco_banho_sug = PRECOS_BANHO.get(porte, 50.0)
            sel_banho = st.checkbox(f"Banho ({formatar_moeda(preco_banho_sug)})", key=f"chk_banho_{porte}")
            if sel_banho:
                val_b = st.number_input(f"Valor Banho (R$)", min_value=0.0, value=float(preco_banho_sug), step=5.0, key=f"val_b_{porte}")
                servicos_selecionados_com_valores.append((f"Banho ({porte})", val_b))

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

        valor_total_calculado = sum(v for _, v in servicos_selecionados_com_valores)

        st.markdown("---")
        st.markdown("#### 3. Lembrete de Próximo Banho & Pagamento")
        col_lmb, col_tot1, col_tot2 = st.columns([2, 2, 2])

        with col_lmb:
            lembrete_sel_texto = st.selectbox(
                "🔔 Lembrete para Próximo Banho",
                list(OPCOES_LEMBRETE_DIAS.keys()),
                index=0,
                key="bt_lembrete_sel",
                help="O sistema avisará a administração quando chegar a data para convidar o tutor a agendar novamente."
            )
            dias_lembrete = OPCOES_LEMBRETE_DIAS[lembrete_sel_texto]
            data_prevista_prox = calcular_data_proximo_banho(data_atend, dias_lembrete)
            if dias_lembrete > 0:
                st.caption(f"📅 Próximo lembrete: **{format_date_br(data_prevista_prox)}** ({dias_lembrete} dias)")

        with col_tot1:
            st.markdown(f"""
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 10px; padding: 10px 16px; text-align: center;">
                    <span style="font-size: 12px; color: #15803d; font-weight: 600;">VALOR TOTAL CALCULADO</span>
                    <h3 style="margin: 2px 0; color: #166534;">{formatar_moeda(valor_total_calculado)}</h3>
                </div>
            """, unsafe_allow_html=True)

        with col_tot2:
            forma_pag = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pendente"], key="bt_formapag")
            lancar_caixa = st.checkbox("💰 Lançar no Caixa", value=True)

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
                    "lembrete_dias": int(dias_lembrete),
                    "data_proximo_banho": data_prevista_prox,
                    "lembrete_status": "Pendente" if dias_lembrete > 0 else "Sem Lembrete",
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

    # ==================== ABAS DE VISUALIZAÇÃO: HISTÓRICO, LEMBRETES & CUPOM ====================
    st.markdown("---")
    tab_historico, tab_lembretes, tab_cupons = st.tabs([
        "📋 **Histórico de Atendimentos & Edição**",
        "🔔 **Central de Lembretes de Retorno (Pós-Venda)**",
        "🧾 **Cupom & Comprovante por Cachorro**"
    ])

    # ------------------ TAB 1: HISTÓRICO COM EDIÇÃO COMPLETA ------------------
    with tab_historico:
        if df_bt.empty:
            st.info("Nenhum registro de banho e tosa encontrado.")
        else:
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
                pet = row.get("pet_nome", "")
                tutor = row.get("tutor_nome", "")
                tel = row.get("tutor_telefone", "")
                raca = row.get("raca", "")
                porte_val = row.get("porte", "Pequeno")
                data_s = row.get("data", "")
                hora_s = row.get("horario", "")
                prof = row.get("profissional", "Silvaneidy (Groomer)")
                servs = row.get("servicos_detalhados", "")
                val = float(row.get("valor_total", 0.0))
                status_pag = row.get("status_pagamento", "Pago")
                obs = row.get("observacoes", "")
                
                # Info de lembrete
                dt_prox_b = row.get("data_proximo_banho", "")
                st_lmb = row.get("lembrete_status", "Pendente")
                info_lmb = avaliar_lembrete_banho(dt_prox_b, st_lmb)

                with st.container():
                    st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); border-left: 5px solid #d82678;">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <div>
                                    <span style="font-size: 17px; font-weight: 700; color: #1e293b;">🐶 {pet} ({raca} • {porte_val})</span>
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
                                {f'<br>🔔 <b>Lembrete Retorno:</b> <span style="color: {info_lmb["cor"]}; font-weight: 700;">{info_lmb["icon"]} {info_lmb["mensagem"]}</span>' if dt_prox_b else ''}
                                {f'<br>📝 <i>Obs: {obs}</i>' if obs else ''}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
                    col_act1, col_act2, col_act3, col_act4 = st.columns([2, 3, 2, 1])

                    # 1. BOTÃO EDITAR REGISTRO
                    with col_act1:
                        with st.popover("✏️ Editar Registro", use_container_width=True):
                            st.markdown(f"#### ✏️ Editar Atendimento: **{pet}**")
                            e_pet = st.text_input("Nome do Pet", value=str(pet), key=f"e_pet_{rec_id}")
                            e_tutor = st.text_input("Nome do Tutor", value=str(tutor), key=f"e_tut_{rec_id}")
                            e_tel = st.text_input("Telefone", value=str(tel), key=f"e_tel_{rec_id}")
                            e_raca = st.text_input("Raça", value=str(raca), key=f"e_raca_{rec_id}")
                            
                            col_e1, col_e2 = st.columns(2)
                            with col_e1:
                                port_idx = ["Pequeno", "Médio", "Grande", "Gigante"].index(porte_val) if porte_val in ["Pequeno", "Médio", "Grande", "Gigante"] else 0
                                e_porte = st.selectbox("Porte", ["Pequeno", "Médio", "Grande", "Gigante"], index=port_idx, key=f"e_port_{rec_id}")
                            with col_e2:
                                prof_idx = PROFISSIONAIS.index(prof) if prof in PROFISSIONAIS else 0
                                e_prof = st.selectbox("Profissional", PROFISSIONAIS, index=prof_idx, key=f"e_prof_{rec_id}")

                            col_e3, col_e4 = st.columns(2)
                            with col_e3:
                                e_data = st.date_input("Data", value=parse_date(data_s), key=f"e_dt_{rec_id}")
                            with col_e4:
                                e_val = st.number_input("Valor Total (R$)", min_value=0.0, value=float(val), step=5.0, key=f"e_val_{rec_id}")

                            e_servs = st.text_area("Serviços Detalhados", value=str(servs), key=f"e_srv_{rec_id}")
                            e_pag = st.selectbox("Status Pagamento", ["Pago (Pix)", "Pago (Cartão de Crédito)", "Pago (Cartão de Débito)", "Pago (Dinheiro)", "Pendente"], key=f"e_pag_{rec_id}")
                            
                            st.markdown("---")
                            st.markdown("**Configuração do Lembrete de Próximo Banho:**")
                            col_el1, col_el2 = st.columns(2)
                            with col_el1:
                                val_dias_cur = int(row.get("lembrete_dias", 15)) if pd.notna(row.get("lembrete_dias")) and str(row.get("lembrete_dias")).isdigit() else 15
                                e_dias_lmb = st.selectbox("Intervalo de Retorno", [0, 8, 15, 30], index=[0, 8, 15, 30].index(val_dias_cur) if val_dias_cur in [0, 8, 15, 30] else 2, key=f"e_dlmb_{rec_id}")
                            with col_el2:
                                e_st_lmb = st.selectbox("Status do Lembrete", ["Pendente", "Contatado", "Agendado", "Sem Lembrete"], index=["Pendente", "Contatado", "Agendado", "Sem Lembrete"].index(st_lmb) if st_lmb in ["Pendente", "Contatado", "Agendado", "Sem Lembrete"] else 0, key=f"e_stlmb_{rec_id}")

                            e_obs = st.text_input("Observações", value=str(obs), key=f"e_obs_{rec_id}")

                            if st.button("💾 Salvar Alterações", key=f"btn_save_edit_{rec_id}", type="primary"):
                                dt_prox_calc = calcular_data_proximo_banho(e_data, e_dias_lmb) if e_dias_lmb > 0 else ""
                                update_record("Banho_Tosa", rec_id, {
                                    "pet_nome": e_pet.strip(),
                                    "tutor_nome": e_tutor.strip(),
                                    "tutor_telefone": e_tel.strip(),
                                    "raca": e_raca.strip(),
                                    "porte": e_porte,
                                    "profissional": e_prof,
                                    "data": e_data.strftime("%Y-%m-%d"),
                                    "servicos_detalhados": e_servs.strip(),
                                    "valor_total": float(e_val),
                                    "status_pagamento": e_pag,
                                    "lembrete_dias": int(e_dias_lmb),
                                    "data_proximo_banho": dt_prox_calc,
                                    "lembrete_status": e_st_lmb if e_dias_lmb > 0 else "Sem Lembrete",
                                    "observacoes": e_obs.strip()
                                })
                                st.success("Registro atualizado com sucesso!")
                                st.rerun()

                    # 2. BOTÃO EMITIR NOTA / CUPOM
                    with col_act2:
                        with st.popover("🖨️ Cupom / Nota", use_container_width=True):
                            itens_rec = extrair_itens_servicos(servs, valor_total_fallback=val)
                            
                            renderizar_modal_comprovante(
                                titulo="Cupom de Banho e Tosa",
                                cliente_nome=tutor,
                                cliente_telefone=tel,
                                pet_nome=pet,
                                raca=raca,
                                porte=porte_val,
                                profissional=prof,
                                data_servico=data_s,
                                itens=itens_rec,
                                valor_total=val,
                                forma_pagamento=status_pag,
                                observacoes=obs,
                                codigo_recibo=str(rec_id)
                            )

                    # 3. WHATSAPP LEMBRETE RÁPIDO
                    with col_act3:
                        if tel:
                            dias_int = int(row.get("lembrete_dias", 15)) if pd.notna(row.get("lembrete_dias")) and str(row.get("lembrete_dias")).isdigit() else 15
                            wa_link = format_whatsapp_lembrete_banho(tel, tutor, pet, dias_int, data_s)
                            st.link_button("💬 WhatsApp", wa_link, use_container_width=True)

                    # 4. EXCLUIR
                    with col_act4:
                        if st.button("🗑️", key=f"del_bt_{rec_id}", help="Excluir este atendimento"):
                            delete_record("Banho_Tosa", rec_id)
                            st.rerun()

    # ------------------ TAB 2: CENTRAL DE LEMBRETES DE RETORNO ------------------
    with tab_lembretes:
        st.markdown("### 🔔 Central de Lembretes de Retorno para Próximo Banho")
        st.markdown("Gerencie o pós-venda, visualize os pets que atingiram o prazo de 8, 15 ou 30 dias e entre em contato direto pelo WhatsApp.")

        if df_bt.empty:
            st.info("Nenhum atendimento registrado.")
        else:
            # Filtrar registros que possuem lembrete com verificação segura de coluna
            if "data_proximo_banho" in df_bt.columns:
                df_com_lembrete = df_bt[df_bt["data_proximo_banho"].fillna("").astype(str).str.len() >= 8].copy()
            else:
                df_com_lembrete = pd.DataFrame()
            
            if df_com_lembrete.empty:
                st.info("Nenhum lembrete de retorno configurado nos atendimentos anteriores. Ao cadastrar um novo banho, selecione o prazo de 8, 15 ou 30 dias!")
            else:
                col_flmb1, col_flmb2 = st.columns([3, 2])
                with col_flmb1:
                    filtro_lmb = st.selectbox(
                        "Filtrar Situação:",
                        ["🚨 Para Contatar Agora (Hoje ou Atrasados)", "📅 Próximos 7 dias", "📋 Todos os Lembretes", "✅ Já Contatados / Agendados"]
                    )

                pets_para_exibir = []
                d_hoje = date.today()

                for _, r_l in df_com_lembrete.iterrows():
                    dt_p = str(r_l.get("data_proximo_banho", ""))
                    st_p = str(r_l.get("lembrete_status", "Pendente"))
                    info = avaliar_lembrete_banho(dt_p, st_p)

                    d_p_obj = parse_date(dt_p)
                    diff = (d_p_obj - d_hoje).days

                    if filtro_lmb == "🚨 Para Contatar Agora (Hoje ou Atrasados)":
                        if info["deve_contatar"] and diff <= 0 and st_p == "Pendente":
                            pets_para_exibir.append((r_l, info))
                    elif filtro_lmb == "📅 Próximos 7 dias":
                        if 0 <= diff <= 7 and st_p == "Pendente":
                            pets_para_exibir.append((r_l, info))
                    elif filtro_lmb == "✅ Já Contatados / Agendados":
                        if st_p in ["Contatado", "Agendado"]:
                            pets_para_exibir.append((r_l, info))
                    else:
                        pets_para_exibir.append((r_l, info))

                st.caption(f"Mostrando **{len(pets_para_exibir)}** lembrete(s)")

                if not pets_para_exibir:
                    st.success("🎉 Nenhum cliente pendente para contato neste filtro!")
                else:
                    for r_item, info_item in pets_para_exibir:
                        r_id = r_item.get("id")
                        r_pet = r_item.get("pet_nome")
                        r_tutor = r_item.get("tutor_nome")
                        r_tel = r_item.get("tutor_telefone")
                        r_ult_dt = r_item.get("data")
                        r_prox_dt = r_item.get("data_proximo_banho")
                        r_dias_raw = r_item.get("lembrete_dias", 15)
                        r_dias = int(r_dias_raw) if pd.notna(r_dias_raw) and str(r_dias_raw).isdigit() else 15
                        r_st_lmb = r_item.get("lembrete_status", "Pendente")

                        st.markdown(f"""
                            <div style="background: white; border-radius: 12px; padding: 16px 20px; margin-bottom: 12px; border-left: 6px solid {info_item['cor']}; box-shadow: 0 2px 8px rgba(0,0,0,0.05);">
                                <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                    <div>
                                        <span style="font-size: 18px; font-weight: 800; color: #1e293b;">🐶 {r_pet}</span>
                                        <span style="color: #64748b; font-size: 14px;"> | Tutor: <b>{r_tutor}</b> ({r_tel})</span>
                                    </div>
                                    <div>
                                        <span style="background: {info_item['cor']}20; color: {info_item['cor']}; padding: 4px 12px; border-radius: 20px; font-weight: 700; font-size: 13px;">
                                            {info_item['icon']} {info_item['mensagem']}
                                        </span>
                                    </div>
                                </div>
                                <div style="margin-top: 8px; font-size: 13px; color: #334155;">
                                    📅 <b>Último Banho:</b> {format_date_br(r_ult_dt)} &nbsp;|&nbsp; 
                                    ⏰ <b>Previsão de Retorno:</b> <b>{format_date_br(r_prox_dt)}</b> (Intervalo: {r_dias} dias) &nbsp;|&nbsp; 
                                    📌 <b>Status:</b> {r_st_lmb}
                                </div>
                            </div>
                        """, unsafe_allow_html=True)

                        col_lmb_b1, col_lmb_b2, col_lmb_b3 = st.columns([3, 2, 2])
                        with col_lmb_b1:
                            wa_link_ret = format_whatsapp_lembrete_banho(r_tel, r_tutor, r_pet, r_dias, r_ult_dt)
                            if wa_link_ret:
                                st.link_button("💬 Enviar Mensagem no WhatsApp", wa_link_ret, use_container_width=True)
                        with col_lmb_b2:
                            if st.button("✅ Marcar como Contatado", key=f"btn_cont_{r_id}", use_container_width=True):
                                update_record("Banho_Tosa", r_id, {"lembrete_status": "Contatado"})
                                st.rerun()
                        with col_lmb_b3:
                            if st.button("📅 Marcar como Reagendado", key=f"btn_reag_{r_id}", use_container_width=True):
                                update_record("Banho_Tosa", r_id, {"lembrete_status": "Agendado"})
                                st.rerun()

    # ------------------ TAB 3: EMISSÃO DE CUPOM DE SERVIÇOS POR CACHORRO ------------------
    with tab_cupons:
        st.markdown("### 🧾 Emissão & Visualização de Cupom de Serviços por Cachorro")
        st.caption("Reúna todos os serviços realizados para um pet em um único comprovante detalhado (estilo cupom de supermercado), com discriminação de cada item, valores individuais, subtotal e total. Perfeito para imprimir, salvar em PDF ou enviar no WhatsApp do tutor.")

        # Carregar pets de todas as fontes para seleção fácil
        df_agd_all = load_table("Agenda")
        df_hosp_all = load_table("Hospedagem")
        
        # Mapear pets únicos conhecidos
        pets_conhecidos = {}
        
        if not df_bt.empty:
            for _, r in df_bt.iterrows():
                p_n = str(r.get("pet_nome", "")).strip()
                if p_n and p_n not in pets_conhecidos:
                    pets_conhecidos[p_n] = {
                        "pet_nome": p_n,
                        "tutor_nome": str(r.get("tutor_nome", "")),
                        "tutor_telefone": str(r.get("tutor_telefone", "")),
                        "raca": str(r.get("raca", "")),
                        "porte": str(r.get("porte", "Pequeno")),
                        "profissional": str(r.get("profissional", "Silvaneidy (Groomer)")),
                        "servicos_detalhados": str(r.get("servicos_detalhados", "")),
                        "valor_total": float(r.get("valor_total", 0.0)),
                        "forma_pagamento": str(r.get("status_pagamento", "Pago (Pix)")),
                        "data": str(r.get("data", get_today_date_str())),
                        "id": str(r.get("id", "BT-001"))
                    }

        if not df_agd_all.empty:
            for _, r in df_agd_all.iterrows():
                p_n = str(r.get("pet_nome", "")).strip()
                if p_n and p_n not in pets_conhecidos:
                    pets_conhecidos[p_n] = {
                        "pet_nome": p_n,
                        "tutor_nome": str(r.get("tutor_nome", "")),
                        "tutor_telefone": str(r.get("tutor_telefone", "")),
                        "raca": str(r.get("raca", "")),
                        "porte": str(r.get("porte", "Pequeno")),
                        "profissional": str(r.get("profissional", "Silvaneidy (Groomer)")),
                        "servicos_detalhados": str(r.get("servicos", "")),
                        "valor_total": float(r.get("valor_total", 0.0)),
                        "forma_pagamento": "Pix",
                        "data": str(r.get("data", get_today_date_str())),
                        "id": str(r.get("id", "AGD-001"))
                    }

        if not df_hosp_all.empty:
            for _, r in df_hosp_all.iterrows():
                p_n = str(r.get("pet_nome", "")).strip()
                if p_n and p_n not in pets_conhecidos:
                    pets_conhecidos[p_n] = {
                        "pet_nome": p_n,
                        "tutor_nome": str(r.get("tutor_nome", "")),
                        "tutor_telefone": str(r.get("tutor_telefone", "")),
                        "raca": "SRD",
                        "porte": "Médio",
                        "profissional": "Equipe SitiPet",
                        "servicos_detalhados": f"Hospedagem ({r.get('diarias', 1)} diárias)",
                        "valor_total": float(r.get("valor_total", 0.0)),
                        "forma_pagamento": str(r.get("forma_pagamento", "Pix")),
                        "data": str(r.get("data_entrada", get_today_date_str())),
                        "id": str(r.get("id", "HOSP-001"))
                    }

        opcoes_pets = ["➕ [Digitar Novo Cachorro / Atendimento Avulso]"] + [
            f"🐶 {p_info['pet_nome']} (Tutor: {p_info['tutor_nome']})" for p_info in pets_conhecidos.values()
        ]

        col_cup1, col_cup2 = st.columns([1, 1], gap="large")

        with col_cup1:
            st.markdown("#### 1. Selecionar ou Preencher Dados")
            sel_pet_opcao = st.selectbox("Selecione um Pet Cadastrado ou crie um novo:", opcoes_pets, key="sel_pet_cupom")
            
            dados_base = {}
            if sel_pet_opcao != "➕ [Digitar Novo Cachorro / Atendimento Avulso]":
                nome_limpo_pet = sel_pet_opcao.replace("🐶 ", "").split(" (Tutor:")[0].strip()
                dados_base = pets_conhecidos.get(nome_limpo_pet, {})

            col_cp1, col_cp2 = st.columns(2)
            with col_cp1:
                cp_pet = st.text_input("🐶 Nome do Cachorro *", value=dados_base.get("pet_nome", ""), placeholder="Ex: Bob, Mel, Luna", key="cp_pet_n")
                cp_raca = st.text_input("Raça", value=dados_base.get("raca", ""), placeholder="Ex: Poodle, Shih-tzu", key="cp_raca_n")
            with col_cp2:
                lista_portes = ["Pequeno", "Médio", "Grande", "Gigante"]
                porte_base_idx = lista_portes.index(dados_base.get("porte", "Pequeno")) if dados_base.get("porte") in lista_portes else 0
                cp_porte = st.selectbox("Porte", lista_portes, index=porte_base_idx, key="cp_porte_n")
                cp_prof = st.selectbox("Profissional", PROFISSIONAIS, index=PROFISSIONAIS.index(dados_base.get("profissional")) if dados_base.get("profissional") in PROFISSIONAIS else 0, key="cp_prof_n")

            col_cp3, col_cp4 = st.columns(2)
            with col_cp3:
                cp_tutor = st.text_input("👤 Nome do Tutor(a) *", value=dados_base.get("tutor_nome", ""), placeholder="Ex: Maria Cordeiro", key="cp_tut_n")
            with col_cp4:
                cp_tel = st.text_input("📱 Telefone / WhatsApp", value=dados_base.get("tutor_telefone", ""), placeholder="(11) 98888-7777", key="cp_tel_n")

            col_cp5, col_cp6 = st.columns(2)
            with col_cp5:
                cp_data = st.date_input("📅 Data do Serviço", value=parse_date(dados_base.get("data", get_today_date_str())), key="cp_dt_n")
            with col_cp6:
                fp_list = ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pendente"]
                fp_base = dados_base.get("forma_pagamento", "Pix")
                fp_idx = 0
                for idx_fp, fp_item in enumerate(fp_list):
                    if fp_item in fp_base:
                        fp_idx = idx_fp
                        break
                cp_fp = st.selectbox("Forma de Pagamento", fp_list, index=fp_idx, key="cp_fp_n")

            st.markdown("---")
            st.markdown("#### 2. Discriminação dos Serviços & Valores")
            st.caption("Adicione ou edite cada serviço realizado para compor o cupom detalhado.")

            # Extrair itens existentes se selecionou pet conhecido
            itens_iniciais = []
            if dados_base.get("servicos_detalhados"):
                itens_iniciais = extrair_itens_servicos(dados_base.get("servicos_detalhados"), dados_base.get("valor_total", 0.0))
            
            if not itens_iniciais:
                itens_iniciais = [
                    {"nome": f"Banho ({cp_porte})", "valor": PRECOS_BANHO.get(cp_porte, 50.0)},
                    {"nome": "Corte de unhas", "valor": 10.0}
                ]

            lista_servicos_finais = []

            for i in range(5):
                nome_padrao = itens_iniciais[i]["nome"] if i < len(itens_iniciais) else ""
                valor_padrao = float(itens_iniciais[i]["valor"]) if i < len(itens_iniciais) else 0.0
                ativo_padrao = True if i < len(itens_iniciais) else False

                col_it_chk, col_it_nome, col_it_val = st.columns([1, 4, 2])
                with col_it_chk:
                    st.write("")
                    st.write("")
                    incluir_item = st.checkbox(f"#{i+1}", value=ativo_padrao, key=f"chk_cupom_it_{i}")
                with col_it_nome:
                    nome_srv = st.text_input(f"Descrição do Serviço {i+1}", value=nome_padrao, placeholder=f"Ex: Serviço {i+1}", key=f"nome_cupom_it_{i}")
                with col_it_val:
                    val_srv = st.number_input(f"Valor (R$)", min_value=0.0, value=valor_padrao, step=5.0, key=f"val_cupom_it_{i}")

                if incluir_item and nome_srv.strip():
                    lista_servicos_finais.append({"nome": nome_srv.strip(), "valor": float(val_srv)})

            col_sub1, col_sub2 = st.columns(2)
            with col_sub1:
                cp_desconto = st.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=5.0, key="cp_desc_n")
            with col_sub2:
                cp_obs = st.text_input("Observações no Cupom", value="", placeholder="Ex: Brinde gravatinha / Pet vacinado", key="cp_obs_n")

            subtotal_calc = sum(it["valor"] for it in lista_servicos_finais)
            total_final_calc = max(0.0, subtotal_calc - cp_desconto)

        with col_cup2:
            st.markdown("#### 3. Visualização do Cupom (Estilo Supermercado)")
            st.caption("Pré-visualização ao vivo do comprovante gerado:")

            recibo_cod = dados_base.get("id") or f"CUP-{datetime.now().strftime('%d%H%M%S')}"

            renderizar_modal_comprovante(
                titulo="Cupom de Serviços SitiPet",
                cliente_nome=cp_tutor if cp_tutor else "Cliente SitiPet",
                cliente_telefone=cp_tel,
                pet_nome=cp_pet if cp_pet else "Pet",
                raca=cp_raca,
                porte=cp_porte,
                profissional=cp_prof,
                data_servico=cp_data.strftime("%Y-%m-%d"),
                itens=lista_servicos_finais,
                valor_total=total_final_calc,
                forma_pagamento=cp_fp,
                observacoes=cp_obs,
                codigo_recibo=recibo_cod,
                desconto=cp_desconto
            )

