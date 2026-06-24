import streamlit as st
from config import carregar_dados_demandas, carregar_dados_modelos, carregar_maiores_capitulos
from datetime import datetime

st.set_page_config(page_title="Gestão Integrada", layout="wide")

# --- CABEÇALHO ---
st.title("Sistema de Gestão")
st.markdown("Bem-vindo ao painel central. Selecione um módulo abaixo para começar.")

# --- MÉTRICAS (Uso do componente nativo - Alta legibilidade) ---
df_d = carregar_dados_demandas()
df_m = carregar_dados_modelos()

st.subheader("Visão Geral")
col1, col2, col3 = st.columns(3)
col1.metric("Demandas", len(df_d))
col2.metric("Modelos", len(df_m))
col3.metric("Status", "Operacional")

st.divider()

# --- NAVEGAÇÃO E ATUALIZAÇÕES ---
# Dividimos a tela para separar o que é AÇÃO do que é INFORMAÇÃO
col_left, col_right = st.columns([1, 2])

with col_left:
    st.subheader("Acesso")
    # Botões estilizados nativamente sem CSS complexo
    if st.button("📁 Módulo de Demandas", use_container_width=True):
        st.switch_page("pages/Demandas.py")
    
    if st.button("🔧 Módulo de Modelos", use_container_width=True):
        st.switch_page("pages/Modelos.py")

    if st.button("📚 Módulo de Capítulos", use_container_width=True):
        st.switch_page("pages/Capitulos.py")

    st.write("---")
    if st.button("🔄 Atualizar dados"):
        st.cache_data.clear()
        st.rerun()

with col_right:
    st.subheader("Atividade Recente")
    # Exibe apenas as colunas mais importantes para não poluir
    if not df_d.empty:
        st.dataframe(
            df_d.head(5), 
            use_container_width=True, 
            hide_index=True
        )
    else:
        st.info("Nenhum dado disponível.")

# --- AVISOS ---
st.divider()
st.subheader("Comunicados")
c_av1, c_av2 = st.columns(2)
with c_av1:
    st.warning("Versão 2026/3 será lançada em 31 de Agosto!")
with c_av2:
    st.info("O sistema está operando com a versão estável mais recente.")

# --- NOVA SEÇÃO: ÚLTIMOS CAPÍTULOS POR MANUAL ---
st.subheader("📈 Maiores Capítulos Utilizados")

# No seu app.py, dentro do expander:
with st.expander("Ver lista de capítulos máximos por manual"):
    df_maiores = carregar_maiores_capitulos()
    
    # Ordenamos pela coluna numérica, mas mostramos os dados originais
    df_display = df_maiores.sort_values(by='CAP_NUM', ascending=False)
    
    st.dataframe(
        df_display[['MANUAL', 'CAPITULO']], # Exibe apenas as colunas amigáveis
        use_container_width=True, 
        hide_index=True
    )

# --- RODAPÉ ---
st.divider()
st.write("© 2026 Gestão Integrada")