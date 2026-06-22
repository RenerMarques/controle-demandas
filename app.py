import streamlit as st
from config import carregar_dados_demandas, carregar_dados_modelos

# --- 1. CONFIGURAÇÃO DE IDENTIDADE ---
st.set_page_config(
    page_title="Gestão Integrada", 
    page_icon="🏢", 
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- 2. CABEÇALHO COM LOGO E MENSAGEM ---
# Caso tenha uma logo, coloque o arquivo na pasta raiz e descomente a linha abaixo:
# st.image("logo.png", width=200)

st.title("🏢 Sistema de Gestão Integrada")
st.markdown("""
Esta é a plataforma central para controle de processos. 
Nossa missão é otimizar o fluxo de trabalho através de uma navegação intuitiva e dados atualizados.
""")
st.markdown("---")

# --- 3. DASHBOARD DE MÉTRICAS (Revisado) ---
df_d = carregar_dados_demandas()
df_m = carregar_dados_modelos()

# Estilização das métricas
c1, c2, c3 = st.columns(3)
c1.metric("Demandas em Aberto", len(df_d), delta="Atualizado")
c2.metric("Base de Modelos", len(df_m), delta="Ativo")
c3.metric("Ambiente", "Produção", help="Sistema operando via Google Sheets")

st.markdown("---")

# --- 4. ACESSO RÁPIDO (Melhoria 1) ---
# Usando um estilo visual mais limpo (Cards com Container)
col1, col2 = st.columns(2)

with col1:
    with st.container(border=True):
        st.subheader("📋 Módulo de Demandas")
        st.write("Acompanhe, crie e edite as demandas de trabalho.")
        if st.button("Ir para Demandas", use_container_width=True, type="primary"):
            st.switch_page("pages/1_Demandas.py")

with col2:
    with st.container(border=True):
        st.subheader("🔧 Módulo de Modelos")
        st.write("Gerencie a base de modelos e especificações técnicas.")
        if st.button("Ir para Modelos", use_container_width=True, type="primary"):
            st.switch_page("pages/2_Modelos.py")

# Rodapé simples
st.markdown("---")
st.caption("Sistema de Gestão Integrada | Versão 1.0")