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
            with col1:
                c_manual = st.selectbox("Manual", LISTA_MANUAIS)
            with col2:
                c_capitulo = st.text_input("Capítulo")
            with col3:
                c_demanda = st.text_input("USADO NA DEMANDA")

            if st.form_submit_button("Salvar Capítulo"):
                if not c_capitulo.strip():
                    st.error("O campo Capítulo é obrigatório.")
                else:
                    try:
                        sheet_capitulos.insert_row([c_manual, c_capitulo, c_demanda], index=2)
                        st.cache_data.clear()  # Limpa o cache para mostrar o novo item
                        st.success("Salvo com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")

    # LISTA ABAIXO DO CADASTRO
    st.subheader("Registros Cadastrados")
    df_cap = carregar_dados_capitulos()

    if df_cap.empty:
        st.info("Nenhum capítulo cadastrado ainda.")
    else:
        # Busca simples
        busca = st.text_input("🔍 Buscar no cadastro (Filtro por título/manual)")
        colunas_visiveis = [c for c in df_cap.columns if c != "_row"]

        if busca:
            df_show = df_cap[
                df_cap[colunas_visiveis].astype(str)
                .apply(lambda x: x.str.contains(busca, case=False, regex=False, na=False))
                .any(axis=1)
            ]
        else:
            df_show = df_cap

        st.dataframe(df_show[colunas_visiveis], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("Alterar ou Remover Registro")
    df_edit = carregar_dados_capitulos()

    if df_edit.empty:
        st.info("Nenhum capítulo cadastrado ainda.")
    else:
        # Seleção do registro pelo nome do capítulo
        cap_lista = df_edit["CAPITULO"].tolist()
        cap_sel = st.selectbox("Selecione o capítulo para editar/excluir:", [""] + cap_lista)

        if cap_sel:
            dados = df_edit[df_edit["CAPITULO"] == cap_sel].iloc[0]
            linha_alvo = dados["_row"]  # localização estável do registro na planilha

            with st.form("form_edit"):
                e_man = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados["MANUAL"]) if dados["MANUAL"] in LISTA_MANUAIS else 0)
                e_cap = st.text_input("Título do Capítulo", value=dados["CAPITULO"])
                e_dem = st.text_input("USADO NA DEMANDA", value=dados["USADO NA DEMANDA"])

                if st.form_submit_button("Atualizar Dados"):
                    if not e_cap.strip():
                        st.error("O campo Capítulo é obrigatório.")
                    else:
                        try:
                            sheet_capitulos.update(range_name=f"A{linha_alvo}:C{linha_alvo}", values=[[e_man, e_cap, e_dem]])
                            st.cache_data.clear()
                            st.success("Registro atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")

            st.divider()
            confirmar_exclusao = st.checkbox(
                "Confirmo que quero excluir este registro permanentemente.", key="confirma_del_cap"
            )
            if st.button("🗑️ Excluir este registro permanentemente", type="primary"):
                if not confirmar_exclusao:
                    st.error("Marque a confirmação antes de excluir.")
                else:
                    try:
                        sheet_capitulos.delete_rows(int(linha_alvo))
                        st.cache_data.clear()
                        st.success("Registro removido!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")