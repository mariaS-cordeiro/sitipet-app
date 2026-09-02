"""
Visão: Aba 3 – Hospedagem / Hotelzinho - SitiPet
Controle de check-in, check-out, cálculo de diárias, ficha médica/comportamento e emissão de notas.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
from utils.storage import load_table, insert_record, update_record, delete_record, concluir_hospedagem
from utils.datas import get_today_date, get_today_date_str, format_date_br, calc_dias_hospedagem, parse_date
from utils.financeiro import formatar_moeda
from utils.comprovante import renderizar_modal_comprovante

def render_hospedagem():
    st.markdown("## 🏨 Aba 3 – Hospedagem / Hotelzinho SitiPet")
    st.markdown("Gestão de estadias, cálculo automático de diárias (R$ 80,00), controle de cuidados e recibos de hospedagem.")

    df_hosp = load_table("Hospedagem")
    preco_diaria_padrao = 80.0

    # ==================== FORMULÁRIO DE NOVA HOSPEDAGEM ====================
    with st.expander("➕ **Registrar Nova Hospedagem / Check-in**", expanded=False):
        st.markdown("#### 1. Identificação do Pet e Tutor")
        col1, col2, col3 = st.columns(3)
        with col1:
            pet_nome = st.text_input("🐶 Nome do Cachorro *", key="hsp_pet_nome", placeholder="Ex: Bob, Thor, Nina")
        with col2:
            tutor_nome = st.text_input("👤 Nome do Tutor *", key="hsp_tutor_nome", placeholder="Ex: Rafael Vasconcelos")
        with col3:
            tutor_telefone = st.text_input("📱 Telefone / WhatsApp", key="hsp_tutor_tel", placeholder="(11) 99999-8888")

        st.markdown("#### 2. Período e Valores")
        col_p1, col_p2, col_p3, col_p4 = st.columns(4)
        
        hoje = get_today_date()
        with col_p1:
            data_entrada = st.date_input("📅 Data de Entrada (Check-in) *", value=hoje, key="hsp_dt_in")
        with col_p2:
            data_saida = st.date_input("📅 Data de Saída (Check-out) *", value=hoje + timedelta(days=2), key="hsp_dt_out")

        # Cálculo automático de diárias
        diarias_calc = calc_dias_hospedagem(data_entrada, data_saida)
        
        with col_p3:
            valor_diaria = st.number_input("💵 Valor da Diária (R$)", min_value=0.0, value=float(preco_diaria_padrao), step=5.0, key="hsp_val_diaria")
        
        valor_total_calc = float(diarias_calc * valor_diaria)
        
        with col_p4:
            st.markdown(f"""
                <div style="background: #eff6ff; border: 1px solid #bfdbfe; border-radius: 8px; padding: 6px 12px; margin-top: 4px;">
                    <div style="font-size: 11px; color: #1e40af; font-weight: 600;">DIÁRIAS: <b>{diarias_calc}</b></div>
                    <div style="font-size: 14px; color: #1e3a8a; font-weight: 800;">TOTAL: {formatar_moeda(valor_total_calc)}</div>
                </div>
            """, unsafe_allow_html=True)

        col_f1, col_f2 = st.columns(2)
        with col_f1:
            forma_pag = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pagar no Check-out"], key="hsp_formapag")
        with col_f2:
            status_inicial = st.selectbox("Status da Hospedagem", ["Hospedado", "Reservado", "Concluído"], key="hsp_status")

        st.markdown("#### 3. Ficha de Cuidados & Informações Importantes")
        col_c1, col_c2 = st.columns(2)
        with col_c1:
            alimentacao = st.text_input("🥣 Alimentação (Tipo / Marca de Ração)", placeholder="Ex: Ração Premier Adulto", key="hsp_alim")
            refeicoes_dia = st.text_input("⏰ Quantidade de Refeições / Dia", placeholder="Ex: 2x ao dia (08:00 e 18:00)", key="hsp_ref")
            medicacao = st.text_input("💊 Medicação e Instruções", placeholder="Ex: Nenhum ou dosagem específica", key="hsp_med")
        
        with col_c2:
            comportamento = st.text_input("🐾 Comportamento / Temperamento", placeholder="Ex: Dócil, brinca bem com outros pets", key="hsp_comp")
            restricoes = st.text_input("⚠️ Restrições / Alergias", placeholder="Ex: Alergia a petisco de frango", key="hsp_rest")
            contato_emergencia = st.text_input("🚨 Contato de Emergência", placeholder="Ex: Dra. Camila Veterinária: (11) 98888-0000", key="hsp_emerg")

        observacoes = st.text_area("📝 Observações Gerais do Tutor", placeholder="Ex: Trouxe caminha e cobertor próprio...", key="hsp_obs")

        if st.button("💾 Confirmar Check-in / Salvar Hospedagem", type="primary", use_container_width=True):
            if not pet_nome or not tutor_nome:
                st.error("Por favor, preencha o Nome do Cachorro e o Nome do Tutor.")
            elif data_saida < data_entrada:
                st.error("A data de saída não pode ser anterior à data de entrada.")
            else:
                hosp_id = f"HSP-{str(uuid.uuid4())[:6].upper()}"
                novo_hosp = {
                    "id": hosp_id,
                    "pet_nome": pet_nome.strip(),
                    "tutor_nome": tutor_nome.strip(),
                    "tutor_telefone": tutor_telefone.strip(),
                    "data_entrada": data_entrada.strftime("%Y-%m-%d"),
                    "data_saida": data_saida.strftime("%Y-%m-%d"),
                    "diarias": int(diarias_calc),
                    "valor_diaria": float(valor_diaria),
                    "valor_total": float(valor_total_calc),
                    "forma_pagamento": forma_pag,
                    "status": status_inicial,
                    "alimentacao": alimentacao.strip(),
                    "refeicoes_dia": refeicoes_dia.strip(),
                    "medicacao": medicacao.strip() if medicacao else "Nenhuma",
                    "comportamento": comportamento.strip() if comportamento else "Dócil",
                    "restricoes": restricoes.strip() if restricoes else "Nenhuma",
                    "contato_emergencia": contato_emergencia.strip(),
                    "observacoes": observacoes.strip(),
                    "criado_em": get_today_date_str()
                }
                insert_record("Hospedagem", novo_hosp)
                st.success(f"✅ Hospedagem de **{pet_nome}** registrada com sucesso! Total: **{formatar_moeda(valor_total_calc)}** ({diarias_calc} diárias).")
                st.rerun()

    # ==================== PAINEL DE VISUALIZAÇÃO EM ABAS ====================
    st.markdown("---")
    tab_ativos, tab_historico = st.tabs(["🏨 **Animais Atualmente Hospedados**", "📚 **Histórico Geral de Hospedagens**"])

    hoje_str = get_today_date_str()
    d_hoje = date.today()

    # ------------------ TAB 1: ATUALMENTE HOSPEDADOS ------------------
    with tab_ativos:
        if df_hosp.empty:
            st.info("Nenhuma hospedagem cadastrada.")
        else:
            df_ativos = df_hosp[df_hosp["status"] == "Hospedado"].copy()
            
            if df_ativos.empty:
                st.success("🎉 Não há animais hospedados no momento. O hotelzinho está pronto para novos hóspedes!")
            else:
                st.markdown(f"### 🐾 Hóspedes Atuais ({len(df_ativos)} cães)")

                for _, row in df_ativos.iterrows():
                    h_id = row.get("id")
                    pet = row.get("pet_nome")
                    tutor = row.get("tutor_nome")
                    tel = row.get("tutor_telefone")
                    dt_in = row.get("data_entrada")
                    dt_out = row.get("data_saida")
                    diarias = int(row.get("diarias", 1))
                    val_diaria = float(row.get("valor_diaria", 80.0))
                    val_tot = float(row.get("valor_total", 0.0))
                    forma_pag = row.get("forma_pagamento", "Pendente")
                    
                    d_out_obj = parse_date(dt_out)
                    is_checkout_hoje = (d_out_obj == d_hoje)
                    is_checkout_atrasado = (d_out_obj < d_hoje)

                    cor_alerta = "#f59e0b"
                    badge_checkout = ""
                    if is_checkout_hoje:
                        cor_alerta = "#ef4444"
                        badge_checkout = "🚨 <b>CHECK-OUT PROGRAMADO PARA HOJE!</b>"
                    elif is_checkout_atrasado:
                        cor_alerta = "#b91c1c"
                        badge_checkout = "⚠️ <b>DATA DE SAÍDA VENCIDA!</b>"

                    st.markdown(f"""
                        <div style="background: white; border-radius: 14px; padding: 18px 22px; margin-bottom: 15px; border-left: 6px solid {cor_alerta}; box-shadow: 0 3px 10px rgba(0,0,0,0.05);">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <div>
                                    <span style="font-size: 19px; font-weight: 800; color: #1e293b;">🐕 {pet}</span>
                                    <span style="color: #64748b; font-size: 14px;"> | Tutor: <b>{tutor}</b> ({tel})</span>
                                </div>
                                <div>
                                    <span style="background: #eff6ff; color: #1d4ed8; padding: 4px 14px; border-radius: 20px; font-weight: 700; font-size: 13px;">
                                        🏨 Hospedado • {diarias} diária(s)
                                    </span>
                                </div>
                            </div>
                            
                            {f'<div style="color: #ef4444; margin-top: 6px; font-size: 13px;">{badge_checkout}</div>' if badge_checkout else ''}

                            <div style="margin-top: 10px; font-size: 13px; color: #334155; line-height: 1.6;">
                                📅 <b>Período:</b> {format_date_br(dt_in)} até <b>{format_date_br(dt_out)}</b> &nbsp;|&nbsp; 
                                💵 <b>Diária:</b> {formatar_moeda(val_diaria)} &nbsp;|&nbsp; 
                                💰 <b>Total Previsto:</b> <span style="font-weight: 700; color: #10b981;">{formatar_moeda(val_tot)}</span>
                            </div>

                            <div style="background: #f8fafc; border-radius: 8px; padding: 10px 14px; margin-top: 10px; font-size: 12px; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                                <div>🥣 <b>Ração:</b> {row.get('alimentacao', 'Padrão')} ({row.get('refeicoes_dia', '2x/dia')})</div>
                                <div>💊 <b>Medicação:</b> {row.get('medicacao', 'Nenhuma')}</div>
                                <div>🐾 <b>Comportamento:</b> {row.get('comportamento', 'Dócil')}</div>
                                <div>🚨 <b>Emergência:</b> {row.get('contato_emergencia', 'Não informado')}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    col_chk1, col_chk2, col_chk3 = st.columns([3, 2, 1])
                    with col_chk1:
                        with st.popover(f"🏁 **Realizar Check-out de {pet}**", use_container_width=True):
                            st.markdown(f"#### Check-out do Hóspede {pet}")
                            st.write(f"Valor Base ({diarias} diárias): **{formatar_moeda(val_tot)}**")
                            
                            val_extras = st.number_input("Adicionais / Consumo Extra (R$)", min_value=0.0, value=0.0, step=10.0, key=f"extra_{h_id}")
                            tot_final = val_tot + val_extras
                            st.markdown(f"**Valor Final a Cobrar:** <span style='color: #10b981; font-size: 18px; font-weight: 800;'>{formatar_moeda(tot_final)}</span>", unsafe_allow_html=True)
                            
                            fp = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"], key=f"fp_out_{h_id}")
                            
                            if st.button("Confirmar Check-out & Lançar no Caixa", key=f"btn_out_{h_id}", type="primary"):
                                concluir_hospedagem(h_id, forma_pagamento=fp, valor_adicionais=val_extras)
                                st.success(f"Check-out de {pet} concluído com sucesso e lançado no Caixa!")
                                st.rerun()

                    with col_chk2:
                        with st.popover("🖨️ Recibo de Hotel", use_container_width=True):
                            renderizar_modal_comprovante(
                                titulo="Recibo de Hospedagem / Hotelzinho",
                                cliente_nome=tutor,
                                cliente_telefone=tel,
                                pet_nome=pet,
                                profissional="Equipe SitiPet",
                                data_servico=dt_in,
                                itens=[
                                    {"nome": f"Diárias Hotelzinho ({diarias} diárias x {formatar_moeda(val_diaria)})", "valor": val_tot}
                                ],
                                valor_total=val_tot,
                                forma_pagamento=forma_pag,
                                observacoes=f"Entrada: {format_date_br(dt_in)} | Previsão Saída: {format_date_br(dt_out)}",
                                codigo_recibo=str(h_id)
                            )

                    with col_chk3:
                        if st.button("🗑️", key=f"del_hsp_{h_id}"):
                            delete_record("Hospedagem", h_id)
                            st.rerun()

    # ------------------ TAB 2: HISTÓRICO GERAL ------------------
    with tab_historico:
        st.markdown("### 📋 Todas as Estadias e Reservas")
        
        if not df_hosp.empty:
            col_hf1, col_hf2 = st.columns([3, 2])
            with col_hf1:
                busca_h = st.text_input("🔍 Buscar Hóspede ou Tutor", placeholder="Digite o nome do pet...", key="busca_h_tab")
            with col_hf2:
                st_filtro = st.selectbox("Status da Estadia", ["Todos", "Hospedado", "Concluído", "Reservado"], key="st_filtro_h")

            df_h_show = df_hosp.copy()
            if busca_h:
                b_low = busca_h.lower()
                df_h_show = df_h_show[
                    df_h_show["pet_nome"].astype(str).str.lower().str.contains(b_low) |
                    df_h_show["tutor_nome"].astype(str).str.lower().str.contains(b_low)
                ]
            if st_filtro != "Todos":
                df_h_show = df_h_show[df_h_show["status"] == st_filtro]

            df_h_show = df_h_show.sort_values(by="data_entrada", ascending=False)
            st.caption(f"Mostrando **{len(df_h_show)}** registro(s)")
            
            for _, r in df_h_show.iterrows():
                h_id = r.get("id")
                st_cor = "#10b981" if r.get("status") == "Concluído" else "#f59e0b" if r.get("status") == "Hospedado" else "#64748b"
                
                st.markdown(f"""
                    <div style="background: white; border-radius: 10px; padding: 12px 18px; margin-bottom: 8px; border-left: 4px solid {st_cor}; box-shadow: 0 1px 5px rgba(0,0,0,0.03);">
                        <div style="display: flex; justify-content: space-between; align-items: center;">
                            <b>🐕 {r.get('pet_nome')}</b> (Tutor: {r.get('tutor_nome')})
                            <span style="font-weight: 700; color: {st_cor};">{r.get('status')}</span>
                        </div>
                        <div style="font-size: 12px; color: #475569; margin-top: 4px;">
                            📅 Entrada: {format_date_br(r.get('data_entrada'))} | Saída: {format_date_br(r.get('data_saida'))} | Diárias: {r.get('diarias')} | Total: <b>{formatar_moeda(r.get('valor_total'))}</b> ({r.get('forma_pagamento')})
                        </div>
                    </div>
                """, unsafe_allow_html=True)
        else:
            st.info("Nenhuma estadia no histórico.")
