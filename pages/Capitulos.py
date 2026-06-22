import streamlit as st
from config import sheet_capitulos, carregar_dados_capitulos, LISTA_MANUAIS

st.set_page_config(page_title="Gestão de Capítulos", layout="wide")

st.title("📚 Capítulos - Controle de Sobras")
st.markdown("Cadastro de capítulos e vínculo com demandas.")

# Carrega os dados
df_cap = carregar_dados_capitulos()

# --- ABAS ---
tab1, tab2 = st.tabs(["➕ Novo Cadastro", "📋 Lista de Capítulos"])

with tab1:
    with st.form("form_add_cap", clear_on_submit=True):
        c_manual = st.selectbox("Manual", LISTA_MANUAIS)
        c_capitulo = st.text_input("Capítulo")
        c_demanda = st.text_input("USADO NA DEMANDA (Descrição)")
        
        if st.form_submit_button("Salvar Registro"):
            if c_capitulo:
                # Insere na planilha (Manual, Capitulo, Demanda)
                sheet_capitulos.insert_row([c_manual, c_capitulo, c_demanda], index=2)
                st.success("Cadastro realizado com sucesso!")
                st.cache_data.clear()
            else:
                st.error("O campo Capítulo é obrigatório.")

with tab2:
    st.subheader("Registros Cadastrados")
    df_cap = carregar_dados_capitulos() # Recarrega para mostrar o novo dado
    
    # Busca rápida
    busca = st.text_input("🔍 Buscar no cadastro")
    
    if busca:
        df_show = df_cap[df_cap.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)]
    else:
        df_show = df_cap
        
    st.dataframe(df_show, use_container_width=True, hide_index=True)
    
    if st.button("🔄 Recarregar Dados"):
        st.cache_data.clear()
        st.rerun()