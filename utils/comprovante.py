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
        max-width: 400px;
        margin: 0 auto;
        background: #ffffff;
        padding: 24px 22px;
        border: 1px solid #cbd5e1;
        border-radius: 12px;
        font-family: 'Courier New', Courier, monospace, 'Lucida Console', monospace;
        box-shadow: 0 4px 16px rgba(0,0,0,0.06);
        color: #0f172a;
        line-height: 1.4;
    ">
        <!-- CABEÇALHO DO ESTABELECIMENTO -->
        <div style="text-align: center; border-bottom: 2px dashed #64748b; padding-bottom: 12px; margin-bottom: 12px;">
            <div style="font-size: 22px; font-weight: 900; letter-spacing: 1.5px; color: #1e3a8a;">🐾 SITIPET 🐾</div>
            <div style="font-size: 12px; font-weight: 800; color: #d82678; letter-spacing: 1px;">PET SHOP E HOTELZINHO</div>
            <div style="font-size: 11px; color: #475569; margin-top: 3px;">Cuidando com todo amor e carinho do seu pet!</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 2px;">Atendimento Especializado • Banho, Tosa & Hotel</div>
        </div>

        <!-- IDENTIFICAÇÃO DO CUPOM / ATENDIMENTO -->
        <div style="font-size: 11px; text-align: center; font-weight: 800; background: #f1f5f9; padding: 4px 8px; border-radius: 6px; margin-bottom: 12px; color: #334155; text-transform: uppercase; letter-spacing: 0.5px;">
            📄 {titulo.upper()} • Nº #{codigo_recibo}
        </div>

        <!-- DADOS DO CACHORRO E DO TUTOR -->
        <div style="font-size: 12px; border-bottom: 1px dashed #94a3b8; padding-bottom: 10px; margin-bottom: 12px;">
            <div style="display: flex; justify-content: space-between;">
                <span><b>📅 DATA:</b> {data_formatada}</span>
                <span><b>HORA:</b> {datetime.now().strftime('%H:%M')}</span>
            </div>
            <div style="margin-top: 4px;"><b>🐶 CACHORRO / PET:</b> <span style="font-size: 14px; font-weight: 900; color: #1e3a8a;">{pet_nome.upper()}</span> {f'({raca} • {porte})' if raca or porte else ''}</div>
            <div style="margin-top: 3px;"><b>👤 TUTOR(A):</b> {cliente_nome}</div>
            {f'<div style="margin-top: 2px;"><b>📱 TELEFONE:</b> {cliente_telefone}</div>' if cliente_telefone else ''}
            {f'<div style="margin-top: 2px;"><b>✂️ PROFISSIONAL:</b> {profissional}</div>' if profissional else ''}
        </div>

        <!-- TABELA DE SERVIÇOS DISCRIMINADOS -->
        <div style="margin-bottom: 12px;">
            <div style="font-size: 11px; font-weight: 900; border-bottom: 1.5px solid #0f172a; padding-bottom: 4px; margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span>QTD &nbsp; DESCRIÇÃO DO SERVIÇO</span>
                <span>VALOR</span>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                {linhas_tabela}
            </table>
        </div>

        <!-- TOTAIS E FORMA DE PAGAMENTO -->
        <div style="border-top: 2px dashed #64748b; padding-top: 10px; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #475569;">
                <span>Qtd. de Serviços:</span>
                <span><b>{len(itens)} item(ns)</b></span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 13px; color: #334155; margin-top: 2px;">
                <span>Subtotal dos Serviços:</span>
                <span>{formatar_moeda(subtotal)}</span>
            </div>
            {f'''<div style="display: flex; justify-content: space-between; font-size: 12px; color: #dc2626; margin-top: 2px;">
                <span>Desconto:</span>
                <span>- {formatar_moeda(desconto)}</span>
            </div>''' if desconto > 0 else ''}
            
            <div style="display: flex; justify-content: space-between; font-size: 17px; font-weight: 900; color: #0f172a; margin-top: 6px; padding-top: 6px; border-top: 1px dotted #94a3b8;">
                <span>TOTAL A PAGAR:</span>
                <span style="color: #15803d;">{formatar_moeda(valor_total)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #334155; margin-top: 4px;">
                <span>Forma de Pagamento:</span>
                <span><b>{forma_pagamento}</b></span>
            </div>
        </div>

        {f'''<div style="margin-top: 10px; font-size: 11px; color: #475569; background: #f8fafc; padding: 6px 8px; border-radius: 6px; border-left: 3px solid #cbd5e1;">
            <b>Observações:</b> {observacoes}
        </div>''' if observacoes else ''}

        <!-- RODAPÉ ESTILO CUPOM FISCAL / TÉRMICO -->
        <div style="text-align: center; margin-top: 18px; border-top: 1px dashed #94a3b8; padding-top: 12px; font-size: 11px; color: #475569;">
            <p style="margin: 0; font-weight: 800; font-size: 12px; color: #1e293b;">🐾 Muito obrigado pela preferência! 🐶❤️</p>
            <p style="margin: 3px 0 0 0;">Cuidamos de quem você mais ama com todo carinho.</p>
            <p style="margin: 2px 0 0 0; font-weight: 700; color: #d82678;">Volte sempre ao SitiPet!</p>
            <div style="margin-top: 8px; font-size: 10px; color: #94a3b8; letter-spacing: 2px;">
                * * * SITIPET PET SHOP * * *
            </div>
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

    col_btn1, col_btn2 = st.columns([1, 1])
    
    with col_btn1:
        # Botão de impressão nativa para Impressora ou Salvar como PDF
        st.components.v1.html(f"""
            <button onclick="imprimirCupomSitipet_{cod_limpo}()" style="
                width: 100%;
                background: linear-gradient(135deg, #1e3a8a 0%, #2563eb 100%);
                color: white;
                border: none;
                padding: 10px 14px;
                border-radius: 8px;
                font-weight: 700;
                cursor: pointer;
                font-size: 13px;
                display: flex;
                align-items: center;
                justify-content: center;
                gap: 6px;
                box-shadow: 0 2px 6px rgba(0,0,0,0.1);
            ">
                🖨️ Imprimir / Salvar PDF
            </button>
            <script>
            function imprimirCupomSitipet_{cod_limpo}() {{
                var targetId = 'cupom-sitipet-{cod_limpo}';
                var elem = document.getElementById(targetId) || window.parent.document.getElementById(targetId);
                var content = elem ? elem.outerHTML : '';
                var win = window.open('', '', 'height=750,width=480');
                win.document.write('<!DOCTYPE html><html><head><title>Cupom SitiPet - {pet_nome}</title>');
                win.document.write('<style>');
                win.document.write('@page {{ size: auto; margin: 5mm; }} body {{ font-family: \"Courier New\", Courier, monospace; background: white; margin: 0; padding: 10px; display: flex; justify-content: center; }}');
                win.document.write('</style>');
                win.document.write('</head><body>');
                win.document.write(content);
                win.document.write('</body></html>');
                win.document.close();
                win.focus();
                setTimeout(function () {{ win.print(); win.close(); }}, 350);
            }}
            </script>
        """, height=48)

    with col_btn2:
        link_wa = formatar_link_whatsapp(cliente_telefone, texto_wa)
        if link_wa:
            st.link_button("💬 Enviar no WhatsApp", link_wa, use_container_width=True)
        else:
            with st.popover("📋 Copiar Cupom", use_container_width=True):
                st.code(texto_wa, language="text")
                st.caption("Copie o texto e envie para o cliente.")

