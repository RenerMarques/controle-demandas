import streamlit as st
import pandas as pd
import io
import logging
import gspread
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, PageBreak
from reportlab.lib.styles import getSampleStyleSheet
from config import (
    sheet_modelos, carregar_dados_modelos,
    LISTA_MODULOS, LISTA_MANUAIS, LISTA_MONTADORAS
)

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Gestão de Modelos", layout="wide")
st.title("📋 Controle de Modelos")

COLUNAS_ESPERADAS = ["MÓDULO", "MANUAL", "CAPITULO", "MONTADORA", "MODELO"]

# --- FUNÇÕES AUXILIARES ---
def get_selectbox_index(lista, valor, nome_campo):
    """Retorna o índice seguro para selectbox."""
    try:
        return lista.index(valor)
    except ValueError:
        st.warning(f"⚠️ '{valor}' não está na lista de {nome_campo}. Usando padrão.")
        logger.warning(f"Valor '{valor}' não encontrado em {nome_campo}")
        return 0

def validar_modelo(modulo, manual, capitulo, montadora, modelo):
    """Valida campos obrigatórios."""
    erros = []
    if not modelo.strip():
        erros.append("Modelo é obrigatório")
    if not capitulo.strip():
        erros.append("Capítulo é obrigatório")

    if erros:
        st.error("❌ Erros de validação:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True

def validar_dataframe_upload(df):
    """Valida DataFrame do upload."""
    erros = []

    # Verifica colunas
    colunas_faltando = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
    if colunas_faltando:
        erros.append(f"Colunas faltando: {', '.join(colunas_faltando)}")

    # Verifica linhas vazias
    if df[COLUNAS_ESPERADAS].isnull().all(axis=1).any():
        erros.append("Há linhas completamente vazias")

    # Verifica campo MODELO obrigatório
    if df["MODELO"].isnull().any() or (df["MODELO"].astype(str).str.strip() == "").any():
        erros.append("Campo MODELO contém valores vazios")

    if erros:
        st.error("❌ Erros no arquivo:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True

def gerar_pdf_modelos(df):
    """Gera PDF formatado com tabela de modelos."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=A4)
    elements = []

    # Estilos
    styles = getSampleStyleSheet()

    # Título
    title = Paragraph("Relatório de Modelos", styles['Heading1'])
    elements.append(title)
    elements.append(Spacer(1, 12))

    # Data do relatório
    data_rel = Paragraph(f"Gerado em: {datetime.now().strftime('%d/%m/%Y às %H:%M')}", styles['Normal'])
    elements.append(data_rel)
    elements.append(Spacer(1, 12))

    # Tabela
    if not df.empty:
        colunas = list(df.columns)
        data = [colunas] + df.values.tolist()

        # Calcula largura das colunas
        col_widths = [80, 100, 80, 100, 80]

        table = Table(data, colWidths=col_widths)
        table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 10),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
            ('GRID', (0, 0), (-1, -1), 1, colors.black),
            ('FONTSIZE', (0, 1), (-1, -1), 9),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.lightgrey])
        ]))
        elements.append(table)
    else:
        elements.append(Paragraph("Nenhum registro encontrado.", styles['Normal']))

    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- ABAS ---
tab_m1, tab_m2, tab_m3, tab_m4, tab_m5 = st.tabs([
    "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
])

# ============ TAB 1: ADICIONAR ============
with tab_m1:
    st.subheader("➕ Adicionar Modelos")
    modo_add = st.radio("Método de cadastro:", ["Manual", "Upload em Lote (Excel)"], horizontal=True)

    if modo_add == "Manual":
        with st.form("form_add_modelo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                m_modulo = st.selectbox("Módulo", LISTA_MODULOS)
                m_manual = st.selectbox("Manual", LISTA_MANUAIS)
                m_capitulo = st.text_input("Capítulo").strip()
            with col2:
                m_montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
                m_modelo = st.text_input("Modelo").strip()

            if st.form_submit_button("Salvar Modelo"):
                if validar_modelo(m_modulo, m_manual, m_capitulo, m_montadora, m_modelo):
                    with st.spinner("Salvando..."):
                        try:
                            sheet_modelos.insert_row(
                                [m_modulo, m_manual, m_capitulo, m_montadora, m_modelo],
                                index=2
                            )
                            st.cache_data.clear()
                            st.success("✅ Modelo salvo com sucesso!")
                            logger.info(f"Modelo criado: {m_modelo}")
                        except gspread.exceptions.APIError:
                            st.error("❌ Erro na API do Google Sheets. Tente novamente.")
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {str(e)}")
                            logger.error(f"Erro ao salvar modelo: {e}", exc_info=True)

    else:  # Upload em Lote
        st.info("📋 O arquivo Excel deve conter as colunas: MÓDULO, MANUAL, CAPITULO, MONTADORA, MODELO")
        uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"])

        if uploaded_file is not None:
            with st.spinner("Lendo arquivo..."):
                try:
                    df_up = pd.read_excel(uploaded_file)
                except Exception as e:
                    st.error(f"❌ Não foi possível ler o arquivo: {e}")
                    df_up = None

            if df_up is not None:
                if validar_dataframe_upload(df_up):
                    df_preview = df_up[COLUNAS_ESPERADAS].fillna("")
                    st.dataframe(df_preview.head(10), use_container_width=True, hide_index=True)
                    st.caption(f"📊 {len(df_preview)} linha(s) prontas para importação.")

                    if st.button("✅ Confirmar Importação em Lote"):
                        dados_formatados = df_preview.values.tolist()
                        with st.spinner("Importando..."):
                            try:
                                sheet_modelos.insert_rows(dados_formatados, row=2)
                                st.cache_data.clear()
                                st.success(f"✅ {len(dados_formatados)} modelo(s) importado(s) com sucesso!")
                                logger.info(f"Importação em lote: {len(dados_formatados)} modelos")
                            except gspread.exceptions.APIError:
                                st.error("❌ Erro na API do Google Sheets.")
                            except Exception as e:
                                st.error(f"❌ Erro na importação: {e}")
                                logger.error(f"Erro ao importar modelos: {e}", exc_info=True)

# ============ TAB 2: BUSCAR ============
with tab_m2:
    st.subheader("🔍 Busca Avançada de Modelos")
    df_mod = carregar_dados_modelos()

    if df_mod.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        modo_busca_m = st.radio(
            "Escolha o método de busca:",
            ["Filtros em Cascata", "Busca por Campo Específico"],
            key="radio_mod",
            horizontal=True
        )

        if modo_busca_m == "Filtros em Cascata":
            c1, c2, c3 = st.columns(3)
            with c1:
                mod_sel = st.selectbox("Módulo", ["Todos"] + sorted(df_mod["MÓDULO"].unique().tolist()))
                man_sel = st.selectbox("Manual", ["Todos"] + sorted(df_mod["MANUAL"].unique().tolist()))
            with c2:
                mont_sel = st.selectbox("Montadora", ["Todas"] + sorted(df_mod["MONTADORA"].unique().tolist()))
                cap_sel = st.selectbox("Capítulo", ["Todos"] + sorted(df_mod["CAPITULO"].unique().tolist()))
            with c3:
                model_sel = st.selectbox("Modelo", ["Todos"] + sorted(df_mod["MODELO"].unique().tolist()))

            final_mod = df_mod.copy()
            if mod_sel != "Todos":
                final_mod = final_mod[final_mod["MÓDULO"] == mod_sel]
            if man_sel != "Todos":
                final_mod = final_mod[final_mod["MANUAL"] == man_sel]
            if mont_sel != "Todas":
                final_mod = final_mod[final_mod["MONTADORA"] == mont_sel]
            if cap_sel != "Todos":
                final_mod = final_mod[final_mod["CAPITULO"] == cap_sel]
            if model_sel != "Todos":
                final_mod = final_mod[final_mod["MODELO"] == model_sel]

            colunas_visiveis = [c for c in final_mod.columns if c != "_row"]
            st.write(f"**Total de registros:** {len(final_mod)}")
            st.dataframe(final_mod[colunas_visiveis], use_container_width=True, hide_index=True)

        else:  # Busca por Campo Específico
            colunas_visiveis = [c for c in df_mod.columns if c != "_row"]
            c1, c2 = st.columns([1, 2])
            with c1:
                coluna_alvo = st.selectbox("Selecione o campo:", colunas_visiveis, key="col_mod")
            with c2:
                valor_busca = st.text_input("Digite o valor para busca:", key="val_mod", placeholder="Ex: Ford").strip()

            if valor_busca:
                resultado_mod = df_mod[
                    df_mod[coluna_alvo].astype(str).str.contains(valor_busca, case=False, regex=False, na=False)
                ]
                st.write(f"**Resultados encontrados:** {len(resultado_mod)}")
                st.dataframe(resultado_mod[colunas_visiveis], use_container_width=True, hide_index=True)
            else:
                st.info("💡 Digite um termo para começar a busca.")

# ============ TAB 3: EDITAR ============
with tab_m3:
    st.subheader("📝 Editar Modelo")
    df_mod = carregar_dados_modelos()

    if df_mod.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        modelo_sel = st.selectbox("Selecione o Modelo para editar:", df_mod["MODELO"].tolist())

        if modelo_sel:
            dados = df_mod[df_mod["MODELO"] == modelo_sel].iloc[0]
            linha_alvo = int(dados["_row"])

            with st.form("form_edit_m"):
                n_mod = st.selectbox(
                    "Módulo",
                    LISTA_MODULOS,
                    index=get_selectbox_index(LISTA_MODULOS, dados["MÓDULO"], "Módulo")
                )
                n_man = st.selectbox(
                    "Manual",
                    LISTA_MANUAIS,
                    index=get_selectbox_index(LISTA_MANUAIS, dados["MANUAL"], "Manual")
                )
                n_cap = st.text_input("Capítulo", value=str(dados["CAPITULO"])).strip()
                n_mon = st.selectbox(
                    "Montadora",
                    LISTA_MONTADORAS,
                    index=get_selectbox_index(LISTA_MONTADORAS, dados["MONTADORA"], "Montadora")
                )
                n_model = st.text_input("Modelo", value=str(dados["MODELO"])).strip()

                if st.form_submit_button("Atualizar"):
                    if validar_modelo(n_mod, n_man, n_cap, n_mon, n_model):
                        with st.spinner("Atualizando..."):
                            try:
                                sheet_modelos.update(
                                    range_name=f"A{linha_alvo}:E{linha_alvo}",
                                    values=[[n_mod, n_man, n_cap, n_mon, n_model]]
                                )
                                st.cache_data.clear()
                                st.success("✅ Modelo atualizado com sucesso!")
                                logger.info(f"Modelo atualizado: {n_model}")
                            except gspread.exceptions.APIError:
                                st.error("❌ Erro na API do Google Sheets.")
                            except Exception as e:
                                st.error(f"❌ Erro ao atualizar: {str(e)}")
                                logger.error(f"Erro ao atualizar modelo: {e}", exc_info=True)

# ============ TAB 4: EXCLUIR ============
with tab_m4:
    st.subheader("🗑️ Excluir Modelo")
    df_mod = carregar_dados_modelos()

    if df_mod.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        m_del = st.selectbox("Selecione o Modelo a excluir", [""] + df_mod["MODELO"].tolist())

        if m_del:
            registro = df_mod[df_mod["MODELO"] == m_del].iloc[0]
            linha_alvo = int(registro["_row"])

            st.warning(f"Você tem certeza que deseja excluir: **{m_del}**?")
            confirmar = st.checkbox("Confirmo que quero excluir este registro permanentemente.", key="confirma_del_modelo")

            if st.button("🗑️ Confirmar Exclusão", type="primary"):
                if not confirmar:
                    st.error("❌ Marque a confirmação antes de excluir.")
                else:
                    with st.spinner("Excluindo..."):
                        try:
                            sheet_modelos.delete_rows(linha_alvo)
                            st.cache_data.clear()
                            st.success("✅ Modelo excluído com sucesso!")
                            logger.info(f"Modelo deletado: {m_del}")
                        except gspread.exceptions.APIError:
                            st.error("❌ Erro na API do Google Sheets.")
                        except Exception as e:
                            st.error(f"❌ Erro ao excluir: {str(e)}")
                            logger.error(f"Erro ao deletar modelo: {e}", exc_info=True)

# ============ TAB 5: RELATÓRIOS ============
with tab_m5:
    st.header("📊 Relatórios Detalhados")
    df_mod_geral = carregar_dados_modelos().copy()

    if df_mod_geral.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        st.subheader("Filtros de Visualização e Exportação")
        c1, c2, c3 = st.columns(3)

        with c1:
            f_mod = st.selectbox("Módulo:", ["Todos"] + sorted(df_mod_geral["MÓDULO"].unique().tolist()))
            f_man = st.selectbox("Manual:", ["Todos"] + sorted(df_mod_geral["MANUAL"].unique().tolist()))
        with c2:
            f_mon = st.selectbox("Montadora:", ["Todas"] + sorted(df_mod_geral["MONTADORA"].unique().tolist()))
            f_cap = st.selectbox("Capítulo:", ["Todos"] + sorted(df_mod_geral["CAPITULO"].unique().tolist()))
        with c3:
            f_mod_ex = st.selectbox("Modelo:", ["Todos"] + sorted(df_mod_geral["MODELO"].unique().tolist()))
            formato = st.radio("Formato:", ["Excel (.xlsx)", "PDF (.pdf)"], horizontal=True)

        # Aplicar filtros
        df_exp = df_mod_geral.drop(columns=["_row"]).copy()
        if f_mod != "Todos":
            df_exp = df_exp[df_exp["MÓDULO"] == f_mod]
        if f_man != "Todos":
            df_exp = df_exp[df_exp["MANUAL"] == f_man]
        if f_mon != "Todas":
            df_exp = df_exp[df_exp["MONTADORA"] == f_mon]
        if f_cap != "Todos":
            df_exp = df_exp[df_exp["CAPITULO"] == f_cap]
        if f_mod_ex != "Todos":
            df_exp = df_exp[df_exp["MODELO"] == f_mod_ex]

        # Visualização
        st.divider()
        st.write(f"### 📊 Visualização: {len(df_exp)} registros encontrados")
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        st.divider()

        # Exportação
        if not df_exp.empty:
            if formato == "Excel (.xlsx)":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_exp.to_excel(writer, index=False, sheet_name="Modelos")
                buffer.seek(0)
                st.download_button(
                    "📥 Baixar Relatório Excel",
                    data=buffer.getvalue(),
                    file_name=f"relatorio_modelos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:  # PDF
                buffer = gerar_pdf_modelos(df_exp)
                st.download_button(
                    "📥 Baixar Relatório PDF",
                    data=buffer.getvalue(),
                    file_name=f"relatorio_modelos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )
        else:
            st.warning("⚠️ Nenhum registro encontrado para exportar.")