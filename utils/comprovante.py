"""
Módulo de Emissão de Comprovantes e Cupons de Serviços - SitiPet
Gera notas e recibos detalhados por cachorro estilo cupom de supermercado,
com discriminação individual de cada serviço e valor, impressão térmica/PDF e envio para WhatsApp.
"""

import streamlit as st
import pandas as pd
import re
import urllib.parse
from datetime import datetime
from utils.financeiro import formatar_moeda
from utils.datas import format_date_br, get_today_date_str

def extrair_itens_servicos(servicos_str: str, valor_total_fallback: float = 0.0) -> list:
    """
    Analisa e extrai cada serviço individual com seu respectivo valor
    a partir de descrições como:
    'Banho (Pequeno) (R$ 50,00), Corte de unhas (R$ 10,00)' ou 'Banho + Tosa'.
    Retorna uma lista de dicionários [{'nome': '...', 'valor': float}].
    """
    if not servicos_str:
        return [{"nome": "Serviço Geral", "valor": float(valor_total_fallback)}]
    
    itens = []
    partes = re.split(r"[,;\n\+]+", str(servicos_str))
    
    for p in partes:
        p = p.strip()
        if not p:
            continue
        
        # Procura padrão monetário: (R$ 50,00) ou R$ 50,00 ou (50.00)
        match = re.search(r"\(?R\$\s*([\d\.,]+)\)?", p, re.IGNORECASE)
        if match:
            val_str = match.group(1).replace(".", "").replace(",", ".")
            try:
                val = float(val_str)
            except ValueError:
                val = 0.0
            # Remove o valor do nome para não duplicar no cupom
            nome = re.sub(r"\(?R\$\s*[\d\.,]+\)?", "", p).strip().strip("-: ")
            if not nome:
                nome = "Serviço"
            itens.append({"nome": nome, "valor": val})
        else:
            itens.append({"nome": p, "valor": 0.0})
    
    # Se alguns itens ficaram com valor 0, distribuir o valor total proporcionalmente ou fallback
    zeros = [it for it in itens if it["valor"] == 0.0]
    if zeros and valor_total_fallback > 0:
        val_preenchido = sum(it["valor"] for it in itens if it["valor"] > 0)
        val_restante = max(0.0, valor_total_fallback - val_preenchido)
        if val_restante > 0:
            val_por_zero = val_restante / len(zeros)
            for it in zeros:
                it["valor"] = val_por_zero
        elif val_preenchido == 0:
            val_cada = valor_total_fallback / len(itens)
            for it in itens:
                it["valor"] = val_cada

    if not itens:
        itens = [{"nome": str(servicos_str), "valor": float(valor_total_fallback)}]
        
    return itens

def formatar_link_whatsapp(telefone: str, mensagem: str) -> str:
    """Gera o link universal wa.me para abertura direta no WhatsApp."""
    if not telefone:
        return ""
    num_limpo = re.sub(r"[^\d]", "", str(telefone))
    if len(num_limpo) in [10, 11] and not num_limpo.startswith("55"):
        num_limpo = f"55{num_limpo}"
    return f"https://wa.me/{num_limpo}?text={urllib.parse.quote(mensagem)}"

def gerar_html_comprovante(
    titulo: str,
    cliente_nome: str,
    cliente_telefone: str,
    pet_nome: str,
    raca: str = "",
    porte: str = "",
    profissional: str = "",
    data_servico: str = "",
    itens: list = None,
    valor_total: float = 0.0,
    forma_pagamento: str = "Pix",
    observacoes: str = "",
    codigo_recibo: str = "",
    desconto: float = 0.0
) -> str:
    """
    Gera o HTML estilizado no formato autêntico de CUPOM DE SERVIÇOS / NOTA TÉRMICA,
    pronto para impressão em impressora comum A4 ou impressora térmica (58/80mm) ou PDF.
    """
    itens = itens or []
    subtotal = sum(float(it.get("valor", 0.0)) for it in itens) if itens else valor_total
    if valor_total <= 0:
        valor_total = subtotal - desconto

    linhas_tabela = ""
    for idx, item in enumerate(itens, start=1):
        nome_item = str(item.get("nome", "Serviço")).strip()
        val_item = float(item.get("valor", 0.0))
        linhas_tabela += f"""
        <tr style="border-bottom: 1px dotted #cbd5e1;">
            <td style="padding: 5px 0; font-size: 13px; color: #0f172a; text-align: left; vertical-align: top;">
                <b>{idx:02d}</b> &nbsp; {nome_item}
            </td>
            <td style="padding: 5px 0; font-size: 13px; font-weight: 700; color: #0f172a; text-align: right; white-space: nowrap; vertical-align: top;">
                {formatar_moeda(val_item)}
            </td>
        </tr>
        """

    cod_limpo = re.sub(r"[^\w\-]", "", str(codigo_recibo)) or "001"
    data_formatada = format_date_br(data_servico) if data_servico else format_date_br(get_today_date_str())

    html = f"""
    <div id="cupom-sitipet-{cod_limpo}" class="cupom-container" style="
        max-width: 330px;
        margin: 0 auto;
        background: #ffffff;
        padding: 16px 14px 28px 14px;
        border: 1px dashed #000000;
        border-radius: 4px;
        font-family: 'Courier New', Courier, monospace, 'Lucida Console', monospace;
        box-shadow: 0 4px 14px rgba(0,0,0,0.06);
        color: #000000;
        line-height: 1.35;
        font-size: 13px;
        font-weight: 700;
    ">
        <!-- CABEÇALHO DO ESTABELECIMENTO -->
        <div style="text-align: center; border-bottom: 2px dashed #000000; padding-bottom: 10px; margin-bottom: 10px;">
            <div style="font-size: 20px; font-weight: 900; letter-spacing: 1px; color: #000000;">🐾 SITIPET 🐾</div>
            <div style="font-size: 12px; font-weight: 800; color: #000000; letter-spacing: 0.5px;">PET SHOP E HOTELZINHO</div>
            <div style="font-size: 11px; color: #000000; margin-top: 2px;">Cuidando com carinho do seu melhor amigo</div>
            <div style="font-size: 11px; color: #000000;">Telefone / WhatsApp: (11) 98888-7777</div>
        </div>

        <!-- IDENTIFICAÇÃO DO CUPOM / ATENDIMENTO -->
        <div style="font-size: 12px; text-align: center; font-weight: 900; border: 1px solid #000000; padding: 4px 6px; margin-bottom: 10px; color: #000000; text-transform: uppercase;">
            📄 {titulo.upper()} • Nº #{codigo_recibo}
        </div>

        <!-- DADOS DO CACHORRO E DO TUTOR -->
        <div style="font-size: 12px; border-bottom: 1px dashed #000000; padding-bottom: 8px; margin-bottom: 10px; line-height: 1.4;">
            <div style="display: flex; justify-content: space-between;">
                <span><b>DATA:</b> {data_formatada}</span>
                <span><b>HORA:</b> {datetime.now().strftime('%H:%M')}</span>
            </div>
            <div style="margin-top: 3px;"><b>🐶 PET:</b> <span style="font-size: 14px; font-weight: 900;">{pet_nome.upper()}</span> {f'({raca} • {porte})' if raca or porte else ''}</div>
            <div style="margin-top: 2px;"><b>👤 CLIENTE:</b> {cliente_nome}</div>
            {f'<div style="margin-top: 2px;"><b>📱 CONTATO:</b> {cliente_telefone}</div>' if cliente_telefone else ''}
            {f'<div style="margin-top: 2px;"><b>✂️ ATENDENTE:</b> {profissional}</div>' if profissional else ''}
        </div>

        <!-- TABELA DE SERVIÇOS DISCRIMINADOS -->
        <div style="margin-bottom: 10px;">
            <div style="font-size: 11px; font-weight: 900; border-bottom: 1.5px solid #000000; padding-bottom: 3px; margin-bottom: 5px; display: flex; justify-content: space-between;">
                <span>ITEM &nbsp; DESCRIÇÃO</span>
                <span>VALOR (R$)</span>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                {linhas_tabela}
            </table>
        </div>

        <!-- TOTAIS E FORMA DE PAGAMENTO -->
        <div style="border-top: 2px dashed #000000; padding-top: 8px; margin-top: 8px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #000000;">
                <span>Qtd. de Serviços:</span>
                <span><b>{len(itens)} item(ns)</b></span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #000000; margin-top: 2px;">
                <span>Subtotal dos Serviços:</span>
                <span>{formatar_moeda(subtotal)}</span>
            </div>
            {f'''<div style="display: flex; justify-content: space-between; font-size: 12px; color: #000000; margin-top: 2px;">
                <span>Desconto:</span>
                <span>- {formatar_moeda(desconto)}</span>
            </div>''' if desconto > 0 else ''}
            
            <div style="display: flex; justify-content: space-between; font-size: 16px; font-weight: 900; color: #000000; margin-top: 6px; padding-top: 6px; border-top: 1px dotted #000000;">
                <span>TOTAL A PAGAR:</span>
                <span>{formatar_moeda(valor_total)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #000000; margin-top: 4px;">
                <span>Forma de Pagto:</span>
                <span><b>{forma_pagamento}</b></span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #000000; margin-top: 2px;">
                <span>Status da Conta:</span>
                <span><b>✅ PAGO / FECHADO</b></span>
            </div>
        </div>

        {f'''<div style="margin-top: 8px; font-size: 11px; color: #000000; border: 1px dotted #000000; padding: 4px 6px;">
            <b>Obs:</b> {observacoes}
        </div>''' if observacoes else ''}

        <!-- RODAPÉ TÉRMICO COM ESPAÇO PARA CORTE DA GUILHOTINA -->
        <div style="text-align: center; margin-top: 14px; border-top: 1px dashed #000000; padding-top: 10px; font-size: 11px; color: #000000;">
            <p style="margin: 0; font-weight: 900; font-size: 12px;">🐾 Muito obrigado pela preferência! 🐶❤️</p>
            <p style="margin: 2px 0 0 0;">Cuidando com amor de quem você ama.</p>
            <p style="margin: 2px 0 0 0; font-weight: 800;">Volte sempre ao SitiPet!</p>
            <div style="margin-top: 8px; font-size: 10px; letter-spacing: 2px;">
                ================================
            </div>
            <div style="height: 25px;"></div>
        </div>
    </div>
    """
    return html

def gerar_texto_cupom_whatsapp(
    titulo: str,
    cliente_nome: str,
    pet_nome: str,
    raca: str = "",
    porte: str = "",
    profissional: str = "",
    data_servico: str = "",
    itens: list = None,
    valor_total: float = 0.0,
    forma_pagamento: str = "Pix",
    observacoes: str = "",
    codigo_recibo: str = ""
) -> str:
    """Gera o texto elegante e formatado para envio direto no WhatsApp."""
    itens = itens or []
    linhas_servicos = []
    for idx, it in enumerate(itens, start=1):
        nome_it = it.get("nome", "Serviço")
        val_it = float(it.get("valor", 0.0))
        linhas_servicos.append(f"  *{idx:02d}.* {nome_it} — *{formatar_moeda(val_it)}*")
    
    txt_servicos = "\n".join(linhas_servicos) if linhas_servicos else f"  • Serviços: {formatar_moeda(valor_total)}"
    data_fmt = format_date_br(data_servico) if data_servico else format_date_br(get_today_date_str())

    msg = f"""🐾 *SITIPET - COMPROVANTE DE SERVIÇOS* 🐾
━━━━━━━━━━━━━━━━━━━━━━━━━━
📄 *Cupom Nº:* #{codigo_recibo} | *Data:* {data_fmt}

🐶 *Cachorro / Pet:* *{pet_nome}* {f'({raca} - {porte})' if raca or porte else ''}
👤 *Tutor(a):* {cliente_nome}
✂️ *Profissional:* {profissional if profissional else 'Equipe SitiPet'}
━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 *SERVIÇOS REALIZADOS:*
{txt_servicos}
━━━━━━━━━━━━━━━━━━━━━━━━━━
💰 *VALOR TOTAL:* *{formatar_moeda(valor_total)}*
💳 *Pagamento:* {forma_pagamento}
{f'📝 *Obs:* {observacoes}' if observacoes else ''}
━━━━━━━━━━━━━━━━━━━━━━━━━━
Muito obrigado pela confiança e carinho com o seu pet! 🐶❤️
*SitiPet Pet Shop e Hotelzinho*"""
    return msg

def renderizar_modal_comprovante(
    titulo: str,
    cliente_nome: str,
    cliente_telefone: str,
    pet_nome: str,
    raca: str = "",
    porte: str = "",
    profissional: str = "",
    data_servico: str = "",
    itens: list = None,
    valor_total: float = 0.0,
    forma_pagamento: str = "Pix",
    observacoes: str = "",
    codigo_recibo: str = "",
    desconto: float = 0.0
):
    """
    Renderiza o comprovante estilizado na tela do Streamlit com botões para:
    1. Imprimir Cupom / Salvar em PDF (via janela de impressão nativa)
    2. Enviar direto no WhatsApp (link wa.me)
    3. Copiar texto formatado
    """
    cod_limpo = re.sub(r"[^\w\-]", "", str(codigo_recibo)) or "001"
    
    # Gerar HTML
    html_cupom = gerar_html_comprovante(
        titulo=titulo,
        cliente_nome=cliente_nome,
        cliente_telefone=cliente_telefone,
        pet_nome=pet_nome,
        raca=raca,
        porte=porte,
        profissional=profissional,
        data_servico=data_servico,
        itens=itens,
        valor_total=valor_total,
        forma_pagamento=forma_pagamento,
        observacoes=observacoes,
        codigo_recibo=codigo_recibo,
        desconto=desconto
    )

    # Exibe o Cupom
    st.markdown(html_cupom, unsafe_allow_html=True)
    st.markdown("<div style='height: 14px;'></div>", unsafe_allow_html=True)

    # Texto para WhatsApp
    texto_wa = gerar_texto_cupom_whatsapp(
        titulo=titulo,
        cliente_nome=cliente_nome,
        pet_nome=pet_nome,
        raca=raca,
        porte=porte,
        profissional=profissional,
        data_servico=data_servico,
        itens=itens,
        valor_total=valor_total,
        forma_pagamento=forma_pagamento,
        observacoes=observacoes,
        codigo_recibo=codigo_recibo
    )

    import json
    html_cupom_json = json.dumps(html_cupom)

    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        # Botão de impressão nativa otimizada para impressora térmica Epson TM-T20 (80mm) ou PDF
        st.components.v1.html(f"""
            <button onclick="imprimirCupomSitipet_{cod_limpo}()" style="
                width: 100%;
                background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
                color: white;
                border: none;
                padding: 11px 14px;
                border-radius: 8px;
                font-weight: 700;
                cursor: pointer;
                font-size: 13px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.15);
            ">
                🖨️ Imprimir na Epson TM-T20 / PDF
            </button>
            <script>
            var cupomHtml_{cod_limpo} = {html_cupom_json};
            function imprimirCupomSitipet_{cod_limpo}() {{
                var win = window.open('', '_blank', 'height=750,width=480');
                if (win) {{
                    win.document.write('<!DOCTYPE html><html><head><title>Cupom SitiPet - {pet_nome}</title>');
                    win.document.write('<style>');
                    win.document.write('@page {{ size: 80mm auto; margin: 0; }} body {{ font-family: \"Courier New\", Courier, monospace; background: white; margin: 0; padding: 2mm 0; display: flex; justify-content: center; }}');
                    win.document.write('</style>');
                    win.document.write('</head><body>');
                    win.document.write(cupomHtml_{cod_limpo});
                    win.document.write('</body></html>');
                    win.document.close();
                    win.focus();
                    setTimeout(function () {{ win.print(); }}, 400);
                }} else {{
                    alert('Por favor, permita pop-ups para imprimir o comprovante.');
                }}
            }}
            </script>
        """, height=50)

    with col_btn2:
        link_wa = formatar_link_whatsapp(cliente_telefone, texto_wa)
        if link_wa:
            st.link_button("💬 Enviar no WhatsApp", link_wa, use_container_width=True)
        else:
            with st.popover("📋 Copiar Cupom", use_container_width=True):
                st.code(texto_wa, language="text")
                st.caption("Copie o texto e envie para o cliente.")

