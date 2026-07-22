import streamlit as st
import gspread
import logging
from config import sheet_capitulos, carregar_dados_capitulos, LISTA_MANUAIS

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Gestão de Capítulos", layout="wide")
st.title("📚 Capítulos - Controle de Sobras")

# --- FUNÇÕES AUXILIARES ---
def get_selectbox_index(lista, valor, nome_campo):
    """Retorna o índice seguro para selectbox."""
    try:
        return lista.index(valor)
    except ValueError:
        st.warning(f"⚠️ '{valor}' não está na lista de {nome_campo}. Usando padrão.")
        logger.warning(f"Valor '{valor}' não encontrado em {nome_campo}")
        return 0


def validar_capitulo(manual, capitulo, demanda):
    """Valida campos obrigatórios."""
    erros = []
    if not capitulo.strip():
        erros.append("Capítulo é obrigatório")

    if erros:
        st.error("❌ Erros de validação:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True


# --- ABAS ---
tab1, tab2 = st.tabs(["➕ Cadastrar & Listar", "✏️ Editar/Excluir"])

with tab1:
    # FORMULÁRIO DE CADASTRO
    with st.expander("📝 Nova Entrada", expanded=True):
        with st.form("form_add_cap", clear_on_submit=True):
            col1, col2, col3 = st.columns(3)
            with col1:
                c_manual = st.selectbox("Manual", LISTA_MANUAIS)
            with col2:
                c_capitulo = st.text_input("Capítulo").strip()
            with col3:
                c_demanda = st.text_input("USADO NA DEMANDA").strip()

            if st.form_submit_button("💾 Salvar Capítulo"):
                if validar_capitulo(c_manual, c_capitulo, c_demanda):
                    with st.spinner("Salvando..."):
                        try:
                            sheet_capitulos.insert_row([c_manual, c_capitulo, c_demanda], index=2)
                            st.cache_data.clear()
                            st.success("✅ Capítulo salvo com sucesso!")
                            logger.info(f"Capítulo criado: {c_manual} - {c_capitulo}")
                        except gspread.exceptions.APIError:
                            st.error("❌ Erro na API do Google Sheets. Tente novamente em alguns segundos.")
                            logger.error("Erro de API ao salvar capítulo")
                        except gspread.exceptions.SpreadsheetNotFound:
                            st.error("❌ Planilha não encontrada. Verifique o ID.")
                            logger.error("Planilha não encontrada ao salvar capítulo")
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {str(e)}")
                            logger.error(f"Erro ao salvar capítulo: {e}", exc_info=True)

    # LISTA ABAIXO DO CADASTRO
    st.subheader("📋 Registros Cadastrados")
    df_cap = carregar_dados_capitulos()

    if df_cap.empty:
        st.info("Nenhum capítulo cadastrado ainda.")
    else:
        # Busca simples
        busca = st.text_input("🔍 Buscar no cadastro (Filtro por título/manual)").strip().lower()
        colunas_visiveis = [c for c in df_cap.columns if c != "_row"]

        if busca:
            df_show = df_cap[
                df_cap[colunas_visiveis].astype(str)
                .apply(lambda x: x.str.contains(busca, case=False, regex=False, na=False))
                .any(axis=1)
            ]
        else:
            df_show = df_cap

        st.write(f"**Total de registros:** {len(df_show)}")
        st.dataframe(df_show[colunas_visiveis], use_container_width=True, hide_index=True)

with tab2:
    st.subheader("✏️ Alterar ou Remover Registro")
    df_edit = carregar_dados_capitulos()

    if df_edit.empty:
        st.info("Nenhum capítulo cadastrado ainda.")
    else:
        # Seleção do registro pelo nome do capítulo
        cap_lista = df_edit["CAPITULO"].tolist()
        cap_sel = st.selectbox("Selecione o capítulo para editar/excluir:", [""] + cap_lista)

        if cap_sel:
            dados = df_edit[df_edit["CAPITULO"] == cap_sel].iloc[0]
            linha_alvo = int(dados["_row"])

            with st.form("form_edit"):
                try:
                    idx = LISTA_MANUAIS.index(dados["MANUAL"])
                except ValueError:
                    st.warning(f"⚠️ Manual '{dados['MANUAL']}' não está na lista padrão.")
                    idx = 0

                e_man = st.selectbox("Manual", LISTA_MANUAIS, index=idx)
                e_cap = st.text_input("Título do Capítulo", value=str(dados["CAPITULO"])).strip()
                e_dem = st.text_input("USADO NA DEMANDA", value=str(dados["USADO NA DEMANDA"])).strip()

                if st.form_submit_button("💾 Atualizar Dados"):
                    if validar_capitulo(e_man, e_cap, e_dem):
                        with st.spinner("Atualizando..."):
                            try:
                                sheet_capitulos.update(
                                    range_name=f"A{linha_alvo}:C{linha_alvo}",
                                    values=[[e_man, e_cap, e_dem]]
                                )
                                st.cache_data.clear()
                                st.success("✅ Registro atualizado com sucesso!")
                                logger.info(f"Capítulo atualizado: {e_man} - {e_cap}")
                            except gspread.exceptions.APIError:
                                st.error("❌ Erro na API do Google Sheets.")
                                logger.error("Erro de API ao atualizar capítulo")
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                                logger.error(f"Erro ao atualizar capítulo: {e}", exc_info=True)

            st.divider()
            confirmar_exclusao = st.checkbox(
                "Confirmo que quero excluir este registro permanentemente.",
                key="confirma_del_cap"
            )
            if st.button("🗑️ Excluir Permanentemente", type="primary"):
                if not confirmar_exclusao:
                    st.error("❌ Marque a confirmação antes de excluir.")
                else:
                    with st.spinner("Excluindo..."):
                        try:
                            sheet_capitulos.delete_rows(linha_alvo)
                            st.cache_data.clear()
                            st.success("✅ Registro removido com sucesso!")
                            logger.info(f"Capítulo deletado: linha {linha_alvo}")
                        except gspread.exceptions.APIError:
                            st.error("❌ Erro na API do Google Sheets.")
                            logger.error("Erro de API ao deletar capítulo")
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")
                            logger.error(f"Erro ao deletar capítulo: {e}", exc_info=True)