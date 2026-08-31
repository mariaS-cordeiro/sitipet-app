"""
Visão: Aba 1 – Agenda Diária - SitiPet
Controle dos atendimentos do dia, alertas de horário e fluxo integrado com Caixa e Banho & Tosa.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, time
import re
from utils.storage import load_table, insert_record, update_record, delete_record, concluir_atendimento_agenda
from utils.datas import get_today_date, get_today_date_str, format_date_br, calcular_status_alerta_horario, parse_date
from utils.financeiro import formatar_moeda

STATUS_OPCOES = ["Agendado", "Confirmado", "Em atendimento", "Finalizado", "Cancelado"]

def format_whatsapp_link(telefone: str, pet_nome: str, horario: str) -> str:
    """Gera link direto para contato via WhatsApp."""
    if not telefone:
        return ""
    num_limpo = re.sub(r"[^\d]", "", telefone)
    if len(num_limpo) in [10, 11] and not num_limpo.startswith("55"):
        num_limpo = f"55{num_limpo}"
    msg = f"Olá! Aqui é da SitiPet Pet Shop. Estamos confirmando o atendimento do(a) {pet_nome} agendado para às {horario}. Qualquer dúvida estamos à disposição! 🐾"
    import urllib.parse
    return f"https://wa.me/{num_limpo}?text={urllib.parse.quote(msg)}"

def render_agenda():
    st.markdown("## 📅 Aba 1 – Agenda Diária de Atendimentos")
    st.markdown("Gerencie os agendamentos diários, monitore horários e conclua atendimentos com envio automático para o Caixa.")

    df_agenda = load_table("Agenda")
    df_servicos = load_table("Servicos_Precos")

    # Lista de serviços para o seletor
    lista_servicos = []
    if not df_servicos.empty and "nome" in df_servicos.columns:
        lista_servicos = df_servicos[df_servicos["ativo"] == True]["nome"].tolist()
    if not lista_servicos:
        lista_servicos = ["Banho simples", "Banho com hidratação", "Tosa higiênica", "Tosa completa", "Tosa bebê", "Corte de unhas"]

    # ==================== FORMULÁRIO DE NOVO AGENDAMENTO ====================
    with st.expander("➕ **Cadastrar Novo Atendimento na Agenda**", expanded=False):
        with st.form("form_novo_agendamento", clear_on_submit=True):
            col_f1, col_f2, col_f3 = st.columns(3)
            with col_f1:
                pet_nome = st.text_input("🐶 Nome do Animal / Pet *", placeholder="Ex: Mel, Thor, Pipoca")
                raca = st.text_input("Raça do Pet", placeholder="Ex: Shih-tzu, Poodle, SRD")
            with col_f2:
                tutor_nome = st.text_input("👤 Nome do Responsável / Tutor *", placeholder="Ex: Juliana Mendes")
                tutor_telefone = st.text_input("📱 Telefone / WhatsApp *", placeholder="(11) 98765-4321")
            with col_f3:
                porte = st.selectbox("Porte", ["Pequeno", "Médio", "Grande", "Gigante"])
                profissional = st.selectbox("Profissional Responsável", ["Carlos (Tosa)", "Ana Paula (Banho)", "Mariana", "Equipe Geral"])

            col_f4, col_f5, col_f6 = st.columns(3)
            with col_f4:
                data_agendada = st.date_input("📅 Data do Atendimento", value=get_today_date())
            with col_f5:
                horarios_sugeridos = [f"{h:02d}:{m:02d}" for h in range(8, 20) for m in (0, 30)]
                horario_agendado = st.selectbox("⏰ Horário", horarios_sugeridos, index=4) # 10:00
            with col_f6:
                status_inicial = st.selectbox("Status Inicial", STATUS_OPCOES, index=0)

            servicos_selecionados = st.multiselect(
                "✂️ Serviços Agendados *",
                options=lista_servicos,
                default=[lista_servicos[0]] if lista_servicos else []
            )

            # Estimativa de valor
            valor_estimado = 0.0
            if not df_servicos.empty and "nome" in df_servicos.columns and "preco_padrao" in df_servicos.columns:
                for s in servicos_selecionados:
                    match_row = df_servicos[df_servicos["nome"] == s]
                    if not match_row.empty:
                        valor_estimado += float(match_row["preco_padrao"].values[0])

            col_v1, col_v2 = st.columns([1, 2])
            with col_v1:
                valor_total = st.number_input("💵 Valor Total Previsto (R$)", min_value=0.0, value=float(valor_estimado), step=5.0)
            with col_v2:
                observacoes = st.text_input("📝 Observações", placeholder="Ex: Alergia a shampoo perfumado, trazer focinheira, etc.")

            btn_salvar = st.form_submit_button("💾 Salvar Agendamento", use_container_width=True, type="primary")

            if btn_salvar:
                if not pet_nome or not tutor_nome:
                    st.error("Por favor, preencha pelo menos o Nome do Animal e o Nome do Tutor.")
                else:
                    novo_rec = {
                        "id": f"AGD-{datetime.now().strftime('%d%H%M%S')}",
                        "data": data_agendada.strftime("%Y-%m-%d"),
                        "horario": horario_agendado,
                        "pet_nome": pet_nome.strip(),
                        "raca": raca.strip(),
                        "porte": porte,
                        "tutor_nome": tutor_nome.strip(),
                        "tutor_telefone": tutor_telefone.strip(),
                        "servicos": " + ".join(servicos_selecionados) if servicos_selecionados else "Banho e Tosa",
                        "valor_total": float(valor_total),
                        "profissional": profissional,
                        "status": status_inicial,
                        "observacoes": observacoes.strip(),
                        "criado_em": get_today_date_str()
                    }
                    insert_record("Agenda", novo_rec)
                    st.success(f"✅ Atendimento de **{pet_nome}** agendado para {format_date_br(data_agendada)} às {horario_agendado} com sucesso!")
                    st.rerun()

    # ==================== FILTROS E VISUALIZAÇÃO ====================
    st.markdown("---")
    st.markdown("### 🔍 Consultar e Gerenciar Atendimentos")

    col_flt1, col_flt2, col_flt3 = st.columns([2, 2, 2])
    with col_flt1:
        data_filtro = st.date_input("Filtrar por Data", value=get_today_date(), key="filtro_data_agenda")
    with col_flt2:
        ver_todos_dias = st.checkbox("📅 Visualizar Todos os Dias (Histórico Completo)", value=False)
    with col_flt3:
        status_filtro = st.selectbox("Filtrar por Status", ["Todos"] + STATUS_OPCOES)

    # Filtrar
    df_exibicao = df_agenda.copy() if not df_agenda.empty else pd.DataFrame()

    if not df_exibicao.empty:
        if not ver_todos_dias:
            data_filtro_str = data_filtro.strftime("%Y-%m-%d")
            df_exibicao = df_exibicao[df_exibicao["data"].astype(str) == data_filtro_str]
        
        if status_filtro != "Todos":
            df_exibicao = df_exibicao[df_exibicao["status"] == status_filtro]

    if df_exibicao.empty:
        st.info("Nenhum atendimento encontrado para os filtros selecionados.")
        return

    # Ordenar por data e horário
    df_exibicao = df_exibicao.sort_values(by=["data", "horario"], ascending=[True, True])

    # Contadores rápidos do filtro
    total_filtrados = len(df_exibicao)
    total_concluidos = len(df_exibicao[df_exibicao["status"] == "Finalizado"])
    st.caption(f"Exibindo **{total_filtrados}** atendimento(s) | **{total_concluidos}** finalizado(s)")

    # ==================== CARDS DE ATENDIMENTOS ====================
    for _, row in df_exibicao.iterrows():
        ag_id = row.get("id")
        pet = row.get("pet_nome", "")
        tutor = row.get("tutor_nome", "")
        telefone = row.get("tutor_telefone", "")
        data_atend = row.get("data", "")
        horario = row.get("horario", "")
        servicos = row.get("servicos", "")
        valor = float(row.get("valor_total", 0.0))
        status = row.get("status", "Agendado")
        prof = row.get("profissional", "Geral")
        obs = row.get("observacoes", "")

        alerta = calcular_status_alerta_horario(data_atend, horario, status)
        cor_borda = alerta["cor"]

        with st.container():
            st.markdown(f"""
                <div style="background: white; border-radius: 14px; padding: 18px 22px; margin-bottom: 15px; border-left: 6px solid {cor_borda}; box-shadow: 0 2px 10px rgba(0,0,0,0.05);">
                    <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                        <div>
                            <span style="font-size: 18px; font-weight: 800; color: #1e293b;">⏰ {horario} - 🐶 {pet}</span>
                            <span style="color: #64748b; font-size: 14px; font-weight: 500;"> | Tutor(a): <b>{tutor}</b> ({telefone})</span>
                        </div>
                        <div style="margin-top: 4px;">
                            <span style="background: {cor_borda}20; color: {cor_borda}; padding: 5px 12px; border-radius: 20px; font-weight: 700; font-size: 13px;">
                                {alerta['icon']} {status} {f'• {alerta["badge_label"]}' if alerta["badge_label"] not in [status, "Finalizado", "Cancelado"] else ""}
                            </span>
                        </div>
                    </div>
                    <div style="margin-top: 10px; font-size: 14px; color: #334155; line-height: 1.6;">
                        ✂️ <b>Serviços:</b> {servicos} <br>
                        👤 <b>Profissional:</b> {prof} &nbsp;|&nbsp; 💵 <b>Valor:</b> <span style="font-weight: 700; color: #10b981;">{formatar_moeda(valor)}</span> &nbsp;|&nbsp; 📅 <b>Data:</b> {format_date_br(data_atend)}
                        {f'<br>📝 <i>Obs: {obs}</i>' if obs else ''}
                    </div>
                </div>
            """, unsafe_allow_html=True)

            # Botões de Ação do Card
            col_b1, col_b2, col_b3, col_b4 = st.columns([2, 3, 2, 2])
            
            with col_b1:
                if status == "Agendado":
                    if st.button("✂️ Iniciar", key=f"btn_init_{ag_id}", use_container_width=True):
                        update_record("Agenda", ag_id, {"status": "Em atendimento"})
                        st.success(f"Atendimento de {pet} iniciado!")
                        st.rerun()
                elif status == "Em atendimento":
                    st.info("Em atendimento...")

            with col_b2:
                if status != "Finalizado" and status != "Cancelado":
                    with st.popover("✅ Concluir & Lançar Caixa", use_container_width=True):
                        st.markdown(f"**Concluir atendimento de {pet}**")
                        st.write(f"Valor a receber: **{formatar_moeda(valor)}**")
                        forma_pag = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"], key=f"fp_{ag_id}")
                        if st.button("Confirmar Conclusão", key=f"conf_{ag_id}", type="primary"):
                            concluir_atendimento_agenda(ag_id, forma_pagamento=forma_pag)
                            st.success(f"Atendimento de {pet} concluído e lançado no Caixa!")
                            st.rerun()

            with col_b3:
                wa_url = format_whatsapp_link(telefone, pet, horario)
                if wa_url:
                    st.link_button("💬 WhatsApp", wa_url, use_container_width=True)

            with col_b4:
                with st.popover("⚙️ Opções", use_container_width=True):
                    novo_st = st.selectbox("Alterar Status", STATUS_OPCOES, index=STATUS_OPCOES.index(status) if status in STATUS_OPCOES else 0, key=f"sel_st_{ag_id}")
                    if st.button("Salvar Status", key=f"save_st_{ag_id}"):
                        update_record("Agenda", ag_id, {"status": novo_st})
                        st.rerun()
                    
                    st.divider()
                    if st.button("🗑️ Excluir", key=f"del_{ag_id}", type="secondary"):
                        delete_record("Agenda", ag_id)
                        st.warning("Atendimento excluído.")
                        st.rerun()
