import streamlit as st
from config import carregar_dados_demandas, carregar_dados_modelos

st.set_page_config(page_title="Sistema de Gestão", layout="wide", page_icon="🚀")

# --- TÍTULO E CABEÇALHO ---
st.title("🚀 Sistema de Gestão Integrada")
st.markdown("Bem-vindo ao painel central de controle. Utilize os acessos rápidos abaixo para navegar.")
st.markdown("---")

# --- 2. DASHBOARD DE MÉTRICAS (Melhoria 2) ---
# Carregamos os dados de forma otimizada
df_d = carregar_dados_demandas()
df_m = carregar_dados_modelos()

col_m1, col_m2, col_m3 = st.columns(3)
col_m1.metric("Total de Demandas", len(df_d))
col_m2.metric("Total de Modelos", len(df_m))
col_m3.metric("Status do Sistema", "Online", "Operacional")

st.markdown("---")

# --- 1. ACESSO RÁPIDO (Melhoria 1) ---
st.subheader("📁 Acesso Rápido")
c1, c2 = st.columns(2)

with c1:
    st.write("### 📋 Módulo de Demandas")
    st.write("Gerencie o fluxo de demandas, adicione novos registros e consulte o histórico.")
    if st.button("Acessar Demandas", use_container_width=True):
        st.switch_page("pages/1_Demandas.py")

with c2:
    st.write("### 🔧 Módulo de Modelos")
    st.write("Consulte, adicione ou edite a base de modelos do seu sistema.")
    if st.button("Acessar Modelos", use_container_width=True):
        st.switch_page("pages/2_Modelos.py")

# Rodapé simples
st.markdown("---")
st.caption("Sistema de Gestão Integrada | Versão 1.0")