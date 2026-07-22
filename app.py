import streamlit as st
import logging
from config import carregar_dados_demandas, carregar_dados_modelos, carregar_maiores_capitulos

# Remover estas linhas:
# from alerts import exibir_alertas_sidebar, exibir_alertas_streamlit

# Configurar logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

st.set_page_config(page_title="Gestão Integrada", layout="wide")

st.title("🏠 Sistema de Gestão Integrada")
st.markdown("Bem-vindo ao painel central. Selecione um módulo abaixo para começar.")

# --- REMOVER ESTA SEÇÃO ---
# exibir_alertas_sidebar()

# --- MÉTRICAS ---
try:
    df_d = carregar_dados_demandas()
    df_m = carregar_dados_modelos()

    st.subheader("📊 Visão Geral")
    col1, col2, col3 = st.columns(3)
    col1.metric("📋 Demandas", len(df_d))
    col2.metric("🔧 Modelos", len(df_m))
    col3.metric("✅ Status", "Operacional")
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    logger.error(f"Erro ao carregar métricas: {e}", exc_info=True)

st.divider()

# --- REMOVER ESTA SEÇÃO ---
# st.subheader("🔔 Centro de Alertas")
# exibir_alertas_streamlit()
# st.divider()

# --- NAVEGAÇÃO E ATUALIZAÇÕES ---
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("🎯 Acesso Rápido")

    if st.button("📋 Módulo de Demandas", use_container_width=True):
        st.switch_page("pages/Demandas.py")

    if st.button("📚 Módulo de Capítulos", use_container_width=True):
        st.switch_page("pages/Capitulos.py")

    if st.button("🔧 Módulo de Modelos", use_container_width=True):
        st.switch_page("pages/Modelos.py")

    if st.button("📊 Dashboard Analítico", use_container_width=True):
        st.switch_page("pages/Dashboard.py")

    st.write("---")
    if st.button("🔄 Atualizar Dados", use_container_width=True):
        with st.spinner("Atualizando cache..."):
            st.cache_data.clear()
            st.success("✅ Cache atualizado!")
            st.rerun()

with col_right:
    st.subheader("📈 Atividade Recente")
    try:
        if not df_d.empty:
            colunas_visiveis = [c for c in df_d.columns if c != "_row"]
            st.dataframe(
                df_d[colunas_visiveis].head(5),
                use_container_width=True,
                hide_index=True
            )
        else:
            st.info("Nenhuma demanda cadastrada ainda.")
    except Exception as e:
        st.error(f"❌ Erro ao exibir atividade: {str(e)}")
        logger.error(f"Erro ao exibir atividade recente: {e}", exc_info=True)

# --- AVISOS ---
st.divider()
st.subheader("📢 Comunicados")
c_av1, c_av2 = st.columns(2)
with c_av1:
    st.warning("⚠️ Versão 2026/3 será lançada em 31 de Agosto!")
with c_av2:
    st.info("ℹ️ O sistema está operando com a versão estável mais recente.")

# --- MAIORES CAPÍTULOS ---
st.divider()
st.subheader("📈 Maiores Capítulos Utilizados")

with st.expander("📂 Ver lista de capítulos máximos por manual"):
    try:
        df_maiores = carregar_maiores_capitulos()

        if df_maiores.empty:
            st.info("Nenhum capítulo disponível ainda.")
        else:
            df_display = df_maiores.sort_values(by='CAP_NUM', ascending=False)
            st.dataframe(
                df_display[['MANUAL', 'CAPITULO']],
                use_container_width=True,
                hide_index=True
            )
    except Exception as e:
        st.error(f"❌ Erro ao carregar capítulos: {str(e)}")
        logger.error(f"Erro ao carregar maiores capítulos: {e}", exc_info=True)

# --- RODAPÉ ---
st.divider()
st.write("© 2026 Gestão Integrada | Versão 1.0.0")