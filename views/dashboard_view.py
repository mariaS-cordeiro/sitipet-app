"""
Visão: Dashboard / Painel Geral - SitiPet
Apresenta indicadores rápidos de gestão, alertas de atendimento, lembretes de retorno de banho e visão panorâmica.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
from utils.storage import load_table, update_record
from utils.datas import (
    get_today_date_str, format_date_br, calcular_status_alerta_horario,
    avaliar_lembrete_banho, format_whatsapp_lembrete_banho, parse_date
)
from utils.financeiro import formatar_moeda, calcular_metricas_financeiras

def render_dashboard(set_page_callback=None):
    hoje = get_today_date_str()
    d_hoje = date.today()
    mes_atual = d_hoje.month
    ano_atual = d_hoje.year

    # Carregar dados
    df_agenda = load_table("Agenda")
    df_bt = load_table("Banho_Tosa")
    df_hospedagem = load_table("Hospedagem")
    df_caixa = load_table("Caixa")

    # Métricas Rápidas
    # 1. Atendimentos Hoje
    if not df_agenda.empty and "data" in df_agenda.columns:
        df_agenda_hoje = df_agenda[df_agenda["data"].astype(str) == hoje]
        qtd_atendimentos_hoje = len(df_agenda_hoje)
        qtd_finalizados_hoje = len(df_agenda_hoje[df_agenda_hoje["status"] == "Finalizado"])
    else:
        df_agenda_hoje = pd.DataFrame()
        qtd_atendimentos_hoje = 0
        qtd_finalizados_hoje = 0

    # 2. Hospedados Agora
    if not df_hospedagem.empty and "status" in df_hospedagem.columns:
        df_hosp_ativos = df_hospedagem[df_hospedagem["status"] == "Hospedado"]
        qtd_hospedados_agora = len(df_hosp_ativos)
    else:
        df_hosp_ativos = pd.DataFrame()
        qtd_hospedados_agora = 0

    # 3. Lembretes de Retorno de Banho para Hoje / Atrasados
    lembretes_pendentes = []
    if not df_bt.empty and "data_proximo_banho" in df_bt.columns:
        for _, r_bt in df_bt.iterrows():
            dt_prox = r_bt.get("data_proximo_banho", "")
            st_lmb = r_bt.get("lembrete_status", "Pendente")
            if dt_prox and st_lmb == "Pendente":
                info_l = avaliar_lembrete_banho(dt_prox, st_lmb)
                d_p = parse_date(dt_prox)
                if (d_p - d_hoje).days <= 0:
                    lembretes_pendentes.append((r_bt, info_l))

    # 4. Finanças do Mês Atual
    metricas_mes = calcular_metricas_financeiras(df_caixa, mes=mes_atual, ano=ano_atual)
    hoje_fmt = format_date_br(d_hoje)

    # ==================== CARDS DE INDICADORES RÁPIDOS ====================
    st.markdown(f"""
        <div style="background: linear-gradient(135deg, #24398e 0%, #1e293b 100%); padding: 18px 24px; border-radius: 16px; color: white; margin-bottom: 24px; box-shadow: 0 4px 15px rgba(0,0,0,0.08);">
            <div style="display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap;">
                <div>
                    <h2 style="margin: 0; color: white; font-size: 24px; font-weight: 700;">🐾 Painel de Gestão SitiPet</h2>
                    <p style="margin: 4px 0 0 0; color: #cbd5e1; font-size: 14px;">Visão em tempo real da agenda, banho e tosa, hotelzinho, finanças e pós-venda.</p>
                </div>
                <div style="text-align: right; margin-top: 8px;">
                    <span style="background: rgba(255,255,255,0.15); padding: 6px 14px; border-radius: 20px; font-size: 13px; font-weight: 600;">
                        📅 Hoje: {hoje_fmt}
                    </span>
                </div>
            </div>
        </div>
    """, unsafe_allow_html=True)

    col1, col2, col3, col4 = st.columns(4)

    with col1:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #3b82f6;">
                <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">📅 Atendimentos Hoje</div>
                <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin: 4px 0;">{qtd_atendimentos_hoje}</div>
                <div style="font-size: 12px; color: #10b981; font-weight: 600;">✅ {qtd_finalizados_hoje} concluído(s)</div>
            </div>
        """, unsafe_allow_html=True)

    with col2:
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #f59e0b;">
                <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">🏨 Cães no Hotel Agora</div>
                <div style="font-size: 28px; font-weight: 800; color: #1e293b; margin: 4px 0;">{qtd_hospedados_agora}</div>
                <div style="font-size: 12px; color: #64748b; font-weight: 600;">🐾 Animais hospedados</div>
            </div>
        """, unsafe_allow_html=True)

    with col3:
        cor_lmb = "#ef4444" if len(lembretes_pendentes) > 0 else "#10b981"
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #d82678;">
                <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">🔔 Lembretes de Retorno</div>
                <div style="font-size: 28px; font-weight: 800; color: {cor_lmb}; margin: 4px 0;">{len(lembretes_pendentes)}</div>
                <div style="font-size: 12px; color: #64748b; font-weight: 600;">Pets para contatar hoje</div>
            </div>
        """, unsafe_allow_html=True)

    with col4:
        saldo_cor = "#10b981" if metricas_mes['saldo'] >= 0 else "#ef4444"
        st.markdown(f"""
            <div class="kpi-card" style="border-left: 5px solid #10b981;">
                <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">💵 Saldo em Caixa (Mês)</div>
                <div style="font-size: 24px; font-weight: 800; color: {saldo_cor}; margin: 4px 0;">{formatar_moeda(metricas_mes['saldo'])}</div>
                <div style="font-size: 12px; color: #64748b;">Resultado do período</div>
            </div>
        """, unsafe_allow_html=True)

    st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

    # ==================== CENTRAL DE LEMBRETES DE RETORNO ====================
    if lembretes_pendentes:
        st.markdown(f"### 🔔 Alerta de Retorno para Banho ({len(lembretes_pendentes)} pets para contato)")
        st.caption("Os pets abaixo atingiram o prazo de retorno configurado (8, 15 ou 30 dias). Envie uma mensagem rápida no WhatsApp!")
        
        for r_lmb, inf_lmb in lembretes_pendentes:
            id_l = r_lmb.get("id")
            pet_l = r_lmb.get("pet_nome")
            tut_l = r_lmb.get("tutor_nome")
            tel_l = r_lmb.get("tutor_telefone")
            ult_dt_l = r_lmb.get("data")
            dias_l = int(r_lmb.get("lembrete_dias", 15))
            
            with st.container():
                st.markdown(f"""
                    <div style="background: white; border-radius: 10px; padding: 12px 18px; margin-bottom: 8px; border-left: 5px solid {inf_lmb['cor']}; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                        <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                            <div>
                                <span style="font-size: 16px; font-weight: 800; color: #1e293b;">🐕 {pet_l}</span>
                                <span style="color: #64748b; font-size: 13px;"> (Tutor: <b>{tut_l}</b> - {tel_l})</span>
                            </div>
                            <span style="background: {inf_lmb['cor']}20; color: {inf_lmb['cor']}; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 12px;">
                                {inf_lmb['icon']} {inf_lmb['mensagem']}
                            </span>
                        </div>
                        <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                            📅 Último banho em <b>{format_date_br(ult_dt_l)}</b> (Ciclo de {dias_l} dias)
                        </div>
                    </div>
                """, unsafe_allow_html=True)
                
                col_w1, col_w2 = st.columns([3, 1])
                with col_w1:
                    wa_lmb_link = format_whatsapp_lembrete_banho(tel_l, tut_l, pet_l, dias_l, ult_dt_l)
                    if wa_lmb_link:
                        st.link_button(f"💬 Enviar Lembrete no WhatsApp de {tut_l}", wa_lmb_link, use_container_width=True)
                with col_w2:
                    if st.button("✅ Marcar Contatado", key=f"dash_cnt_{id_l}", use_container_width=True):
                        update_record("Banho_Tosa", id_l, {"lembrete_status": "Contatado"})
                        st.rerun()

    # ==================== SEÇÃO DE ALERTAS DE HORÁRIO DA AGENDA ====================
    alertas_atendimento = []
    if not df_agenda_hoje.empty:
        for _, row in df_agenda_hoje.iterrows():
            st_alerta = calcular_status_alerta_horario(row.get("data"), row.get("horario"), row.get("status"))
            if st_alerta.get("is_atrasado") or st_alerta.get("is_em_breve"):
                alertas_atendimento.append({
                    "pet": row.get("pet_nome"),
                    "tutor": row.get("tutor_nome"),
                    "horario": row.get("horario"),
                    "servicos": row.get("servicos"),
                    "alerta": st_alerta
                })

    saidas_hoje = []
    if not df_hosp_ativos.empty and "data_saida" in df_hosp_ativos.columns:
        for _, row in df_hosp_ativos.iterrows():
            if str(row.get("data_saida")) == hoje:
                saidas_hoje.append(row)

    if alertas_atendimento or saidas_hoje:
        st.markdown("### 🔔 Alertas de Horário e Check-outs de Hoje")
        for al in alertas_atendimento:
            al_info = al["alerta"]
            tipo_box = st.error if al_info["is_atrasado"] else st.warning
            tipo_box(
                f"**{al_info['icon']} {al_info['badge_label']} ({al['horario']}):** "
                f"Pet **{al['pet']}** (Tutor: {al['tutor']}) - *{al['servicos']}*. {al_info['mensagem']}"
            )
        for s in saidas_hoje:
            st.info(f"🏨 **Check-out de Hotel Hoje:** Pet **{s.get('pet_nome')}** (Tutor: {s.get('tutor_nome')}) tem previsão de saída hoje! Diárias: {s.get('diarias', 1)}.")

    # ==================== VISÃO RÁPIDA DAS ATIVIDADES ====================
    col_ag, col_hp = st.columns([3, 2])

    with col_ag:
        st.markdown("### 📋 Compromissos de Hoje na Agenda")
        if not df_agenda_hoje.empty:
            df_agenda_hoje_sorted = df_agenda_hoje.sort_values(by="horario")
            
            for _, r in df_agenda_hoje_sorted.iterrows():
                alerta = calcular_status_alerta_horario(r.get("data"), r.get("horario"), r.get("status"))
                cor_status = alerta["cor"]
                
                st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 14px 18px; margin-bottom: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); border-left: 5px solid {cor_status};">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <div>
                                <span style="font-size: 16px; font-weight: 700; color: #1e293b;">⏰ {r.get('horario')} - 🐶 {r.get('pet_nome')}</span>
                                <span style="color: #64748b; font-size: 13px;"> (Tutor: {r.get('tutor_nome')})</span>
                            </div>
                            <span style="background: {cor_status}20; color: {cor_status}; padding: 3px 10px; border-radius: 12px; font-weight: 600; font-size: 12px;">
                                {alerta['icon']} {r.get('status')}
                            </span>
                        </div>
                        <div style="margin-top: 6px; font-size: 13px; color: #475569;">
                            ✂️ <b>Serviços:</b> {r.get('servicos')} | 💵 <b>Valor:</b> {formatar_moeda(r.get('valor_total'))}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum compromisso agendado para hoje. Utilize a aba **Agenda** para cadastrar.")

    with col_hp:
        st.markdown("### 🏨 Hóspedes no Hotelzinho")
        if not df_hosp_ativos.empty:
            for _, r in df_hosp_ativos.iterrows():
                st.markdown(f"""
                    <div style="background: white; border-radius: 12px; padding: 14px 16px; margin-bottom: 10px; box-shadow: 0 2px 6px rgba(0,0,0,0.04); border-left: 5px solid #f59e0b;">
                        <div style="font-weight: 700; font-size: 15px; color: #1e293b;">🐕 {r.get('pet_nome')}</div>
                        <div style="font-size: 12px; color: #64748b; margin-top: 2px;">Tutor: {r.get('tutor_nome')} | Tel: {r.get('tutor_telefone')}</div>
                        <div style="font-size: 12px; color: #334155; margin-top: 4px;">
                            📅 Entrada: <b>{format_date_br(r.get('data_entrada'))}</b> | Saída: <b>{format_date_br(r.get('data_saida'))}</b>
                        </div>
                        <div style="font-size: 11px; color: #64748b; margin-top: 4px; background: #f8fafc; padding: 4px 8px; border-radius: 6px;">
                            🥣 <b>Alimentação:</b> {r.get('alimentacao', 'Normal')}
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhum cão hospedado no momento. Cadastre entradas na aba **Hospedagem**.")
