"""
Visão: Aba 3 – Hospedagem / Hotelzinho - SitiPet
Controle de check-in, check-out, cálculo de diárias, edição e exclusão completas em todas as abas,
e integração financeira automática em tempo real com o Fluxo de Caixa.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date, timedelta
import uuid
from utils.storage import (
    load_table, insert_record, update_record, delete_record,
    concluir_hospedagem, lancar_ou_atualizar_hospedagem_caixa,
    verificar_hospedagem_no_caixa, excluir_hospedagem_e_caixa
)
from utils.datas import get_today_date, get_today_date_str, format_date_br, calc_dias_hospedagem, parse_date
from utils.financeiro import formatar_moeda
from utils.comprovante import renderizar_modal_comprovante

def render_hospedagem():
    st.markdown("## 🏨 Aba 3 – Hospedagem / Hotelzinho SitiPet")
    st.markdown("Gestão de estadias, edição e exclusão de registros, diárias automáticas (R$ 80,00), emissão de recibos e integração financeira com o Caixa.")

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

        col_f1, col_f2, col_f3 = st.columns([2, 2, 2])
        with col_f1:
            forma_pag = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pendente / Check-out"], key="hsp_formapag")
        with col_f2:
            status_inicial = st.selectbox("Status da Hospedagem", ["Hospedado", "Reservado", "Concluído"], key="hsp_status")
        with col_f3:
            lancar_no_caixa_inicial = st.checkbox("💰 Lançar no Fluxo de Caixa agora", value=True, help="Registra imediatamente a receita de hospedagem no Caixa.")

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

                # Integração com o Caixa
                if lancar_no_caixa_inicial and valor_total_calc > 0 and forma_pag != "Pendente / Check-out":
                    desc_cx = f"Hospedagem {pet_nome.strip()} ({diarias_calc} diárias) - Tutor: {tutor_nome.strip()}"
                    obs_cx = f"Entrada: {format_date_br(data_entrada)} | Saída: {format_date_br(data_saida)}"
                    lancar_ou_atualizar_hospedagem_caixa(hosp_id, valor_total_calc, forma_pag, desc_cx, observacao=obs_cx)

                st.success(f"✅ Hospedagem de **{pet_nome}** registrada com sucesso! Total: **{formatar_moeda(valor_total_calc)}** ({diarias_calc} diárias).")
                st.rerun()

    # ==================== PAINEL DE VISUALIZAÇÃO EM ABAS ====================
    st.markdown("---")
    tab_ativos, tab_historico = st.tabs([
        "🏨 **Animais Atualmente Hospedados**",
        "📋 **Histórico Geral de Hospedagens & Edição**"
    ])

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
                    pet = row.get("pet_nome", "")
                    tutor = row.get("tutor_nome", "")
                    tel = row.get("tutor_telefone", "")
                    dt_in = row.get("data_entrada", "")
                    dt_out = row.get("data_saida", "")
                    diarias = int(row.get("diarias", 1))
                    val_diaria = float(row.get("valor_diaria", 80.0))
                    val_tot = float(row.get("valor_total", 0.0))
                    forma_pag = row.get("forma_pagamento", "Pendente")
                    
                    # Status no Caixa
                    info_cx = verificar_hospedagem_no_caixa(h_id)
                    cx_badge = "🟢 <b>Caixa:</b> Lançado" if info_cx["lancado"] else "🟠 <b>Caixa:</b> Pendente de lançamento"

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
                                💰 <b>Total:</b> <span style="font-weight: 700; color: #10b981;">{formatar_moeda(val_tot)}</span> ({forma_pag}) &nbsp;|&nbsp;
                                <span style="font-size: 12px;">{cx_badge}</span>
                            </div>

                            <div style="background: #f8fafc; border-radius: 8px; padding: 10px 14px; margin-top: 10px; font-size: 12px; color: #475569; display: grid; grid-template-columns: 1fr 1fr; gap: 6px;">
                                <div>🥣 <b>Ração:</b> {row.get('alimentacao', 'Padrão')} ({row.get('refeicoes_dia', '2x/dia')})</div>
                                <div>💊 <b>Medicação:</b> {row.get('medicacao', 'Nenhuma')}</div>
                                <div>🐾 <b>Comportamento:</b> {row.get('comportamento', 'Dócil')}</div>
                                <div>🚨 <b>Emergência:</b> {row.get('contato_emergencia', 'Não informado')}</div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    col_chk1, col_chk2, col_chk3, col_chk4, col_chk5 = st.columns([3, 2, 2, 2, 1])
                    
                    # 1. CHECK-OUT
                    with col_chk1:
                        with st.popover(f"🏁 Check-out {pet}", use_container_width=True):
                            st.markdown(f"#### Check-out do Hóspede **{pet}**")
                            st.write(f"Valor Base ({diarias} diárias): **{formatar_moeda(val_tot)}**")
                            
                            val_extras = st.number_input("Adicionais / Consumo Extra (R$)", min_value=0.0, value=0.0, step=10.0, key=f"extra_{h_id}")
                            tot_final = val_tot + val_extras
                            st.markdown(f"**Valor Final:** <span style='color: #10b981; font-size: 18px; font-weight: 800;'>{formatar_moeda(tot_final)}</span>", unsafe_allow_html=True)
                            
                            fp_out = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"], key=f"fp_out_{h_id}")
                            
                            if st.button("Confirmar Check-out & Lançar no Caixa", key=f"btn_out_{h_id}", type="primary"):
                                concluir_hospedagem(h_id, forma_pagamento=fp_out, valor_adicionais=val_extras)
                                st.success(f"Check-out de {pet} concluído e lançado no Caixa!")
                                st.rerun()

                    # 2. EDITAR HOSPEDAGEM (HÓSPEDES ATUAIS)
                    with col_chk2:
                        with st.popover("✏️ Editar", use_container_width=True):
                            st.markdown(f"#### ✏️ Editar Hospedagem: **{pet}**")
                            eh_pet = st.text_input("Nome do Pet", value=str(pet), key=f"eh_pet_{h_id}")
                            eh_tutor = st.text_input("Nome do Tutor", value=str(tutor), key=f"eh_tut_{h_id}")
                            eh_tel = st.text_input("Telefone", value=str(tel), key=f"eh_tel_{h_id}")
                            
                            col_eh1, col_eh2 = st.columns(2)
                            with col_eh1:
                                eh_dt_in = st.date_input("Data Entrada", value=parse_date(dt_in), key=f"eh_dtin_{h_id}")
                            with col_eh2:
                                eh_dt_out = st.date_input("Data Saída", value=parse_date(dt_out), key=f"eh_dtout_{h_id}")

                            eh_diarias_calc = calc_dias_hospedagem(eh_dt_in, eh_dt_out)
                            
                            col_eh3, col_eh4 = st.columns(2)
                            with col_eh3:
                                eh_val_dia = st.number_input("Valor Diária (R$)", min_value=0.0, value=float(val_diaria), step=5.0, key=f"eh_vdia_{h_id}")
                            with col_eh4:
                                st_lista = ["Hospedado", "Reservado", "Concluído"]
                                eh_st_idx = st_lista.index(row.get("status", "Hospedado")) if row.get("status") in st_lista else 0
                                eh_st = st.selectbox("Status", st_lista, index=eh_st_idx, key=f"eh_st_{h_id}")

                            eh_tot_calc = float(eh_diarias_calc * eh_val_dia)
                            eh_fp = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pendente / Check-out"], key=f"eh_fp_{h_id}")
                            
                            eh_sync_cx = st.checkbox("💰 Atualizar / Sincronizar no Caixa", value=True, key=f"eh_sync_cx_{h_id}")

                            eh_alim = st.text_input("Alimentação / Ração", value=str(row.get("alimentacao", "")), key=f"eh_alim_{h_id}")
                            eh_med = st.text_input("Medicação", value=str(row.get("medicacao", "")), key=f"eh_med_{h_id}")
                            eh_comp = st.text_input("Comportamento", value=str(row.get("comportamento", "")), key=f"eh_comp_{h_id}")
                            eh_emerg = st.text_input("Contato Emergência", value=str(row.get("contato_emergencia", "")), key=f"eh_em_{h_id}")
                            eh_obs = st.text_input("Observações", value=str(row.get("observacoes", "")), key=f"eh_obs_{h_id}")

                            if st.button("💾 Salvar Alterações", key=f"btn_save_eh_{h_id}", type="primary"):
                                update_record("Hospedagem", h_id, {
                                    "pet_nome": eh_pet.strip(),
                                    "tutor_nome": eh_tutor.strip(),
                                    "tutor_telefone": eh_tel.strip(),
                                    "data_entrada": eh_dt_in.strftime("%Y-%m-%d"),
                                    "data_saida": eh_dt_out.strftime("%Y-%m-%d"),
                                    "diarias": int(eh_diarias_calc),
                                    "valor_diaria": float(eh_val_dia),
                                    "valor_total": float(eh_tot_calc),
                                    "forma_pagamento": eh_fp,
                                    "status": eh_st,
                                    "alimentacao": eh_alim.strip(),
                                    "medicacao": eh_med.strip(),
                                    "comportamento": eh_comp.strip(),
                                    "contato_emergencia": eh_emerg.strip(),
                                    "observacoes": eh_obs.strip()
                                })
                                if eh_sync_cx and eh_tot_calc > 0 and eh_fp != "Pendente / Check-out":
                                    desc_sync = f"Hospedagem {eh_pet.strip()} ({eh_diarias_calc} diárias) - Tutor: {eh_tutor.strip()}"
                                    lancar_ou_atualizar_hospedagem_caixa(h_id, eh_tot_calc, eh_fp, desc_sync)
                                st.success("Hospedagem atualizada com sucesso!")
                                st.rerun()

                    # 3. LANÇAR NO CAIXA (DIRETO)
                    with col_chk3:
                        with st.popover("💰 Caixa", use_container_width=True):
                            st.markdown(f"**Lançar Hospedagem no Caixa**")
                            st.write(f"Pet: **{pet}** | Valor: **{formatar_moeda(val_tot)}**")
                            cx_fp_dir = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"], key=f"cxfp_dir_{h_id}")
                            if st.button("Confirmar Lançamento no Caixa", key=f"btn_cxfp_dir_{h_id}", type="primary"):
                                desc_d = f"Hospedagem {pet} ({diarias} diárias) - Tutor: {tutor}"
                                lancar_ou_atualizar_hospedagem_caixa(h_id, val_tot, cx_fp_dir, desc_d)
                                st.success("Lançamento efetuado no Caixa com sucesso!")
                                st.rerun()

                    # 4. RECIBO
                    with col_chk4:
                        with st.popover("🖨️ Recibo", use_container_width=True):
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

                    # 5. EXCLUIR HOSPEDAGEM (HÓSPEDES ATUAIS)
                    with col_chk5:
                        with st.popover("🗑️", use_container_width=True):
                            st.warning(f"Excluir hospedagem de **{pet}**?")
                            del_cx_check = st.checkbox("Excluir também do Caixa", value=True, key=f"del_cx_chk_{h_id}")
                            if st.button("Sim, Excluir", key=f"btn_conf_del_{h_id}", type="secondary"):
                                excluir_hospedagem_e_caixa(h_id, excluir_tambem_caixa=del_cx_check)
                                st.success("Hospedagem excluída.")
                                st.rerun()

    # ------------------ TAB 2: HISTÓRICO GERAL COM EDIÇÃO E EXCLUSÃO COMPLETAS ------------------
    with tab_historico:
        st.markdown("### 📋 Todas as Estadias e Reservas")
        st.caption("Consulte o histórico completo, edite dados, sincronize com o Caixa ou exclua estadias antigas.")
        
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
            st.caption(f"Mostrando **{len(df_h_show)}** estadia(s)")
            
            for _, r in df_h_show.iterrows():
                h_id_h = r.get("id")
                pet_h = r.get("pet_nome", "")
                tut_h = r.get("tutor_nome", "")
                tel_h = r.get("tutor_telefone", "")
                dt_in_h = r.get("data_entrada", "")
                dt_out_h = r.get("data_saida", "")
                diarias_h = int(r.get("diarias", 1))
                val_dia_h = float(r.get("valor_diaria", 80.0))
                val_tot_h = float(r.get("valor_total", 0.0))
                fp_h = r.get("forma_pagamento", "Pix")
                status_h = r.get("status", "Hospedado")

                # Info no Caixa
                info_cxh = verificar_hospedagem_no_caixa(h_id_h)
                cx_badge_h = "🟢 <b>Caixa:</b> Lançado" if info_cxh["lancado"] else "🟠 <b>Caixa:</b> Não lançado"
                st_cor = "#10b981" if status_h == "Concluído" else "#f59e0b" if status_h == "Hospedado" else "#64748b"
                
                with st.container():
                    st.markdown(f"""
                        <div style="background: white; border-radius: 12px; padding: 14px 18px; margin-bottom: 10px; border-left: 5px solid {st_cor}; box-shadow: 0 2px 6px rgba(0,0,0,0.04);">
                            <div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap;">
                                <div>
                                    <span style="font-size: 16px; font-weight: 800; color: #1e293b;">🐕 {pet_h}</span>
                                    <span style="color: #64748b; font-size: 13px;"> | Tutor: <b>{tut_h}</b> ({tel_h})</span>
                                </div>
                                <div>
                                    <span style="background: {st_cor}20; color: {st_cor}; padding: 3px 10px; border-radius: 12px; font-weight: 700; font-size: 12px;">
                                        {status_h} • {diarias_h} diária(s)
                                    </span>
                                </div>
                            </div>
                            <div style="font-size: 13px; color: #334155; margin-top: 6px;">
                                📅 <b>Período:</b> {format_date_br(dt_in_h)} até {format_date_br(dt_out_h)} &nbsp;|&nbsp; 
                                💵 <b>Diária:</b> {formatar_moeda(val_dia_h)} &nbsp;|&nbsp; 
                                💰 <b>Total:</b> <span style="font-weight: 700; color: #10b981;">{formatar_moeda(val_tot_h)}</span> ({fp_h}) &nbsp;|&nbsp; 
                                <span style="font-size: 12px;">{cx_badge_h}</span>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    col_hb1, col_hb2, col_hb3, col_hb4 = st.columns([2, 2, 2, 1])

                    # 1. EDITAR NO HISTÓRICO
                    with col_hb1:
                        with st.popover("✏️ Editar Estadia", use_container_width=True):
                            st.markdown(f"#### ✏️ Editar Estadia: **{pet_h}**")
                            eh_pet_t = st.text_input("Nome do Pet", value=str(pet_h), key=f"eht_pet_{h_id_h}")
                            eh_tut_t = st.text_input("Nome do Tutor", value=str(tut_h), key=f"eht_tut_{h_id_h}")
                            eh_tel_t = st.text_input("Telefone", value=str(tel_h), key=f"eht_tel_{h_id_h}")
                            
                            col_eht1, col_eht2 = st.columns(2)
                            with col_eht1:
                                eh_dtin_t = st.date_input("Data Entrada", value=parse_date(dt_in_h), key=f"eht_dtin_{h_id_h}")
                            with col_eht2:
                                eh_dtout_t = st.date_input("Data Saída", value=parse_date(dt_out_h), key=f"eht_dtout_{h_id_h}")

                            eh_dias_calc_t = calc_dias_hospedagem(eh_dtin_t, eh_dtout_t)
                            
                            col_eht3, col_eht4 = st.columns(2)
                            with col_eht3:
                                eh_vdia_t = st.number_input("Valor Diária (R$)", min_value=0.0, value=float(val_dia_h), step=5.0, key=f"eht_vdia_{h_id_h}")
                            with col_eht4:
                                st_list = ["Hospedado", "Reservado", "Concluído"]
                                eh_st_idx_t = st_list.index(status_h) if status_h in st_list else 0
                                eh_st_t = st.selectbox("Status", st_list, index=eh_st_idx_t, key=f"eht_st_{h_id_h}")

                            eh_tot_t = float(eh_dias_calc_t * eh_vdia_t)
                            eh_fp_t = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Pendente"], key=f"eht_fp_{h_id_h}")
                            eh_sync_cxt = st.checkbox("💰 Atualizar / Sincronizar no Caixa", value=True, key=f"eht_synccx_{h_id_h}")

                            eh_obs_t = st.text_input("Observações", value=str(r.get("observacoes", "")), key=f"eht_obs_{h_id_h}")

                            if st.button("💾 Salvar Alterações", key=f"btn_save_eht_{h_id_h}", type="primary"):
                                update_record("Hospedagem", h_id_h, {
                                    "pet_nome": eh_pet_t.strip(),
                                    "tutor_nome": eh_tut_t.strip(),
                                    "tutor_telefone": eh_tel_t.strip(),
                                    "data_entrada": eh_dtin_t.strftime("%Y-%m-%d"),
                                    "data_saida": eh_dtout_t.strftime("%Y-%m-%d"),
                                    "diarias": int(eh_dias_calc_t),
                                    "valor_diaria": float(eh_vdia_t),
                                    "valor_total": float(eh_tot_t),
                                    "forma_pagamento": eh_fp_t,
                                    "status": eh_st_t,
                                    "observacoes": eh_obs_t.strip()
                                })
                                if eh_sync_cxt and eh_tot_t > 0:
                                    desc_t = f"Hospedagem {eh_pet_t.strip()} ({eh_dias_calc_t} diárias) - Tutor: {eh_tut_t.strip()}"
                                    lancar_ou_atualizar_hospedagem_caixa(h_id_h, eh_tot_t, eh_fp_t, desc_t)
                                st.success("Estadia atualizada com sucesso!")
                                st.rerun()

                    # 2. LANÇAR / SINCRONIZAR NO CAIXA
                    with col_hb2:
                        with st.popover("💰 Lançar no Caixa", use_container_width=True):
                            st.markdown(f"**Lançar no Fluxo de Caixa**")
                            st.write(f"Pet: **{pet_h}** | Valor: **{formatar_moeda(val_tot_h)}**")
                            fp_lan_t = st.selectbox("Forma de Pagamento", ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro"], key=f"fplan_t_{h_id_h}")
                            if st.button("Confirmar Lançamento no Caixa", key=f"btn_lan_cxt_{h_id_h}", type="primary"):
                                desc_lt = f"Hospedagem {pet_h} ({diarias_h} diárias) - Tutor: {tut_h}"
                                lancar_ou_atualizar_hospedagem_caixa(h_id_h, val_tot_h, fp_lan_t, desc_lt)
                                st.success("Receita de hospedagem registrada no Caixa!")
                                st.rerun()

                    # 3. RECIBO
                    with col_hb3:
                        with st.popover("🖨️ Recibo", use_container_width=True):
                            renderizar_modal_comprovante(
                                titulo="Recibo de Hospedagem / Hotelzinho",
                                cliente_nome=tut_h,
                                cliente_telefone=tel_h,
                                pet_nome=pet_h,
                                profissional="Equipe SitiPet",
                                data_servico=dt_in_h,
                                itens=[
                                    {"nome": f"Diárias Hotelzinho ({diarias_h} diárias x {formatar_moeda(val_dia_h)})", "valor": val_tot_h}
                                ],
                                valor_total=val_tot_h,
                                forma_pagamento=fp_h,
                                observacoes=f"Entrada: {format_date_br(dt_in_h)} | Saída: {format_date_br(dt_out_h)}",
                                codigo_recibo=str(h_id_h)
                            )

                    # 4. EXCLUIR NO HISTÓRICO
                    with col_hb4:
                        with st.popover("🗑️", use_container_width=True):
                            st.warning(f"Excluir estadia de **{pet_h}**?")
                            del_cxt_chk = st.checkbox("Excluir também do Caixa", value=True, key=f"del_cxt_chk_{h_id_h}")
                            if st.button("Sim, Excluir", key=f"btn_conf_delh_{h_id_h}", type="secondary"):
                                excluir_hospedagem_e_caixa(h_id_h, excluir_tambem_caixa=del_cxt_chk)
                                st.success("Estadia excluída com sucesso.")
                                st.rerun()
        else:
            st.info("Nenhuma estadia no histórico.")
