import streamlit as st
from config import carregar_dados_demandas, carregar_dados_modelos
from datetime import datetime

# --- CONFIGURAÇÃO CLEAN ---
st.set_page_config(
    page_title="Gestão Integrada",
    layout="wide"
)

# Estilização minimalista (Sem imagens, sem borrão, apenas foco)
st.markdown("""
    <style>
        .main { background-color: #f8f9fa; }
        .stMetric { background-color: #ffffff; padding: 20px; border-radius: 8px; border: 1px solid #e9ecef; }
        h1 { color: #343a40; font-weight: 600; }
        h3 { color: #495057; }
    </style>
    """, unsafe_allow_html=True)

# --- CABEÇALHO ---
st.title("Sistema de Gestão")
st.caption(f"Painel administrativo atualizado em {datetime.now().strftime('%d/%m/%Y %H:%M')}")
st.divider()

# --- MÉTRICAS ---
df_d = carregar_dados_demandas()
df_m = carregar_dados_modelos()

c1, c2, c3 = st.columns(3)
c1.metric("Demandas Cadastradas", len(df_d))
c2.metric("Modelos na Base", len(df_m))
c3.metric("Status do Sistema", "Online")

st.write("") # Espaçamento

# --- CORPO ---
col1, col2 = st.columns([2, 1])

with col1:
    st.subheader("Navegação")
    c_a, c_b = st.columns(2)
    with c_a:
        if st.button("📁 Módulo de Demandas", use_container_width=True):
            st.switch_page("pages/1_Demandas.py")
    with c_b:
        if st.button("🔧 Módulo de Modelos", use_container_width=True):
            st.switch_page("pages/2_Modelos.py")
            
    st.write("")
    st.subheader("Atividade Recente")
    st.dataframe(df_d.head(5), use_container_width=True, hide_index=True)

with col2:
    st.subheader("Avisos")
    st.info("O sistema está sincronizado com a base de dados principal.")
    st.warning("Verifique as demandas com prazo de entrega para esta semana.")
    
    if st.button("🔄 Atualizar dados da tela"):
        st.cache_data.clear()
        st.rerun()

# --- RODAPÉ ---
st.divider()
st.write("© 2026 Gestão Integrada")