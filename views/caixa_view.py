"""
Visão: Aba 4 – Caixa e Gestão Financeira - SitiPet
Fechamento de conta consolidado por cliente/pet, emissão exclusiva de cupons Epson TM-T20,
controle de entradas/saídas, métricas mensais e extrato.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
import io
from utils.storage import (
    load_table, insert_record, update_record, delete_record,
    obter_servicos_pendentes_pagamento, fechar_conta_cliente, PROFISSIONAIS
)
from utils.datas import (
    get_today_date, get_today_date_str, format_date_br, parse_date,
    get_meses_nomes, get_anos_disponiveis, mes_nome_para_numero, mes_numero_para_nome
)
from utils.financeiro import (
    formatar_moeda, calcular_metricas_financeiras,
    gerar_grafico_pizza_servicos, obter_servicos_destaque, filtrar_dataframe_por_periodo
)
from utils.comprovante import renderizar_modal_comprovante, extrair_itens_servicos

CATEGORIAS_ENTRADA = ["Fechamento de Conta", "Banho e Tosa", "Hospedagem", "Serviços Adicionais", "Venda de Produtos", "Outras Receitas"]
CATEGORIAS_SAIDA = ["Produtos e Materiais", "Shampoos e Cosméticos", "Manutenção e Equipamentos", "Pagamento de Pessoal", "Aluguel e Contas", "Despesas Administrativas", "Outros Gastos"]
FORMAS_PAGAMENTO = ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Boleto", "Outro"]

def render_caixa():
    st.markdown("## 💰 Aba 4 – Caixa, Fechamento de Contas & Finanças")
    st.markdown("Centralize o fechamento de contas dos clientes, emita cupons fiscais para impressora **Epson TM-T20** e gerencie o fluxo de caixa.")

    tab_pdv, tab_fluxo = st.tabs([
        "🧾 **Fechamento de Conta do Cliente & Emissão de Cupom (PDV)**",
        "📊 **Fluxo de Caixa, Despesas & Relatórios**"
    ])

    # ==================== TAB 1: FECHAMENTO DE CONTA & CUPOM EXCLUSIVO ====================
    with tab_pdv:
        st.markdown("### 🧾 Fechamento de Conta & Emissão de Cupom Fiscal")
        st.caption("Reúna todos os serviços realizados para o cliente (Banho, Tosa, Hospedagem e adicionais) em um único fechamento de conta. Após a confirmação, o sistema dá baixa automática nas pendências e gera o cupom formatado para **Epson TM-T20**.")

        # Buscar todos os clientes com serviços pendentes de pagamento
        pendencias_dict = obter_servicos_pendentes_pagamento()
        
        opcoes_clientes = []
        mapa_chaves = {}

        for chave, dados_p in pendencias_dict.items():
            tot_pend = sum(it["valor"] for it in dados_p["itens"])
            label = f"🐕 {dados_p['pet_nome']} | Tutor(a): {dados_p['tutor_nome']} ({len(dados_p['itens'])} item(ns) - {formatar_moeda(tot_pend)})"
            opcoes_clientes.append(label)
            mapa_chaves[label] = chave

        opcoes_selecao = ["➕ [Novo Fechamento Avulso / Outro Cliente]"] + opcoes_clientes

        col_fc1, col_fc2 = st.columns([1, 1], gap="large")

        with col_fc1:
            st.markdown("#### 1. Selecionar Cliente e Conferir Serviços")
            sel_cliente_opt = st.selectbox(
                "Selecione o Cliente / Pet com serviços pendentes:",
                opcoes_selecao,
                key="sel_cliente_fechamento"
            )

            dados_selecionados = {}
            if sel_cliente_opt != "➕ [Novo Fechamento Avulso / Outro Cliente]":
                chave_real = mapa_chaves.get(sel_cliente_opt)
                if chave_real:
                    dados_selecionados = pendencias_dict.get(chave_real, {})

            col_dp1, col_dp2 = st.columns(2)
            with col_dp1:
                fc_pet = st.text_input("🐶 Nome do Animal / Pet *", value=dados_selecionados.get("pet_nome", ""), placeholder="Ex: Thor, Mel, Bob", key="fc_pet_nome")
                fc_raca = st.text_input("Raça", value=dados_selecionados.get("raca", ""), placeholder="Ex: Shih-tzu, Poodle", key="fc_raca")
            with col_dp2:
                fc_tutor = st.text_input("👤 Nome do Cliente / Tutor *", value=dados_selecionados.get("tutor_nome", ""), placeholder="Ex: Mariana Silva", key="fc_tutor_nome")
                fc_tel = st.text_input("📱 Telefone / WhatsApp", value=dados_selecionados.get("tutor_telefone", ""), placeholder="(11) 98888-7777", key="fc_tel")

            col_dp3, col_dp4 = st.columns(2)
            with col_dp3:
                lista_portes = ["Pequeno", "Médio", "Grande", "Gigante"]
                porte_idx = lista_portes.index(dados_selecionados.get("porte", "Pequeno")) if dados_selecionados.get("porte") in lista_portes else 0
                fc_porte = st.selectbox("Porte", lista_portes, index=porte_idx, key="fc_porte")
            with col_dp4:
                prof_idx = PROFISSIONAIS.index(dados_selecionados.get("profissional")) if dados_selecionados.get("profissional") in PROFISSIONAIS else 0
                fc_prof = st.selectbox("Profissional / Atendente", PROFISSIONAIS, index=prof_idx, key="fc_prof")

            st.markdown("---")
            st.markdown("#### 2. Serviços e Produtos a Pagar")

            itens_pendentes_base = dados_selecionados.get("itens", [])
            itens_para_fechamento = []

            if itens_pendentes_base:
                st.markdown("**Serviços identificados no sistema para este pet:**")
                for idx_it, item_p in enumerate(itens_pendentes_base):
                    col_chk, col_desc, col_val = st.columns([1, 4, 2])
                    with col_chk:
                        st.write("")
                        st.write("")
                        usar_item = st.checkbox(f"#{idx_it+1}", value=True, key=f"chk_item_fech_{idx_it}_{item_p.get('origem_id')}")
                    with col_desc:
                        nome_editado = st.text_input(f"Descrição #{idx_it+1}", value=item_p.get("nome"), key=f"nome_item_fech_{idx_it}_{item_p.get('origem_id')}")
                    with col_val:
                        val_editado = st.number_input(f"Valor #{idx_it+1} (R$)", min_value=0.0, value=float(item_p.get("valor", 0.0)), step=5.0, key=f"val_item_fech_{idx_it}_{item_p.get('origem_id')}")

                    if usar_item and nome_editado.strip():
                        itens_para_fechamento.append({
                            "origem": item_p.get("origem"),
                            "origem_id": item_p.get("origem_id"),
                            "nome": nome_editado.strip(),
                            "valor": float(val_editado)
                        })
            else:
                st.info("Nenhum serviço pendente automático selecionado. Preencha os itens abaixo:")
                for i in range(3):
                    col_chk, col_desc, col_val = st.columns([1, 4, 2])
                    with col_chk:
                        st.write("")
                        st.write("")
                        usar_item = st.checkbox(f"#{i+1}", value=(i == 0), key=f"chk_item_avulso_{i}")
                    with col_desc:
                        nome_av = st.text_input(f"Descrição #{i+1}", value=f"Banho ({fc_porte})" if i == 0 else "", placeholder="Ex: Banho, Tosa, Ração...", key=f"nome_av_{i}")
                    with col_val:
                        val_av = st.number_input(f"Valor #{i+1} (R$)", min_value=0.0, value=50.0 if i == 0 else 0.0, step=5.0, key=f"val_av_{i}")

                    if usar_item and nome_av.strip():
                        itens_para_fechamento.append({
                            "origem": "Avulso",
                            "origem_id": "",
                            "nome": nome_av.strip(),
                            "valor": float(val_av)
                        })

            # Adicionar item extra avulso se desejar
            with st.expander("➕ Adicionar Produto / Serviço Extra na Conta", expanded=False):
                col_ex1, col_ex2 = st.columns([3, 2])
                with col_ex1:
                    extra_nome = st.text_input("Item Extra (Produto / Serviço)", placeholder="Ex: Gravatinha, Shampoo Especial, Petisco", key="fc_extra_n")
                with col_ex2:
                    extra_val = st.number_input("Valor do Extra (R$)", min_value=0.0, value=0.0, step=5.0, key="fc_extra_v")
                if extra_nome.strip() and extra_val > 0:
                    itens_para_fechamento.append({
                        "origem": "Extra",
                        "origem_id": "",
                        "nome": extra_nome.strip(),
                        "valor": float(extra_val)
                    })

            st.markdown("---")
            st.markdown("#### 3. Total, Desconto & Pagamento")

            subtotal_fc = sum(it["valor"] for it in itens_para_fechamento)

            col_pag1, col_pag2 = st.columns(2)
            with col_pag1:
                fc_desconto = st.number_input("Desconto (R$)", min_value=0.0, value=0.0, step=5.0, key="fc_desc")
            with col_pag2:
                fc_forma_pag = st.selectbox("Forma de Pagamento *", FORMAS_PAGAMENTO, key="fc_fp")

            total_final_fc = max(0.0, subtotal_fc - fc_desconto)

            fc_obs = st.text_input("Observações Adicionais", placeholder="Ex: Pago no balcão, cliente satisfeito", key="fc_obs_texto")

            st.markdown(f"""
                <div style="background: #f0fdf4; border: 2px solid #10b981; border-radius: 10px; padding: 12px 18px; margin: 15px 0; text-align: center;">
                    <div style="font-size: 13px; color: #166534; font-weight: 700;">TOTAL CONSOLIDADO A PAGAR</div>
                    <div style="font-size: 28px; font-weight: 900; color: #15803d;">{formatar_moeda(total_final_fc)}</div>
                    <div style="font-size: 12px; color: #4b5563;">Subtotal: {formatar_moeda(subtotal_fc)} | Desconto: - {formatar_moeda(fc_desconto)}</div>
                </div>
            """, unsafe_allow_html=True)

            if st.button("✅ Confirmar Pagamento & Fechar Conta", type="primary", use_container_width=True):
                if not fc_pet or not fc_tutor:
                    st.error("Por favor, preencha o Nome do Pet e o Nome do Cliente.")
                elif not itens_para_fechamento:
                    st.error("Selecione ou adicione pelo menos 1 serviço para fechar a conta.")
                else:
                    res_fech = fechar_conta_cliente(
                        cliente_nome=fc_tutor.strip(),
                        pet_nome=fc_pet.strip(),
                        tutor_telefone=fc_tel.strip(),
                        raca=fc_raca.strip(),
                        porte=fc_porte,
                        profissional=fc_prof,
                        itens_selecionados=itens_para_fechamento,
                        valor_total=total_final_fc,
                        forma_pagamento=fc_forma_pag,
                        desconto=fc_desconto,
                        observacoes=fc_obs.strip()
                    )
                    st.session_state["ultimo_recibo_gerado"] = res_fech
                    st.success(f"🎉 Conta de **{fc_pet}** fechada e lançada no Caixa com sucesso!")
                    st.rerun()

        with col_fc2:
            st.markdown("#### 4. Visualização do Cupom (Epson TM-T20)")
            
            recibo_exibir = st.session_state.get("ultimo_recibo_gerado")
            
            if recibo_exibir:
                st.success("✅ **Conta Fechada com Sucesso!** Cupom pronto para impressão:")
                renderizar_modal_comprovante(
                    titulo="Comprovante de Pagamento",
                    cliente_nome=recibo_exibir["cliente_nome"],
                    cliente_telefone=recibo_exibir.get("tutor_telefone", ""),
                    pet_nome=recibo_exibir["pet_nome"],
                    raca=recibo_exibir.get("raca", ""),
                    porte=recibo_exibir.get("porte", ""),
                    profissional=recibo_exibir.get("profissional", ""),
                    data_servico=recibo_exibir.get("data_servico", get_today_date_str()),
                    itens=recibo_exibir["itens"],
                    valor_total=recibo_exibir["valor_total"],
                    forma_pagamento=recibo_exibir["forma_pagamento"],
                    observacoes=recibo_exibir.get("observacoes", ""),
                    codigo_recibo=recibo_exibir["recibo_id"],
                    desconto=recibo_exibir.get("desconto", 0.0)
                )
                if st.button("➕ Realizar Novo Fechamento de Conta", use_container_width=True):
                    st.session_state["ultimo_recibo_gerado"] = None
                    st.rerun()
            else:
                st.caption("Prévia ao vivo do cupom conforme os itens selecionados ao lado:")
                renderizar_modal_comprovante(
                    titulo="Comprovante de Pagamento",
                    cliente_nome=fc_tutor if fc_tutor else "Cliente SitiPet",
                    cliente_telefone=fc_tel,
                    pet_nome=fc_pet if fc_pet else "Pet",
                    raca=fc_raca,
                    porte=fc_porte,
                    profissional=fc_prof,
                    data_servico=get_today_date_str(),
                    itens=itens_para_fechamento,
                    valor_total=total_final_fc,
                    forma_pagamento=fc_forma_pag,
                    observacoes=fc_obs,
                    codigo_recibo="001",
                    desconto=fc_desconto
                )

    # ==================== TAB 2: FLUXO DE CAIXA, DESPESAS & RELATÓRIOS ====================
    with tab_fluxo:
        df_caixa = load_table("Caixa")
        df_bt = load_table("Banho_Tosa")
        df_hosp = load_table("Hospedagem")

        # Formulário de Lançamento Manual / Despesas
        with st.expander("➕ **Novo Lançamento Manual (Entrada / Despesa / Saída)**", expanded=False):
            with st.form("form_novo_lancamento", clear_on_submit=True):
                col_t1, col_t2, col_t3 = st.columns(3)
                with col_t1:
                    tipo_mov = st.selectbox("Tipo de Movimentação *", ["Saída", "Entrada", "Desconto"], key="cx_tipo")
                with col_t2:
                    if tipo_mov == "Entrada":
                        cat_opcoes = CATEGORIAS_ENTRADA
                    elif tipo_mov == "Saída":
                        cat_opcoes = CATEGORIAS_SAIDA
                    else:
                        cat_opcoes = ["Desconto Cliente / Promoção", "Ajuste de Valor"]
                    categoria = st.selectbox("Categoria *", cat_opcoes, key="cx_cat")
                with col_t3:
                    servico_rel = st.selectbox("Serviço Relacionado", ["Geral / Despesas", "Produtos e Materiais", "Banho e Tosa", "Hospedagem"], key="cx_serv_rel")

                col_d1, col_d2, col_d3 = st.columns(3)
                with col_d1:
                    data_lanc = st.date_input("📅 Data", value=get_today_date(), key="cx_data")
                with col_d2:
                    valor_lanc = st.number_input("💵 Valor (R$) *", min_value=0.01, value=50.0, step=5.0, key="cx_val")
                with col_d3:
                    forma_pag = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO, key="cx_fp")

                descricao = st.text_input("📝 Descrição do Lançamento *", placeholder="Ex: Compra Shampoos 5L, Manutenção Soprador...", key="cx_desc")
                observacao = st.text_input("Observação Adicional", placeholder="Ex: Fornecedor PetClean...", key="cx_obs")

                btn_salvar_cx = st.form_submit_button("💾 Salvar Lançamento no Caixa", type="primary", use_container_width=True)

                if btn_salvar_cx:
                    if not descricao:
                        st.error("Por favor, preencha a descrição do lançamento.")
                    else:
                        novo_cx = {
                            "id": f"CX-{str(uuid.uuid4())[:6].upper()}",
                            "data": data_lanc.strftime("%Y-%m-%d"),
                            "tipo": tipo_mov,
                            "categoria": categoria,
                            "servico_relacionado": servico_rel,
                            "descricao": descricao.strip(),
                            "valor": float(valor_lanc),
                            "forma_pagamento": forma_pag,
                            "referencia_id": "",
                            "observacao": observacao.strip(),
                            "criado_em": get_today_date_str()
                        }
                        insert_record("Caixa", novo_cx)
                        st.success(f"✅ Lançamento de **{formatar_moeda(valor_lanc)}** salvo com sucesso!")
                        st.rerun()

        # Filtros de Período
        st.markdown("---")
        st.markdown("### 📊 Análise Financeira & Extrato")
        
        hoje = date.today()
        meses_lista = get_meses_nomes()
        anos_lista = get_anos_disponiveis(2024, 2032)

        col_flt_m, col_flt_a, col_flt_all = st.columns([2, 2, 2])
        with col_flt_m:
            mes_selecionado_nome = st.selectbox("Mês:", meses_lista, index=hoje.month - 1, key="sel_mes_caixa")
            num_mes_sel = mes_nome_para_numero(mes_selecionado_nome)
        with col_flt_a:
            ano_selecionado = st.selectbox("Ano:", anos_lista, index=anos_lista.index(hoje.year) if hoje.year in anos_lista else 0, key="sel_ano_caixa")
        with col_flt_all:
            ver_todos_periodos = st.checkbox("🌐 Ver Todos os Períodos", value=False, key="chk_all_periodos")

        m_filtro = None if ver_todos_periodos else num_mes_sel
        a_filtro = None if ver_todos_periodos else ano_selecionado

        # Métricas
        metricas = calcular_metricas_financeiras(df_caixa, mes=m_filtro, ano=a_filtro)

        col1, col2, col3, col4 = st.columns(4)
        with col1:
            st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #10b981;">
                    <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">📥 Entradas</div>
                    <div style="font-size: 24px; font-weight: 800; color: #10b981; margin: 4px 0;">{formatar_moeda(metricas['total_entradas'])}</div>
                    <div style="font-size: 11px; color: #64748b;">Faturamento do período</div>
                </div>
            """, unsafe_allow_html=True)

        with col2:
            st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #ef4444;">
                    <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">📤 Saídas / Despesas</div>
                    <div style="font-size: 24px; font-weight: 800; color: #ef4444; margin: 4px 0;">{formatar_moeda(metricas['total_saidas'])}</div>
                    <div style="font-size: 11px; color: #64748b;">Despesas e compras</div>
                </div>
            """, unsafe_allow_html=True)

        with col3:
            st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #f59e0b;">
                    <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">🏷️ Descontos</div>
                    <div style="font-size: 24px; font-weight: 800; color: #f59e0b; margin: 4px 0;">{formatar_moeda(metricas['total_descontos'])}</div>
                    <div style="font-size: 11px; color: #64748b;">Promoções concedidas</div>
                </div>
            """, unsafe_allow_html=True)

        with col4:
            saldo_cor = "#10b981" if metricas['saldo'] >= 0 else "#ef4444"
            st.markdown(f"""
                <div class="kpi-card" style="border-left: 5px solid #24398e;">
                    <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">💎 Saldo Líquido</div>
                    <div style="font-size: 24px; font-weight: 800; color: {saldo_cor}; margin: 4px 0;">{formatar_moeda(metricas['saldo'])}</div>
                    <div style="font-size: 11px; color: #64748b;">Resultado do período</div>
                </div>
            """, unsafe_allow_html=True)

        st.markdown("<div style='height: 15px;'></div>", unsafe_allow_html=True)

        # Gráficos
        destaques = obter_servicos_destaque(df_caixa, df_bt, df_hosp, mes=m_filtro, ano=a_filtro)
        col_dest1, col_dest2 = st.columns(2)
        with col_dest1:
            st.markdown("#### 🥧 Distribuição de Receitas por Categoria")
            fig_pizza = gerar_grafico_pizza_servicos(destaques)
            st.plotly_chart(fig_pizza, use_container_width=True)

        with col_dest2:
            st.markdown("#### 🏆 Destaques Financeiros")
            st.markdown(f"""
                <div style="background: white; border-radius: 12px; padding: 18px; box-shadow: 0 2px 8px rgba(0,0,0,0.04); font-size: 14px; line-height: 1.8;">
                    🛁 <b>Banho e Tosa:</b> {formatar_moeda(destaques['total_banho_tosa'])} ({destaques['qtd_banho_tosa']} serviços)<br>
                    🏨 <b>Hospedagem / Hotel:</b> {formatar_moeda(destaques['total_hospedagem'])} ({destaques['qtd_hospedagens']} estadias)<br>
                    🛍️ <b>Produtos e Outros:</b> {formatar_moeda(destaques['total_outros'])}<br>
                    <hr style="margin: 10px 0;">
                    💰 <b>Ticket Médio Geral:</b> {formatar_moeda(destaques['ticket_medio'])}
                </div>
            """, unsafe_allow_html=True)

        # Extrato
        st.markdown("---")
        st.markdown("### 📋 Extrato de Lançamentos & Edição")

        df_filtrado_cx = filtrar_dataframe_por_periodo(df_caixa, data_col="data", mes=m_filtro, ano=a_filtro)

        if df_filtrado_cx.empty:
            st.info("Nenhum lançamento no período selecionado.")
        else:
            col_b_cx, col_f_cx = st.columns([3, 2])
            with col_b_cx:
                busca_cx = st.text_input("🔍 Buscar Lançamento", placeholder="Descrição, categoria...", key="busca_cx_ext")
            with col_f_cx:
                filtro_tipo = st.selectbox("Filtrar Tipo:", ["Todos", "Entrada", "Saída", "Desconto"], key="flt_tipo_cx")

            df_show = df_filtrado_cx.copy()
            if busca_cx:
                b_low = busca_cx.lower()
                df_show = df_show[
                    df_show["descricao"].astype(str).str.lower().str.contains(b_low) |
                    df_show["categoria"].astype(str).str.lower().str.contains(b_low)
                ]
            if filtro_tipo != "Todos":
                df_show = df_show[df_show["tipo"] == filtro_tipo]

            df_show = df_show.sort_values(by="data", ascending=False)
            st.caption(f"Mostrando **{len(df_show)}** lançamento(s)")

            for _, row in df_show.iterrows():
                cx_id = row.get("id")
                tipo = row.get("tipo", "Entrada")
                data_s = row.get("data", "")
                desc = row.get("descricao", "")
                cat = row.get("categoria", "")
                val = float(row.get("valor", 0.0))
                fp = row.get("forma_pagamento", "Pix")
                obs = row.get("observacao", "")

                cor_tipo = "#10b981" if tipo == "Entrada" else "#ef4444" if tipo == "Saída" else "#f59e0b"
                sinal = "+" if tipo == "Entrada" else "-"

                with st.container():
                    st.markdown(f"""
                        <div style="background: white; border-radius: 10px; padding: 12px 18px; margin-bottom: 8px; border-left: 5px solid {cor_tipo}; box-shadow: 0 1px 5px rgba(0,0,0,0.03);">
                            <div style="display: flex; justify-content: space-between; align-items: center;">
                                <div>
                                    <span style="font-weight: 700; font-size: 15px; color: #1e293b;">{desc}</span>
                                    <span style="font-size: 12px; color: #64748b;"> ({cat} • {fp})</span>
                                </div>
                                <div style="font-size: 16px; font-weight: 800; color: {cor_tipo};">
                                    {sinal} {formatar_moeda(val)}
                                </div>
                            </div>
                            <div style="font-size: 12px; color: #64748b; margin-top: 4px;">
                                📅 {format_date_br(data_s)} {f'| 📝 {obs}' if obs else ''}
                            </div>
                        </div>
                    """, unsafe_allow_html=True)

                    col_act1, col_act2, col_act3 = st.columns([5, 2, 1])
                    with col_act2:
                        with st.popover("✏️ Editar", use_container_width=True):
                            st.markdown(f"#### ✏️ Editar Lançamento")
                            ecx_desc = st.text_input("Descrição", value=str(desc), key=f"ecx_d_{cx_id}")
                            col_ec1, col_ec2 = st.columns(2)
                            with col_ec1:
                                tipo_idx = ["Entrada", "Saída", "Desconto"].index(tipo) if tipo in ["Entrada", "Saída", "Desconto"] else 0
                                ecx_tipo = st.selectbox("Tipo", ["Entrada", "Saída", "Desconto"], index=tipo_idx, key=f"ecx_t_{cx_id}")
                            with col_ec2:
                                ecx_val = st.number_input("Valor (R$)", min_value=0.01, value=float(val), step=5.0, key=f"ecx_v_{cx_id}")

                            col_ec3, col_ec4 = st.columns(2)
                            with col_ec3:
                                ecx_data = st.date_input("Data", value=parse_date(data_s), key=f"ecx_dt_{cx_id}")
                            with col_ec4:
                                fp_idx = FORMAS_PAGAMENTO.index(fp) if fp in FORMAS_PAGAMENTO else 0
                                ecx_fp = st.selectbox("Pagamento", FORMAS_PAGAMENTO, index=fp_idx, key=f"ecx_fp_{cx_id}")

                            ecx_cat = st.text_input("Categoria", value=str(cat), key=f"ecx_cat_{cx_id}")
                            ecx_obs = st.text_input("Observação", value=str(obs), key=f"ecx_obs_{cx_id}")

                            if st.button("💾 Salvar Alterações", key=f"btn_save_ecx_{cx_id}", type="primary"):
                                update_record("Caixa", cx_id, {
                                    "descricao": ecx_desc.strip(),
                                    "tipo": ecx_tipo,
                                    "valor": float(ecx_val),
                                    "data": ecx_data.strftime("%Y-%m-%d"),
                                    "forma_pagamento": ecx_fp,
                                    "categoria": ecx_cat.strip(),
                                    "observacao": ecx_obs.strip()
                                })
                                st.success("Lançamento atualizado!")
                                st.rerun()

                    with col_act3:
                        if st.button("🗑️", key=f"del_cx_{cx_id}", help="Excluir lançamento"):
                            delete_record("Caixa", cx_id)
                            st.rerun()
