import streamlit as st
from config import carregar_dados_demandas, carregar_dados_modelos
from datetime import datetime

# --- 1. CONFIGURAÇÃO DE IDENTIDADE E TEMA ---
st.set_page_config(
    page_title="Gestão Integrada", 
    page_icon="🏢", 
    layout="wide",
)

# --- 2. ESTILIZAÇÃO CUSTOMIZADA (CSS) ---
# Aqui definimos o fundo e melhoramos a aparência dos cartões
st.markdown("""
    <style>
        /* Fundo da página com um degradê moderno */
        .stApp {
            background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
        }
        
        /* Estilização dos blocos de métricas */
        [data-testid="stMetricValue"] {
            font-size: 28px;
            color: #1E3A8A;
        }
        
        /* Deixar os botões levemente arredondados */
        .stButton>button {
            border-radius: 10px;
        }
    </style>
    """, unsafe_allow_html=True)

# --- 3. CABEÇALHO ---
col_logo, col_titulo = st.columns([1, 4])
with col_titulo:
    st.title("🏢 Sistema de Gestão Integrada")
    st.write(f"Hoje é dia {datetime.now().strftime('%d/%m/%Y')}")

st.markdown("---")

# --- 4. DASHBOARD DE MÉTRICAS ---
df_d = carregar_dados_demandas()
df_m = carregar_dados_modelos()

c1, c2, c3, c4 = st.columns(4)
c1.metric("📋 Demandas", len(df_d))
c2.metric("🔧 Modelos", len(df_m))
c3.metric("✅ Concluídas", "12") # Exemplo estático
c4.metric("⚠️ Pendentes", "05")  # Exemplo estático

st.markdown("---")

# --- 5. CORPO PRINCIPAL (Acessos e Avisos) ---
col_principal, col_lateral = st.columns([2, 1])

with col_principal:
    st.subheader("📁 Acessos Rápidos")
    
    col_a, col_b = st.columns(2)
    with col_a:
        with st.container(border=True):
            st.markdown("### 📋 Demandas")
            st.write("Controle total do fluxo de trabalho.")
            if st.button("Abrir Módulo", key="btn_dem", use_container_width=True, type="primary"):
                st.switch_page("pages/1_Demandas.py")

    with col_b:
        with st.container(border=True):
            st.markdown("### 🔧 Modelos")
            st.write("Base de dados técnica e manuais.")
            if st.button("Abrir Módulo", key="btn_mod", use_container_width=True, type="primary"):
                st.switch_page("pages/2_Modelos.py")

    # Seção de Últimas Atualizações
    st.write("")
    st.subheader("🆕 Últimas Atualizações")
    # Aqui você pode listar as últimas 3 linhas do seu DF de demandas, por exemplo
    st.dataframe(df_d.head(3), use_container_width=True, hide_index=True)

with col_lateral:
    # Seção de Avisos Rápidos
    st.subheader("🔔 Avisos Rápidos")
    
    with st.expander("📌 Manutenção de Planilha", expanded=True):
        st.write("A sincronização ocorrerá hoje às 22h.")
        
    st.info("**Dica:** Use o módulo de Modelos para baixar relatórios em PDF.")
    
    st.warning("**Atenção:** Verifique as demandas atrasadas da Versão 1.0.")
    
    if st.button("Recarregar Dados", use_container_width=True):
        st.cache_data.clear()
        st.rerun()

# --- 6. RODAPÉ ---
st.markdown("---")
st.markdown(
    "<div style='text-align: center; color: grey;'>© 2024 Gestão Integrada | Desenvolvido com Streamlit</div>", 
    unsafe_allow_html=True
)