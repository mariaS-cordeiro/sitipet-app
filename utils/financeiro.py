"""
Utilitários Financeiros - SitiPet
Cálculos de métricas, totais, gráficos interativos Plotly e análise estratégica.
"""

import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
from datetime import datetime
from utils.datas import parse_date

CORES_SITIPET = {
    "Banho": "#3b82f6",       # Azul
    "Tosa": "#d82678",        # Rosa SitiPet
    "Hospedagem": "#f59e0b",  # Amarelo/Caramelo
    "Adicionais": "#8b5cf6",  # Roxo
    "Produtos": "#10b981",    # Verde
    "Outros": "#64748b"       # Cinza ardósia
}

def formatar_moeda(valor) -> str:
    """Formata valor float para moeda brasileira (R$ 1.250,00)."""
    try:
        val = float(valor) if valor is not None else 0.0
    except (ValueError, TypeError):
        val = 0.0
    
    s = f"{val:,.2f}"
    # Inverter separadores para o padrão brasileiro
    s = s.replace(",", "X").replace(".", ",").replace("X", ".")
    return f"R$ {s}"

def filtrar_dataframe_por_periodo(df: pd.DataFrame, mes: int = None, ano: int = None, coluna_data: str = "data") -> pd.DataFrame:
    """Filtra um DataFrame por mês e ano."""
    if df is None or df.empty or coluna_data not in df.columns:
        return pd.DataFrame()
    
    df_temp = df.copy()
    # Garantir que a coluna de data seja convertida
    df_temp["_dt"] = df_temp[coluna_data].apply(parse_date)
    df_temp["_ano"] = df_temp["_dt"].apply(lambda d: d.year)
    df_temp["_mes"] = df_temp["_dt"].apply(lambda d: d.month)
    
    if ano is not None:
        df_temp = df_temp[df_temp["_ano"] == int(ano)]
    if mes is not None:
        df_temp = df_temp[df_temp["_mes"] == int(mes)]
        
    return df_temp.drop(columns=["_dt", "_ano", "_mes"], errors="ignore")

def calcular_metricas_financeiras(df_caixa: pd.DataFrame, mes: int = None, ano: int = None) -> dict:
    """Calcula Total de Entradas, Saídas, Descontos e Saldo."""
    if df_caixa is None or df_caixa.empty:
        return {
            "total_entradas": 0.0,
            "total_saidas": 0.0,
            "total_descontos": 0.0,
            "saldo": 0.0,
            "qtd_lancamentos": 0
        }
    
    df_filtrado = filtrar_dataframe_por_periodo(df_caixa, mes, ano)
    if df_filtrado.empty:
        return {
            "total_entradas": 0.0,
            "total_saidas": 0.0,
            "total_descontos": 0.0,
            "saldo": 0.0,
            "qtd_lancamentos": 0
        }

    # Converter coluna de valor
    df_filtrado["valor_num"] = pd.to_numeric(df_filtrado["valor"], errors="coerce").fillna(0.0)
    
    entradas = df_filtrado[df_filtrado["tipo"] == "Entrada"]["valor_num"].sum()
    saidas = df_filtrado[df_filtrado["tipo"] == "Saída"]["valor_num"].sum()
    descontos = df_filtrado[df_filtrado["tipo"] == "Desconto"]["valor_num"].sum()
    
    saldo = entradas - saidas - descontos

    return {
        "total_entradas": float(entradas),
        "total_saidas": float(saidas),
        "total_descontos": float(descontos),
        "saldo": float(saldo),
        "qtd_lancamentos": len(df_filtrado)
    }

def normalizar_servico_categoria(servico_nome: str, categoria: str = "") -> str:
    """Classifica o serviço em grupos padrão: Banho, Tosa, Hospedagem, Outros."""
    s = str(servico_nome).lower() if servico_nome else ""
    c = str(categoria).lower() if categoria else ""
    
    if "hosped" in s or "hotel" in s or "diária" in s or "diaria" in s or "hosped" in c:
        return "Hospedagem"
    elif "tosa" in s or "tosa" in c:
        return "Tosa"
    elif "banho" in s or "banho" in c:
        return "Banho"
    elif "unha" in s or "ouvido" in s or "dente" in s or "hidrata" in s or "adicional" in c:
        return "Adicionais"
    elif "produto" in s or "ração" in s or "petisco" in s or "produto" in c:
        return "Produtos"
    else:
        return "Outros"

def gerar_grafico_pizza_servicos(df_caixa: pd.DataFrame, mes: int = None, ano: int = None):
    """Gera gráfico de pizza mensal com participação dos serviços no faturamento."""
    df_filtrado = filtrar_dataframe_por_periodo(df_caixa, mes, ano)
    
    if df_filtrado.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Nenhum dado financeiro para o período selecionado",
            annotations=[dict(text="Sem dados para exibir o gráfico", showarrow=False, font=dict(size=14, color="#64748b"))],
            height=320,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    # Filtrar apenas entradas
    df_entradas = df_filtrado[df_filtrado["tipo"] == "Entrada"].copy()
    if df_entradas.empty:
        fig = go.Figure()
        fig.update_layout(
            title="Nenhuma entrada registrada no período",
            annotations=[dict(text="Nenhum faturamento registrado", showarrow=False, font=dict(size=14, color="#64748b"))],
            height=320,
            margin=dict(l=20, r=20, t=40, b=20)
        )
        return fig

    df_entradas["valor_num"] = pd.to_numeric(df_entradas["valor"], errors="coerce").fillna(0.0)
    df_entradas["grupo_servico"] = df_entradas.apply(
        lambda r: normalizar_servico_categoria(r.get("servico_relacionado", ""), r.get("categoria", "")),
        axis=1
    )

    df_agrupado = df_entradas.groupby("grupo_servico")["valor_num"].sum().reset_index()
    df_agrupado = df_agrupado[df_agrupado["valor_num"] > 0]

    if df_agrupado.empty:
        fig = go.Figure()
        fig.update_layout(height=320)
        return fig

    cores = [CORES_SITIPET.get(g, "#64748b") for g in df_agrupado["grupo_servico"]]

    fig = go.Figure(data=[go.Pie(
        labels=df_agrupado["grupo_servico"],
        values=df_agrupado["valor_num"],
        hole=0.45,
        marker=dict(colors=cores, line=dict(color='#ffffff', width=2)),
        textinfo='label+percent',
        hoverinfo='label+value+percent',
        hovertemplate='<b>%{label}</b><br>Faturamento: R$ %{value:,.2f}<br>Participação: %{percent}<extra></extra>'
    )])

    fig.update_layout(
        title="<b>Participação por Tipo de Serviço</b>",
        title_font=dict(size=16, color="#1e293b"),
        showlegend=True,
        legend=dict(orientation="h", yanchor="bottom", y=-0.2, xanchor="center", x=0.5),
        margin=dict(l=20, r=20, t=50, b=30),
        height=350,
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)'
    )
    return fig

def obter_servicos_destaque(df_caixa: pd.DataFrame, df_banho_tosa: pd.DataFrame = None, df_hospedagem: pd.DataFrame = None, mes: int = None, ano: int = None) -> dict:
    """
    Identifica:
    1. Serviço mais realizado (quantidade/volume)
    2. Serviço com maior faturamento (receita total)
    """
    # 1. Análise de Faturamento (Caixa)
    df_caixa_fil = filtrar_dataframe_por_periodo(df_caixa, mes, ano)
    servico_maior_faturamento = "Nenhum no período"
    valor_maior_faturamento = 0.0

    if not df_caixa_fil.empty:
        df_entradas = df_caixa_fil[df_caixa_fil["tipo"] == "Entrada"].copy()
        if not df_entradas.empty:
            df_entradas["valor_num"] = pd.to_numeric(df_entradas["valor"], errors="coerce").fillna(0.0)
            df_entradas["grupo_servico"] = df_entradas.apply(
                lambda r: normalizar_servico_categoria(r.get("servico_relacionado", ""), r.get("categoria", "")),
                axis=1
            )
            fat_grp = df_entradas.groupby("grupo_servico")["valor_num"].sum()
            if not fat_grp.empty and fat_grp.max() > 0:
                top_serv = fat_grp.idxmax()
                top_val = fat_grp.max()
                servico_maior_faturamento = top_serv
                valor_maior_faturamento = float(top_val)

    # 2. Análise de Volume Realizado (Contagem em Banho & Tosa e Hospedagem)
    contagens = {"Banho": 0, "Tosa": 0, "Hospedagem": 0, "Adicionais": 0, "Outros": 0}
    
    if df_banho_tosa is not None and not df_banho_tosa.empty:
        df_bt_fil = filtrar_dataframe_por_periodo(df_banho_tosa, mes, ano)
        for _, row in df_bt_fil.iterrows():
            servs = str(row.get("servicos_detalhados", "")).lower()
            if "banho" in servs:
                contagens["Banho"] += 1
            if "tosa" in servs:
                contagens["Tosa"] += 1
            if "unha" in servs or "ouvido" in servs or "dente" in servs or "hidrata" in servs:
                contagens["Adicionais"] += 1

    if df_hospedagem is not None and not df_hospedagem.empty:
        df_hosp_fil = filtrar_dataframe_por_periodo(df_hospedagem, mes, ano, coluna_data="data_entrada")
        contagens["Hospedagem"] += len(df_hosp_fil)

    # Se não houver dados nas tabelas específicas, estimar pelas entradas do caixa
    if sum(contagens.values()) == 0 and not df_caixa_fil.empty:
        df_ent = df_caixa_fil[df_caixa_fil["tipo"] == "Entrada"]
        for _, r in df_ent.iterrows():
            g = normalizar_servico_categoria(r.get("servico_relacionado", ""), r.get("categoria", ""))
            contagens[g] = contagens.get(g, 0) + 1

    servico_mais_realizado = "Nenhum no período"
    qtd_mais_realizado = 0
    if contagens:
        top_qtd_serv = max(contagens, key=contagens.get)
        top_qtd = contagens[top_qtd_serv]
        if top_qtd > 0:
            servico_mais_realizado = top_qtd_serv
            qtd_mais_realizado = top_qtd

    return {
        "mais_realizado_nome": servico_mais_realizado,
        "mais_realizado_qtd": qtd_mais_realizado,
        "maior_faturamento_nome": servico_maior_faturamento,
        "maior_faturamento_valor": valor_maior_faturamento
    }
