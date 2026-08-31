"""
Visão: Aba 4 – Caixa e Gestão Financeira - SitiPet
Controle de entradas, saídas, descontos, métricas mensais, gráfico de pizza e indicadores de serviço.
"""

import streamlit as st
import pandas as pd
from datetime import datetime, date
import uuid
import io
from utils.storage import load_table, insert_record, delete_record
from utils.datas import (
    get_today_date, get_today_date_str, format_date_br,
    get_meses_nomes, get_anos_disponiveis, mes_nome_para_numero, mes_numero_para_nome
)
from utils.financeiro import (
    formatar_moeda, calcular_metricas_financeiras,
    gerar_grafico_pizza_servicos, obter_servicos_destaque, filtrar_dataframe_por_periodo
)

CATEGORIAS_ENTRADA = ["Banho e Tosa", "Hospedagem", "Serviços Adicionais", "Venda de Produtos", "Outras Receitas"]
CATEGORIAS_SAIDA = ["Produtos e Materiais", "Shampoos e Cosméticos", "Manutenção e Equipamentos", "Pagamento de Pessoal", "Aluguel e Contas", "Despesas Administrativas", "Outros Gastos"]
FORMAS_PAGAMENTO = ["Pix", "Cartão de Crédito", "Cartão de Débito", "Dinheiro", "Boleto", "Outro"]

def render_caixa():
    st.markdown("## 💰 Aba 4 – Caixa e Gestão Financeira")
    st.markdown("Controle de fluxo de caixa, receitas por serviço, controle de despesas e análise mensal com indicadores estratégicos.")

    df_caixa = load_table("Caixa")
    df_bt = load_table("Banho_Tosa")
    df_hosp = load_table("Hospedagem")

    # ==================== FORMULÁRIO DE NOVO LANÇAMENTO ====================
    with st.expander("➕ **Novo Lançamento Financeiro (Entrada / Saída / Desconto)**", expanded=False):
        with st.form("form_novo_lancamento", clear_on_submit=True):
            col_t1, col_t2, col_t3 = st.columns(3)
            with col_t1:
                tipo_mov = st.selectbox("Tipo de Movimentação *", ["Entrada", "Saída", "Desconto"], key="cx_tipo")
            with col_t2:
                if tipo_mov == "Entrada":
                    cat_opcoes = CATEGORIAS_ENTRADA
                elif tipo_mov == "Saída":
                    cat_opcoes = CATEGORIAS_SAIDA
                else:
                    cat_opcoes = ["Desconto Cliente / Promoção", "Ajuste de Valor"]
                categoria = st.selectbox("Categoria *", cat_opcoes, key="cx_cat")
            with col_t3:
                servico_rel = st.selectbox("Serviço Relacionado", ["Banho e Tosa", "Hospedagem", "Produtos", "Geral / Despesas"], key="cx_serv_rel")

            col_d1, col_d2, col_d3 = st.columns(3)
            with col_d1:
                data_lanc = st.date_input("📅 Data", value=get_today_date(), key="cx_data")
            with col_d2:
                valor_lanc = st.number_input("💵 Valor (R$) *", min_value=0.01, value=50.0, step=5.0, key="cx_val")
            with col_d3:
                forma_pag = st.selectbox("Forma de Pagamento", FORMAS_PAGAMENTO, key="cx_fp")

            descricao = st.text_input("📝 Descrição do Lançamento *", placeholder="Ex: Pagamento Banho Thor, Compra Shampoos 5L, etc.", key="cx_desc")
            observacao = st.text_input("Observação Adicional", placeholder="Ex: Fornecedor PetClean, Nota Fiscal 1234...", key="cx_obs")

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
                    st.success(f"✅ Lançamento de **{formatar_moeda(valor_lanc)}** ({tipo_mov}) salvo com sucesso!")
                    st.rerun()

    # ==================== FILTRO DE MÊS E ANO COM HISTÓRICO PERMANENTE ====================
    st.markdown("---")
    st.markdown("### 📊 Análise Financeira Mensal & Indicadores")
    
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
        ver_todos_periodos = st.checkbox("🌐 Ver Todos os Períodos (Acumulado)", value=False, key="chk_all_periodos")

    m_filtro = None if ver_todos_periodos else num_mes_sel
    a_filtro = None if ver_todos_periodos else ano_selecionado

    # ==================== MÉTRICAS TOTAIS ====================
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
                <div style="font-size: 13px; color: #64748b; font-weight: 600; text-transform: uppercase;">📤 Saídas / Gastos</div>
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

    # ==================== DOIS INDICADORES ESTRATÉGICOS ====================
    destaques = obter_servicos_destaque(df_caixa, df_bt, df_hosp, mes=m_filtro, ano=a_filtro)

    col_dest1, col_dest2 = st.columns(2)
    with col_dest1:
        st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 16px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 6px solid #3b82f6;">
                <div style="font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase;">🏆 Serviço Mais Realizado (Volume)</div>
                <div style="font-size: 22px; font-weight: 800; color: #1e293b; margin: 6px 0;">
                    {destaques['mais_realizado_nome']}
                </div>
                <div style="font-size: 14px; color: #3b82f6; font-weight: 700;">
                    📊 {destaques['mais_realizado_qtd']} atendimentos no período
                </div>
            </div>
        """, unsafe_allow_html=True)

    with col_dest2:
        st.markdown(f"""
            <div style="background: white; border-radius: 12px; padding: 16px 20px; box-shadow: 0 2px 8px rgba(0,0,0,0.05); border-left: 6px solid #d82678;">
                <div style="font-size: 13px; color: #64748b; font-weight: 700; text-transform: uppercase;">💰 Serviço com Maior Faturamento (Receita)</div>
                <div style="font-size: 22px; font-weight: 800; color: #1e293b; margin: 6px 0;">
                    {destaques['maior_faturamento_nome']}
                </div>
                <div style="font-size: 14px; color: #d82678; font-weight: 700;">
                    💵 {formatar_moeda(destaques['maior_faturamento_valor'])} faturados
                </div>
            </div>
        """, unsafe_allow_html=True)

    # ==================== GRÁFICO DE PIZZA MENSAL ====================
    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("#### 🥧 Distribuição de Participação dos Serviços no Faturamento")
    fig_pizza = gerar_grafico_pizza_servicos(df_caixa, mes=m_filtro, ano=a_filtro)
    st.plotly_chart(fig_pizza, use_container_width=True)

    # ==================== EXTRATO DETALHADO ====================
    st.markdown("---")
    st.markdown("### 📋 Extrato de Lançamentos do Caixa")

    df_extrato = filtrar_dataframe_por_periodo(df_caixa, mes=m_filtro, ano=a_filtro)

    if df_extrato.empty:
        st.info("Nenhum lançamento financeiro registrado para o período selecionado.")
        return

    # Filtro interno de busca e tipo
    col_ef1, col_ef2, col_ef3 = st.columns([3, 2, 2])
    with col_ef1:
        busca_cx = st.text_input("🔍 Buscar no Extrato", placeholder="Descrição, categoria...", key="busca_cx")
    with col_ef2:
        tipo_filtro = st.selectbox("Filtrar por Tipo", ["Todos", "Entrada", "Saída", "Desconto"], key="flt_tipo_cx")
    with col_ef3:
        # Botão para download em CSV
        csv_buffer = io.StringIO()
        df_extrato.to_csv(csv_buffer, index=False, sep=";", encoding="utf-8-sig")
        st.download_button(
            "📥 Baixar Extrato (CSV)",
            data=csv_buffer.getvalue(),
            file_name=f"sitipet_caixa_{mes_selecionado_nome}_{ano_selecionado}.csv",
            mime="text/csv",
            use_container_width=True
        )

    df_show = df_extrato.copy()
    if busca_cx:
        b_low = busca_cx.lower()
        df_show = df_show[
            df_show["descricao"].astype(str).str.lower().str.contains(b_low) |
            df_show["categoria"].astype(str).str.lower().str.contains(b_low) |
            df_show["forma_pagamento"].astype(str).str.lower().str.contains(b_low)
        ]
    if tipo_filtro != "Todos":
        df_show = df_show[df_show["tipo"] == tipo_filtro]

    # Ordenar por data decrescente
    df_show = df_show.sort_values(by="data", ascending=False)

    for _, row in df_show.iterrows():
        cx_id = row.get("id")
        tipo = row.get("tipo")
        data_s = row.get("data")
        desc = row.get("descricao")
        cat = row.get("categoria")
        val = float(row.get("valor", 0.0))
        fp = row.get("forma_pagamento")
        obs = row.get("observacao", "")

        cor_tipo = "#10b981" if tipo == "Entrada" else "#ef4444" if tipo == "Saída" else "#f59e0b"
        sinal = "+" if tipo == "Entrada" else "-"

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

        col_act1, col_act2 = st.columns([6, 1])
        with col_act2:
            if st.button("🗑️", key=f"del_cx_{cx_id}", help="Excluir este lançamento"):
                delete_record("Caixa", cx_id)
                st.rerun()
