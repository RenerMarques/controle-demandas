import streamlit as st
from config import sheet_capitulos, carregar_dados_capitulos, LISTA_MANUAIS

st.set_page_config(page_title="Gestão de Capítulos", layout="wide")

st.title("📚 Capítulos - Controle de Sobras")

# --- ABAS ---
tab1, tab2 = st.tabs(["➕ Cadastrar & Listar", "✏️ Editar/Excluir"])

with tab1:
    # FORMULÁRIO DE CADASTRO
    with st.expander("Nova Entrada", expanded=True):
        with st.form("form_add_cap", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1: c_manual = st.selectbox("Manual", LISTA_MANUAIS)
            with col2: c_capitulo = st.text_input("Capítulo")
            with col3: c_demanda = st.text_input("USADO NA DEMANDA")
            
            if st.form_submit_button("Salvar Capítulo"):
                if c_capitulo:
                    sheet_capitulos.insert_row([c_manual, c_capitulo, c_demanda], index=2)
                    st.success("Salvo com sucesso!")
                    st.cache_data.clear() # Limpa o cache para mostrar o novo item
                else:
                    st.error("O campo Capítulo é obrigatório.")

    # LISTA ABAIXO DO CADASTRO
    st.subheader("Registros Cadastrados")
    df_cap = carregar_dados_capitulos()
    
    # Busca simples
    busca = st.text_input("🔍 Buscar no cadastro (Filtro por título/manual)")
    df_show = df_cap[df_cap.astype(str).apply(lambda x: x.str.contains(busca, case=False)).any(axis=1)] if busca else df_cap
    
    st.dataframe(df_show, use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Alterar ou Remover Registro")
    df_edit = carregar_dados_capitulos()
    
    # Seleção do registro pelo nome do capítulo
    cap_lista = df_edit["CAPITULO"].tolist()
    cap_sel = st.selectbox("Selecione o capítulo para editar/excluir:", [""] + cap_lista)
    
    if cap_sel:
        dados = df_edit[df_edit["CAPITULO"] == cap_sel].iloc[0]
        
        with st.form("form_edit"):
            e_man = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados["MANUAL"]))
            e_cap = st.text_input("Título do Capítulo", value=dados["CAPITULO"])
            e_dem = st.text_input("USADO NA DEMANDA", value=dados["USADO NA DEMANDA"])
            
            if st.form_submit_button("Atualizar Dados"):
                cell = sheet_capitulos.find(cap_sel)
                sheet_capitulos.update(range_name=f"A{cell.row}:C{cell.row}", values=[[e_man, e_cap, e_dem]])
                st.success("Registro atualizado!")
                st.cache_data.clear()
                st.rerun()

        st.divider()
        if st.button("🗑️ Excluir este registro permanentemente", type="primary"):
            cell = sheet_capitulos.find(cap_sel)
            sheet_capitulos.delete_rows(cell.row)
            st.success("Registro removido!")
            st.cache_data.clear()
            st.rerun()