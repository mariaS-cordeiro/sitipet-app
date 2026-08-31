"""
SitiPet - Aplicativo de Gestão para Pet Shop e Hotelzinho
Interface Streamlit principal com navegação fluida, branding e persistência de dados.
"""

import streamlit as st
import os
from PIL import Image

# Configuração da Página
st.set_page_config(
    page_title="SitiPet - Pet Shop e Hotelzinho",
    page_icon="🐾",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Estilização CSS Customizada SitiPet
st.markdown("""
<style>
    /* Estilos Gerais SitiPet */
    @import url('https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&display=swap');
    
    html, body, [class*="css"] {
        font-family: 'Plus Jakarta Sans', sans-serif;
    }

    /* Cores de Fundo */
    .stApp {
        background-color: #f8fafc;
    }

    /* KPI Cards */
    .kpi-card {
        background-color: #ffffff;
        border-radius: 14px;
        padding: 18px 20px;
        box-shadow: 0 2px 10px rgba(0, 0, 0, 0.04);
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    .kpi-card:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 16px rgba(0, 0, 0, 0.08);
    }

    /* Botões Primários */
    div.stButton > button[kind="primary"] {
        background-color: #d82678 !important;
        border-color: #d82678 !important;
        color: white !important;
        font-weight: 700 !important;
        border-radius: 10px !important;
        padding: 8px 18px !important;
        transition: all 0.2s ease;
    }
    div.stButton > button[kind="primary"]:hover {
        background-color: #be185d !important;
        border-color: #be185d !important;
        transform: scale(1.02);
    }

    /* Botões Secundários */
    div.stButton > button[kind="secondary"] {
        border-radius: 10px !important;
        font-weight: 600 !important;
    }

    /* Estilização da Sidebar */
    section[data-testid="stSidebar"] {
        background-color: #ffffff;
        border-right: 1px solid #e2e8f0;
    }

    /* Ajuste de Headers */
    h1, h2, h3, h4 {
        color: #1e293b;
        font-weight: 800;
    }

    /* Estilo de Expander */
    .streamlit-expanderHeader {
        background-color: #ffffff !important;
        border-radius: 10px !important;
        font-weight: 700 !important;
        color: #1e293b !important;
    }
</style>
""", unsafe_allow_html=True)

# Importar as visões
from views.dashboard_view import render_dashboard
from views.agenda_view import render_agenda
from views.banho_tosa_view import render_banho_tosa
from views.hospedagem_view import render_hospedagem
from views.caixa_view import render_caixa
from views.config_view import render_config
from utils.storage import get_storage_status

# ==================== SIDEBAR ====================
with st.sidebar:
    # Logo SitiPet
    logo_path = os.path.join(os.path.dirname(__file__), "assets", "logo.png")
    if os.path.exists(logo_path):
        try:
            image = Image.open(logo_path)
            st.image(image, use_container_width=True)
        except Exception:
            st.markdown("## 🐾 **SitiPet**\n*Pet Shop e Hotelzinho*")
    else:
        st.markdown("## 🐾 **SitiPet**\n*Pet Shop e Hotelzinho*")

    st.markdown("<div style='height: 10px;'></div>", unsafe_allow_html=True)
    st.markdown("### 📌 Navegação")

    # Menu de Navegação
    opcao_menu = st.radio(
        "Selecione uma área:",
        [
            "📊 Início / Painel Geral",
            "📅 Aba 1 – Agenda Diária",
            "✂️ Aba 2 – Banho e Tosa",
            "🏨 Aba 3 – Hospedagem / Hotel",
            "💰 Aba 4 – Caixa e Finanças",
            "⚙️ Configurações & Nuvem"
        ],
        index=0,
        label_visibility="collapsed"
    )

    st.divider()

    # Status de Conexão
    status_db = get_storage_status()
    st.caption(f"**Persistência:** {status_db['status_label']}")
    st.caption("📧 Conta: `sitipet01@gmail.com`")
    st.caption("Versão: **SitiPet 2.0 Pro**")

# ==================== RENDERIZAÇÃO DA VISÃO SELECIONADA ====================
if opcao_menu == "📊 Início / Painel Geral":
    render_dashboard()
elif opcao_menu == "📅 Aba 1 – Agenda Diária":
    render_agenda()
elif opcao_menu == "✂️ Aba 2 – Banho e Tosa":
    render_banho_tosa()
elif opcao_menu == "🏨 Aba 3 – Hospedagem / Hotel":
    render_hospedagem()
elif opcao_menu == "💰 Aba 4 – Caixa e Finanças":
    render_caixa()
elif opcao_menu == "⚙️ Configurações & Nuvem":
    render_config()
