"""
Módulo de Emissão de Comprovantes e Notas - SitiPet
Gera recibos formatados para impressão (PDF/Impressora) e envio via WhatsApp.
"""

import streamlit as st
from utils.financeiro import formatar_moeda
from utils.datas import format_date_br

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
    codigo_recibo: str = ""
) -> str:
    """Gera o HTML estilizado pronto para impressão térmica/A4."""
    itens = itens or []
    
    itens_html = ""
    for item in itens:
        nome_item = item.get("nome", "Serviço")
        val_item = item.get("valor", 0.0)
        itens_html += f"""
        <tr>
            <td style="padding: 6px 0; border-bottom: 1px dashed #e2e8f0; font-size: 13px; color: #1e293b;">{nome_item}</td>
            <td style="padding: 6px 0; border-bottom: 1px dashed #e2e8f0; text-align: right; font-size: 13px; font-weight: 700; color: #1e293b;">{formatar_moeda(val_item)}</td>
        </tr>
        """

    html = f"""
    <div id="comprovante-print-{codigo_recibo}" style="max-width: 380px; margin: 0 auto; background: #ffffff; padding: 24px 20px; border: 1px solid #e2e8f0; border-radius: 12px; font-family: 'Courier New', Courier, monospace, sans-serif; box-shadow: 0 4px 12px rgba(0,0,0,0.05); color: #1e293b;">
        <!-- CABEÇALHO -->
        <div style="text-align: center; border-bottom: 2px dashed #94a3b8; padding-bottom: 12px; margin-bottom: 12px;">
            <div style="font-size: 20px; font-weight: 900; letter-spacing: 1px; color: #253b80;">🐾 SITIPET</div>
            <div style="font-size: 12px; font-weight: 700; color: #d82678;">PET SHOP E HOTELZINHO</div>
            <div style="font-size: 11px; color: #64748b; margin-top: 3px;">Cuidando com carinho do seu melhor amigo</div>
            <div style="font-size: 11px; color: #475569; margin-top: 4px; font-weight: 600;">{titulo.upper()}</div>
        </div>

        <!-- DADOS DO ATENDIMENTO -->
        <div style="font-size: 12px; line-height: 1.5; margin-bottom: 12px; border-bottom: 1px dashed #cbd5e1; padding-bottom: 10px;">
            <div><b>Recibo N°:</b> #{codigo_recibo}</div>
            <div><b>Data:</b> {format_date_br(data_servico)}</div>
            <div><b>Cliente/Tutor:</b> {cliente_nome}</div>
            {f'<div><b>Telefone:</b> {cliente_telefone}</div>' if cliente_telefone else ''}
            <div><b>Pet:</b> {pet_nome} {f'({raca} - {porte})' if raca or porte else ''}</div>
            {f'<div><b>Profissional:</b> {profissional}</div>' if profissional else ''}
        </div>

        <!-- LISTA DE SERVIÇOS -->
        <div style="margin-bottom: 12px;">
            <div style="font-size: 12px; font-weight: 800; border-bottom: 1px solid #1e293b; padding-bottom: 3px; margin-bottom: 6px; display: flex; justify-content: space-between;">
                <span>DESCRIÇÃO DOS SERVIÇOS</span>
                <span>VALOR</span>
            </div>
            <table style="width: 100%; border-collapse: collapse;">
                {itens_html}
            </table>
        </div>

        <!-- TOTAL E FORMA DE PAGAMENTO -->
        <div style="border-top: 2px dashed #94a3b8; padding-top: 10px; margin-top: 10px;">
            <div style="display: flex; justify-content: space-between; font-size: 16px; font-weight: 900; color: #1e293b;">
                <span>TOTAL:</span>
                <span>{formatar_moeda(valor_total)}</span>
            </div>
            <div style="display: flex; justify-content: space-between; font-size: 12px; color: #475569; margin-top: 4px;">
                <span>Forma de Pagamento:</span>
                <span><b>{forma_pagamento}</b></span>
            </div>
        </div>

        {f'<div style="margin-top: 10px; font-size: 11px; color: #64748b; background: #f8fafc; padding: 6px 8px; border-radius: 6px;"><b>Obs:</b> {observacoes}</div>' if observacoes else ''}

        <!-- RODAPÉ -->
        <div style="text-align: center; margin-top: 18px; border-top: 1px dashed #cbd5e1; padding-top: 12px; font-size: 11px; color: #64748b;">
            <p style="margin: 0; font-weight: 700; color: #1e293b;">Obrigado pela preferência! 🐶❤️</p>
            <p style="margin: 3px 0 0 0;">Volte sempre ao SitiPet!</p>
        </div>
    </div>
    """
    return html

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
    codigo_recibo: str = ""
):
    """Exibe o comprovante na tela com botão de imprimir e texto para WhatsApp."""
    html_recibo = gerar_html_comprovante(
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
        codigo_recibo=codigo_recibo
    )

    st.markdown(html_recibo, unsafe_allow_html=True)
    
    st.markdown("<div style='height: 12px;'></div>", unsafe_allow_html=True)
    
    # Gerar texto formatado para envio no WhatsApp
    itens_txt = "\n".join([f"• {it.get('nome')}: {formatar_moeda(it.get('valor', 0))}" for it in (itens or [])])
    texto_whatsapp = f"""*🐾 SITIPET - COMPROVANTE DE SERVIÇOS 🐾*
Recibo #{codigo_recibo} | Data: {format_date_br(data_servico)}

*Cliente:* {cliente_nome}
*Pet:* {pet_nome} ({porte})
*Profissional:* {profissional}

*Serviços Realizados:*
{itens_txt}

*TOTAL:* {formatar_moeda(valor_total)} ({forma_pagamento})

Obrigado pela preferência e carinho com o seu pet! 🐶❤️"""

    col_btn1, col_btn2 = st.columns(2)
    with col_btn1:
        # Botão de impressão nativa via JavaScript
        st.components.v1.html(f"""
            <button onclick="imprimirRecibo()" style="width: 100%; background-color: #253b80; color: white; border: none; padding: 10px 16px; border-radius: 8px; font-weight: 700; cursor: pointer; font-size: 14px; display: flex; align-items: center; justify-content: center; gap: 8px;">
                🖨️ Imprimir Comprovante / PDF
            </button>
            <script>
            function imprimirRecibo() {{
                var printContents = document.getElementById('comprovante-print-{codigo_recibo}') ? 
                    document.getElementById('comprovante-print-{codigo_recibo}').outerHTML : 
                    window.parent.document.getElementById('comprovante-print-{codigo_recibo}').outerHTML;
                var win = window.open('', '', 'height=650,width=450');
                win.document.write('<html><head><title>Comprovante SitiPet</title>');
                win.document.write('<style>body {{ font-family: monospace; padding: 20px; }} @media print {{ @page {{ margin: 0; }} }}</style>');
                win.document.write('</head><body>');
                win.document.write(printContents);
                win.document.write('</body></html>');
                win.document.close();
                win.focus();
                setTimeout(function () {{ win.print(); win.close(); }}, 300);
            }}
            </script>
        """, height=50)

    with col_btn2:
        with st.popover("📱 Copiar p/ WhatsApp", use_container_width=True):
            st.code(texto_whatsapp, language="text")
            st.caption("Copie o texto acima e envie pelo WhatsApp do cliente.")
