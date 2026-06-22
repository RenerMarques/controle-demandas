import streamlit as st
from config import carregar_dados_demandas, carregar_dados_modelos
from datetime import datetime
import pandas as pd

# --- 1. CONFIGURAÇÃO E TEMA ---
st.set_page_config(
    page_title="Portal de Gestão Integrada", 
    page_icon="📡", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- 2. CSS CUSTOMIZADO (GLASMORFISMO & BACKGROUND) ---
# Substitua a URL abaixo pela URL de uma imagem de sua preferência se desejar.
# Esta é uma imagem abstrata de conexão de dados em tons escuros.
background_image_url = "https://images.unsplash.com/photo-1518770660439-4636190af475?q=80&w=2070&auto=format&fit=crop"

st.markdown(f"""
    <style>
        /* Imagem de Fundo com Blur */
        .stApp {{
            background-image: url("{background_image_url}");
            background-size: cover;
            background-position: center;
            background-attachment: fixed;
        }}
        .stApp::before {{
            content: "";
            position: absolute;
            top: 0; left: 0; width: 100%; height: 100%;
            background: rgba(0, 0, 0, 0.5); /* Filtro escuro sobre a imagem */
            backdrop-filter: blur(5px); /* Efeito de desfoque no fundo */
            z-index: -1;
        }}

        /* Cards estilo Glassmorphism */
        .glass-card {{
            background: rgba(255, 255, 255, 0.05);
            border-radius: 16px;
            box-shadow: 0 4px 30px rgba(0, 0, 0, 0.1);
            backdrop-filter: blur(10px);
            -webkit-backdrop-filter: blur(10px);
            border: 1px solid rgba(255, 255, 255, 0.1);
            padding: 20px;
            margin-bottom: 20px;
            color: white;
        }}
        
        /* Títulos e Textos dentro dos Cards */
        .glass-card h1, .glass-card h2, .glass-card h3 {{
            color: #00f2fe; /* Azul Neon */
            font-weight: 700;
        }}
        .glass-card p, .glass-card div {{
            color: #e0e0e0;
        }}

        /* Estilização das Métricas */
        [data-testid="stMetricValue"] {{
            color: #4facfe !important;
            font-size: 36px !important;
            font-weight: 800 !important;
        }}
        [data-testid="stMetricLabel"] {{
            color: #a0a0a0 !important;
        }}

        /* Botões Estilizados */
        .stButton>button {{
            border-radius: 12px;
            border: 1px solid #4facfe;
            background: rgba(79, 172, 254, 0.1);
            color: #4facfe;
            transition: 0.3s;
        }}
        .stButton>button:hover {{
            background: #4facfe;
            color: white;
            box-shadow: 0 0 15px #4facfe;
        }}
        
        /* Esconder o menu do Streamlit para um visual limpo */
        #MainMenu {{visibility: hidden;}}
        footer {{visibility: hidden;}}
        header {{visibility: hidden;}}

    </style>
    """, unsafe_allow_html=True)

# --- 3. CABEÇALHO (Em um Card de Vidro) ---
st.markdown('<div class="glass-card">', unsafe_allow_html=True)
col_tit1, col_tit2 = st.columns([3, 1])
with col_tit1:
    st.markdown("<h1>📡 Portal de Gestão Integrada</h1>", unsafe_allow_html=True)
    st.markdown(f"<p>Ambiente de Monitoramento e Controle | {datetime.now().strftime('%A, %d de %B de %Y')}</p>", unsafe_allow_html=True)
with col_tit2:
    st.write("") # Alinhamento
    if st.button("🔄 Recarregar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()
st.markdown('</div>', unsafe_allow_html=True)

# --- 4. DASHBOARD DE MÉTRICAS (Cards Individuais de Vidro) ---
df_d = carregar_dados_demandas()
df_m = carregar_dados_modelos()

m1, m2, m3, m4 = st.columns(4)

with m1:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.metric("📋 Total Demandas", len(df_d))
    st.markdown('</div>', unsafe_allow_html=True)
with m2:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.metric("🔧 Base Modelos", len(df_m))
    st.markdown('</div>', unsafe_allow_html=True)
with m3:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.metric("✅ Concluídas (Mês)", "14") # Exemplo
    st.markdown('</div>', unsafe_allow_html=True)
with m4:
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.metric("⏱️ Média SLA", "3.2 dias") # Exemplo
    st.markdown('</div>', unsafe_allow_html=True)

# --- 5. CORPO PRINCIPAL ---
col_main, col_side = st.columns([2, 1])

with col_main:
    # Acessos Rápidos em Cards Lado a Lado
    st.markdown("### 🚀 Acessos Rápidos")
    c_acc1, c_acc2 = st.columns(2)
    
    with c_acc1:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3>📁 Módulo Demandas</h3>", unsafe_allow_html=True)
        st.write("Fluxo de trabalho, prazos e responsáveis.")
        if st.button("Abrir Demandas", key="btn_dem", use_container_width=True):
            st.switch_page("pages/1_Demandas.py")
        st.markdown('</div>', unsafe_allow_html=True)

    with c_acc2:
        st.markdown('<div class="glass-card">', unsafe_allow_html=True)
        st.markdown("<h3>🔧 Módulo Modelos</h3>", unsafe_allow_html=True)
        st.write("Biblioteca técnica e especificações.")
        if st.button("Abrir Modelos", key="btn_mod", use_container_width=True):
            st.switch_page("pages/2_Modelos.py")
        st.markdown('</div>', unsafe_allow_html=True)

    # Nova Seção: Status do Projeto
    st.write("")
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h3>📊 Progresso da Versão atual (v1.2)</h3>", unsafe_allow_html=True)
    st.progress(0.75, text="75% Concluído")
    st.write("Faltam 3 demandas críticas para o deploy.")
    st.markdown('</div>', unsafe_allow_html=True)

with col_side:
    # Seção combinada de Avisos e Atualizações
    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h3>🔔 Avisos Rápidos</h3>", unsafe_allow_html=True)
    st.error("**Urgente:** Planilha de Modelos ficará offline amanhã das 08h às 09h para manutenção.")
    st.info("**SLA:** Lembre-se de atualizar o status das demandas concluídas.")
    st.markdown('</div>', unsafe_allow_html=True)

    st.markdown('<div class="glass-card">', unsafe_allow_html=True)
    st.markdown("<h3>🆕 Última Demanda</h3>", unsafe_allow_html=True)
    # Mostra apenas a linha mais recente
    if not df_d.empty:
        last_demand = df_d.iloc[[0]]
        st.dataframe(last_demand, use_container_width=True, hide_index=True)
    else:
        st.write("Nenhuma demanda cadastrada.")
    st.markdown('</div>', unsafe_allow_html=True)

# --- 6. RODAPÉ ---
st.markdown(
    "<div style='text-align: center; color: #808080; padding: 20px;'>© 2024 Portal de Gestão Integrada | Plataforma Monitorada v1.2</div>", 
    unsafe_allow_html=True
)