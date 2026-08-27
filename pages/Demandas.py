import streamlit as st
import pandas as pd
from datetime import datetime
import io
import logging
import gspread
from reportlab.lib.pagesizes import A4, landscape
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from config import (
    sheet_demandas, carregar_dados_demandas,
    LISTA_TIPOS, LISTA_MODULOS, LISTA_MANUAIS,
    LISTA_MONTADORAS, LISTA_VERSOES
)

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Controle de Demandas", layout="wide")
st.title("📋 Controle de Demandas")

COLUNAS_ESPERADAS_DEMANDAS = [
    "DEMANDA", "TIPO DEMANDA", "MÓDULO", "MANUAL",
    "DATA LINKAGEM", "CAPITULO", "MONTADORA", "VERSÃO"
]

# --- FUNÇÕES AUXILIARES ---
def parse_data(data_str):
    """Parse data em múltiplos formatos."""
    if not data_str or pd.isna(data_str):
        return datetime.now().date()

    data_str = str(data_str).strip()
    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y']

    for fmt in formatos:
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            continue

    st.warning(f"⚠️ Não consegui interpretar a data: '{data_str}'")
    return datetime.now().date()

def formatar_data(data_obj):
    """Formata data para DD/MM/YYYY."""
    if isinstance(data_obj, str):
        data_obj = parse_data(data_obj)
    return data_obj.strftime("%d/%m/%Y") if data_obj else ""

def get_selectbox_index(lista, valor, nome_campo):
    """Retorna o índice seguro para selectbox."""
    try:
        return lista.index(valor)
    except ValueError:
        st.warning(f"⚠️ '{valor}' não está na lista de {nome_campo}. Usando padrão.")
        logger.warning(f"Valor '{valor}' não encontrado em {nome_campo}")
        return 0

def validar_demanda(demanda, tipo, modulo, manual, capitulo, montadora, versao):
    """Valida campos obrigatórios."""
    erros = []
    if not demanda.strip():
        erros.append("Demanda é obrigatória")
    if not capitulo.strip():
        erros.append("Capítulo é obrigatório")

    if erros:
        st.error("❌ Erros de validação:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True

def validar_dataframe_upload_demandas(df):
    """Valida DataFrame do upload em lote de demandas."""
    erros = []

    colunas_faltando = [c for c in COLUNAS_ESPERADAS_DEMANDAS if c not in df.columns]
    if colunas_faltando:
        erros.append(f"Colunas faltando: {', '.join(colunas_faltando)}")
        st.error("❌ Erros no arquivo:\n" + "\n".join(f"• {e}" for e in erros))
        return False

    if df[COLUNAS_ESPERADAS_DEMANDAS].isnull().all(axis=1).any():
        erros.append("Há linhas completamente vazias")

    if df["DEMANDA"].isnull().any() or (df["DEMANDA"].astype(str).str.strip() == "").any():
        erros.append("Campo DEMANDA contém valores vazios")

    if df["CAPITULO"].isnull().any() or (df["CAPITULO"].astype(str).str.strip() == "").any():
        erros.append("Campo CAPITULO contém valores vazios")

    invalidos_tipo = set(df["TIPO DEMANDA"].astype(str).str.strip()) - set(LISTA_TIPOS)
    if invalidos_tipo:
        erros.append(f"TIPO DEMANDA com valores fora da lista: {', '.join(invalidos_tipo)}")

    invalidos_modulo = set(df["MÓDULO"].astype(str).str.strip()) - set(LISTA_MODULOS)
    if invalidos_modulo:
        erros.append(f"MÓDULO com valores fora da lista: {', '.join(invalidos_modulo)}")

    invalidos_manual = set(df["MANUAL"].astype(str).str.strip()) - set(LISTA_MANUAIS)
    if invalidos_manual:
        erros.append(f"MANUAL com valores fora da lista: {', '.join(invalidos_manual)}")

    invalidos_montadora = set(df["MONTADORA"].astype(str).str.strip()) - set(LISTA_MONTADORAS)
    if invalidos_montadora:
        erros.append(f"MONTADORA com valores fora da lista: {', '.join(invalidos_montadora)}")

    invalidos_versao = set(df["VERSÃO"].astype(str).str.strip()) - set(LISTA_VERSOES)
    if invalidos_versao:
        erros.append(f"VERSÃO com valores fora da lista: {', '.join(invalidos_versao)}")

    if erros:
        st.error("❌ Erros no arquivo:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True

def gerar_pdf_demandas(df_export, colunas_export, filtros_texto=""):
    """Gera PDF do relatório de demandas em paisagem, com colunas proporcionais
    ao conteúdo e quebra de texto automática (evita nomes cortados/sobrepostos)."""
    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=landscape(A4),
        leftMargin=20, rightMargin=20, topMargin=30, bottomMargin=20
    )
    elements = []
    styles = getSampleStyleSheet()

    elements.append(Paragraph("Relatório de Demandas", styles['Heading1']))
    if filtros_texto:
        elements.append(Paragraph(f"Filtros aplicados: {filtros_texto}", styles['Normal']))
    elements.append(Paragraph(f"Total de registros: {len(df_export)}", styles['Normal']))
    elements.append(Spacer(1, 12))

    cell_style = ParagraphStyle('CellStyle', parent=styles['Normal'], fontSize=7, leading=9)
    header_style = ParagraphStyle(
        'HeaderStyle', parent=styles['Normal'], fontSize=8, leading=10,
        textColor=colors.whitesmoke, fontName='Helvetica-Bold'
    )

    # Pesos proporcionais de largura por coluna (colunas de texto mais longo
    # recebem mais espaço; a soma dos pesos é normalizada para a largura útil da página)
    pesos = {
        "DEMANDA": 0.09, "TIPO DEMANDA": 0.10, "MÓDULO": 0.10,
        "MANUAL": 0.20, "DATA LINKAGEM": 0.09, "CAPITULO": 0.07,
        "MONTADORA": 0.16, "VERSÃO": 0.09
    }
    largura_util = landscape(A4)[0] - 40
    soma_pesos = sum(pesos.get(c, 0.10) for c in colunas_export)
    col_widths = [largura_util * (pesos.get(c, 0.10) / soma_pesos) for c in colunas_export]

    header_row = [Paragraph(str(c), header_style) for c in colunas_export]
    data = [header_row]
    for _, row in df_export.iterrows():
        data.append([Paragraph(str(v), cell_style) for v in row])

    table = Table(data, colWidths=col_widths, repeatRows=1)
    table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
        ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
        ('TOPPADDING', (0, 0), (-1, 0), 8),
        ('BOTTOMPADDING', (0, 0), (-1, 0), 8),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.black),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.Color(0.95, 0.95, 0.95)])
    ]))
    elements.append(table)
    doc.build(elements)
    buffer.seek(0)
    return buffer

# --- ABAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
])

# ============ TAB 1: ADICIONAR ============
with tab1:
    st.subheader("Nova Demanda")
    modo_add = st.radio("Método de cadastro:", ["Manual", "Upload em Lote (Excel)"], horizontal=True)

    if modo_add == "Manual":
        with st.form("form_adicionar", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                demanda = st.text_input("Demanda").strip()
                tipo = st.selectbox("Tipo", LISTA_TIPOS)
                modulo = st.selectbox("Módulo", LISTA_MODULOS)
                manual = st.selectbox("Manual", LISTA_MANUAIS)
            with col2:
                data_obj = st.date_input("Data Linkagem")
                data_linkagem = formatar_data(data_obj)
                capitulo = st.text_input("Capítulo").strip()
                montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
                versao = st.selectbox("Versão", LISTA_VERSOES)

            if st.form_submit_button("Salvar Nova Demanda"):
                if validar_demanda(demanda, tipo, modulo, manual, capitulo, montadora, versao):
                    with st.spinner("Salvando..."):
                        try:
                            sheet_demandas.insert_row(
                                [demanda, tipo, modulo, manual, data_linkagem, capitulo, montadora, versao],
                                index=2
                            )
                            st.cache_data.clear()
                            st.success("✅ Demanda salva com sucesso!")
                            logger.info(f"Demanda criada: {demanda}")
                        except gspread.exceptions.APIError:
                            st.error("❌ Erro na API do Google Sheets. Tente novamente.")
                        except Exception as e:
                            st.error(f"❌ Erro ao salvar: {str(e)}")
                            logger.error(f"Erro ao salvar demanda: {e}", exc_info=True)

    else:  # Upload em Lote
        st.info(
            "📋 O arquivo Excel deve conter as colunas: DEMANDA, TIPO DEMANDA, MÓDULO, MANUAL, "
            "DATA LINKAGEM, CAPITULO, MONTADORA, VERSÃO. Os valores de TIPO DEMANDA, MÓDULO, MANUAL, "
            "MONTADORA e VERSÃO precisam bater exatamente com as listas oficiais do sistema."
        )
        uploaded_file_dem = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"], key="upload_demandas")

        if uploaded_file_dem is not None:
            with st.spinner("Lendo arquivo..."):
                try:
                    df_up_dem = pd.read_excel(uploaded_file_dem)
                except Exception as e:
                    st.error(f"❌ Não foi possível ler o arquivo: {e}")
                    df_up_dem = None

            if df_up_dem is not None:
                # Normaliza a coluna de data para o formato DD/MM/YYYY em texto
                if "DATA LINKAGEM" in df_up_dem.columns:
                    def _formatar_data_upload(v):
                        if pd.isna(v):
                            return ""
                        if isinstance(v, (pd.Timestamp, datetime)):
                            return v.strftime("%d/%m/%Y")
                        return formatar_data(parse_data(str(v)))
                    df_up_dem["DATA LINKAGEM"] = df_up_dem["DATA LINKAGEM"].apply(_formatar_data_upload)

                if validar_dataframe_upload_demandas(df_up_dem):
                    df_preview_dem = df_up_dem[COLUNAS_ESPERADAS_DEMANDAS].fillna("")
                    st.dataframe(df_preview_dem.head(10), use_container_width=True, hide_index=True)
                    st.caption(f"📊 {len(df_preview_dem)} linha(s) prontas para importação.")

                    if st.button("✅ Confirmar Importação em Lote", key="confirmar_lote_demandas"):
                        dados_formatados_dem = df_preview_dem.values.tolist()
                        with st.spinner("Importando..."):
                            try:
                                sheet_demandas.insert_rows(dados_formatados_dem, row=2)
                                st.cache_data.clear()
                                st.success(f"✅ {len(dados_formatados_dem)} demanda(s) importada(s) com sucesso!")
                                logger.info(f"Importação em lote: {len(dados_formatados_dem)} demandas")
                            except gspread.exceptions.APIError:
                                st.error("❌ Erro na API do Google Sheets.")
                            except Exception as e:
                                st.error(f"❌ Erro na importação: {e}")
                                logger.error(f"Erro ao importar demandas: {e}", exc_info=True)

    st.divider()
    st.subheader("📋 Demandas Cadastradas Recentemente")
    df_atualizado = carregar_dados_demandas()
    if not df_atualizado.empty:
        colunas_visiveis = [c for c in df_atualizado.columns if c != "_row"]
        st.dataframe(df_atualizado[colunas_visiveis].head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma demanda cadastrada ainda.")

# ============ TAB 2: BUSCAR ============
with tab2:
    st.subheader("🔍 Busca Avançada")
    df = carregar_dados_demandas()

    if df.empty:
        st.info("Nenhuma demanda disponível.")
    else:
        modo_busca = st.radio(
            "Escolha o método de busca:",
            ["Filtros em Cascata", "Busca por Campo Específico"],
            horizontal=True
        )

        if modo_busca == "Filtros em Cascata":
            st.info("Utilize os filtros abaixo para filtrar os dados:")
            col_a, col_b, col_c = st.columns(3)

            with col_a:
                mod_sel = st.selectbox("Módulo", ["Todos"] + sorted(df["MÓDULO"].unique().tolist()))
                df_f1 = df if mod_sel == "Todos" else df[df["MÓDULO"] == mod_sel]

                tipo_sel = st.selectbox("Tipo", ["Todos"] + sorted(df_f1["TIPO DEMANDA"].unique().tolist()))
                df_f2 = df_f1 if tipo_sel == "Todos" else df_f1[df_f1["TIPO DEMANDA"] == tipo_sel]

            with col_b:
                mont_sel = st.selectbox("Montadora", ["Todas"] + sorted(df_f2["MONTADORA"].unique().tolist()))
                df_f3 = df_f2 if mont_sel == "Todas" else df_f2[df_f2["MONTADORA"] == mont_sel]

                man_sel = st.selectbox("Manual", ["Todos"] + sorted(df_f3["MANUAL"].unique().tolist()))
                df_f4 = df_f3 if man_sel == "Todos" else df_f3[df_f3["MANUAL"] == man_sel]

            with col_c:
                dem_sel = st.selectbox("Demanda", ["Todas"] + sorted(df_f4["DEMANDA"].unique().tolist()))
                final = df_f4 if dem_sel == "Todas" else df_f4[df_f4["DEMANDA"] == dem_sel]

            st.divider()
            colunas_visiveis = [c for c in final.columns if c != "_row"]
            st.dataframe(final[colunas_visiveis], use_container_width=True, hide_index=True)
            st.write(f"**Total de registros:** {len(final)}")

        else:  # Busca por Campo Específico
            st.caption(
                "Selecione um ou mais valores em cada campo para combinar a busca "
                "(ex.: várias demandas, vários capítulos, várias datas ao mesmo tempo). "
                "Deixe em branco para não filtrar por aquele campo."
            )

            col_b1, col_b2, col_b3 = st.columns(3)
            with col_b1:
                b_demanda = st.multiselect("Demanda:", sorted(df["DEMANDA"].unique().tolist()), key="busca_demanda")
                b_tipo = st.multiselect("Tipo Demanda:", sorted(df["TIPO DEMANDA"].unique().tolist()), key="busca_tipo")
                b_modulo = st.multiselect("Módulo:", sorted(df["MÓDULO"].unique().tolist()), key="busca_modulo")
            with col_b2:
                b_manual = st.multiselect("Manual:", sorted(df["MANUAL"].unique().tolist()), key="busca_manual")
                b_data = st.multiselect("Data Linkagem:", sorted(df["DATA LINKAGEM"].astype(str).unique().tolist()), key="busca_data")
                b_capitulo = st.multiselect("Capítulo:", sorted(df["CAPITULO"].astype(str).unique().tolist()), key="busca_capitulo")
            with col_b3:
                b_montadora = st.multiselect("Montadora:", sorted(df["MONTADORA"].unique().tolist()), key="busca_montadora")
                b_versao = st.multiselect("Versão:", sorted(df["VERSÃO"].unique().tolist()), key="busca_versao")

            resultado = df.copy()
            if b_demanda:
                resultado = resultado[resultado["DEMANDA"].isin(b_demanda)]
            if b_tipo:
                resultado = resultado[resultado["TIPO DEMANDA"].isin(b_tipo)]
            if b_modulo:
                resultado = resultado[resultado["MÓDULO"].isin(b_modulo)]
            if b_manual:
                resultado = resultado[resultado["MANUAL"].isin(b_manual)]
            if b_data:
                resultado = resultado[resultado["DATA LINKAGEM"].astype(str).isin(b_data)]
            if b_capitulo:
                resultado = resultado[resultado["CAPITULO"].astype(str).isin(b_capitulo)]
            if b_montadora:
                resultado = resultado[resultado["MONTADORA"].isin(b_montadora)]
            if b_versao:
                resultado = resultado[resultado["VERSÃO"].isin(b_versao)]

            st.divider()
            colunas_visiveis = [c for c in resultado.columns if c != "_row"]
            st.write(f"**Total de registros encontrados:** {len(resultado)}")
            st.dataframe(resultado[colunas_visiveis], use_container_width=True, hide_index=True)

            if not resultado.empty:
                st.subheader("📥 Exportar Resultado da Busca")
                formato_busca = st.radio(
                    "Formato de exportação:", ["Excel (.xlsx)", "PDF (.pdf)"], key="formato_busca"
                )

                df_busca_export = resultado[colunas_visiveis]

                partes_filtro_b = []
                if b_demanda: partes_filtro_b.append(f"Demanda: {', '.join(b_demanda)}")
                if b_tipo: partes_filtro_b.append(f"Tipo: {', '.join(b_tipo)}")
                if b_modulo: partes_filtro_b.append(f"Módulo: {', '.join(b_modulo)}")
                if b_manual: partes_filtro_b.append(f"Manual: {', '.join(b_manual)}")
                if b_data: partes_filtro_b.append(f"Data: {', '.join(b_data)}")
                if b_capitulo: partes_filtro_b.append(f"Capítulo: {', '.join(b_capitulo)}")
                if b_montadora: partes_filtro_b.append(f"Montadora: {', '.join(b_montadora)}")
                if b_versao: partes_filtro_b.append(f"Versão: {', '.join(b_versao)}")
                filtros_texto_b = " | ".join(partes_filtro_b) if partes_filtro_b else "Todos os registros"

                if formato_busca == "Excel (.xlsx)":
                    buffer_b = io.BytesIO()
                    with pd.ExcelWriter(buffer_b, engine='openpyxl') as writer:
                        df_busca_export.to_excel(writer, index=False, sheet_name="Busca")
                    buffer_b.seek(0)
                    st.download_button(
                        "📥 Baixar Excel",
                        data=buffer_b.getvalue(),
                        file_name=f"busca_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                        mime="application/vnd.ms-excel",
                        key="download_busca_excel"
                    )
                else:  # PDF
                    buffer_b = gerar_pdf_demandas(df_busca_export, colunas_visiveis, filtros_texto_b)
                    st.download_button(
                        "📥 Baixar PDF",
                        data=buffer_b.getvalue(),
                        file_name=f"busca_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                        mime="application/pdf",
                        key="download_busca_pdf"
                    )

# ============ TAB 3: EDITAR ============
with tab3:
    st.subheader("✏️ Alterar Demanda Existente")
    df_edit = carregar_dados_demandas()

    if df_edit.empty:
        st.info("Nenhuma demanda disponível para editar.")
    else:
        demanda_selecionada = st.selectbox(
            "Selecione a demanda para editar:",
            options=df_edit["DEMANDA"].tolist(),
            key="edit_select"
        )
        dados_atuais = df_edit[df_edit["DEMANDA"] == demanda_selecionada].iloc[0]
        linha_alvo = int(dados_atuais["_row"])

        with st.form("form_editar"):
            col1, col2 = st.columns(2)
            with col1:
                nova_demanda = st.text_input("Demanda", value=str(dados_atuais["DEMANDA"])).strip()
                novo_tipo = st.selectbox(
                    "Tipo",
                    LISTA_TIPOS,
                    index=get_selectbox_index(LISTA_TIPOS, dados_atuais["TIPO DEMANDA"], "Tipo")
                )
                novo_modulo = st.selectbox(
                    "Módulo",
                    LISTA_MODULOS,
                    index=get_selectbox_index(LISTA_MODULOS, dados_atuais["MÓDULO"], "Módulo")
                )
                novo_manual = st.selectbox(
                    "Manual",
                    LISTA_MANUAIS,
                    index=get_selectbox_index(LISTA_MANUAIS, dados_atuais["MANUAL"], "Manual")
                )
            with col2:
                data_val = parse_data(dados_atuais["DATA LINKAGEM"])
                nova_data = st.date_input("Data Linkagem", value=data_val)
                nova_data_str = formatar_data(nova_data)

                novo_capitulo = st.text_input("Capítulo", value=str(dados_atuais["CAPITULO"])).strip()
                nova_montadora = st.selectbox(
                    "Montadora",
                    LISTA_MONTADORAS,
                    index=get_selectbox_index(LISTA_MONTADORAS, dados_atuais["MONTADORA"], "Montadora")
                )
                nova_versao = st.selectbox(
                    "Versão",
                    LISTA_VERSOES,
                    index=get_selectbox_index(LISTA_VERSOES, dados_atuais["VERSÃO"], "Versão")
                )

            if st.form_submit_button("Salvar Alterações"):
                if validar_demanda(nova_demanda, novo_tipo, novo_modulo, novo_manual, novo_capitulo, nova_montadora, nova_versao):
                    with st.spinner("Atualizando..."):
                        try:
                            sheet_demandas.update(
                                range_name=f"A{linha_alvo}:H{linha_alvo}",
                                values=[[nova_demanda, novo_tipo, novo_modulo, novo_manual, nova_data_str, novo_capitulo, nova_montadora, nova_versao]]
                            )
                            st.cache_data.clear()
                            st.success("✅ Demanda atualizada com sucesso!")
                            logger.info(f"Demanda atualizada: {nova_demanda}")
                        except gspread.exceptions.APIError:
                            st.error("❌ Erro na API do Google Sheets.")
                        except Exception as e:
                            st.error(f"❌ Erro ao atualizar: {str(e)}")
                            logger.error(f"Erro ao atualizar demanda: {e}", exc_info=True)

# ============ TAB 4: EXCLUIR ============
with tab4:
    st.header("🗑️ Excluir Demanda")
    df_temp = carregar_dados_demandas()

    if df_temp.empty:
        st.info("Nenhuma demanda disponível para excluir.")
    else:
        try:
            demandas_disponiveis = sorted(df_temp["DEMANDA"].unique().tolist())
            demanda_selecionada = st.selectbox("1. Selecione a Demanda", [""] + demandas_disponiveis)

            if demanda_selecionada:
                df_filtered = df_temp[df_temp["DEMANDA"] == demanda_selecionada]
                datas_disponiveis = sorted(df_filtered["DATA LINKAGEM"].unique().tolist())
                data_selecionada = st.selectbox("2. Selecione a Data", [""] + datas_disponiveis)

                if data_selecionada:
                    df_filtered2 = df_filtered[df_filtered["DATA LINKAGEM"] == data_selecionada]
                    capitulos_disponiveis = sorted(df_filtered2["CAPITULO"].unique().tolist())
                    capitulo_selecionado = st.selectbox("3. Selecione o Capítulo", [""] + capitulos_disponiveis)

                    if capitulo_selecionado:
                        resultado = df_filtered2[df_filtered2["CAPITULO"] == capitulo_selecionado]

                        if not resultado.empty:
                            linha_alvo = int(resultado.iloc[0]["_row"])

                            with st.form("confirmar_exclusao"):
                                st.warning(f"Você tem certeza que deseja excluir a demanda: **{demanda_selecionada}**?")
                                if st.form_submit_button("Confirmar e Excluir Definitivamente"):
                                    with st.spinner("Excluindo..."):
                                        try:
                                            sheet_demandas.delete_rows(linha_alvo)
                                            st.cache_data.clear()
                                            st.success("✅ Demanda excluída com sucesso!")
                                            logger.info(f"Demanda deletada: {demanda_selecionada}")
                                        except gspread.exceptions.APIError:
                                            st.error("❌ Erro na API do Google Sheets.")
                                        except Exception as e:
                                            st.error(f"❌ Erro ao excluir: {str(e)}")
                                            logger.error(f"Erro ao deletar demanda: {e}", exc_info=True)
        except Exception as e:
            st.error(f"❌ Erro ao carregar filtros: {str(e)}")
            logger.error(f"Erro ao carregar filtros de exclusão: {e}", exc_info=True)

# ============ TAB 5: RELATÓRIOS ============
with tab5:
    st.header("📊 Relatórios e Exportação")
    df_geral = carregar_dados_demandas()

    if df_geral.empty:
        st.info("Nenhuma demanda disponível para relatório.")
    else:
        col1, col2 = st.columns(2)
        with col1:
            st.subheader("Por Versão")
            df_geral["VERSÃO"] = df_geral["VERSÃO"].astype(str).str.strip()
            st.bar_chart(df_geral["VERSÃO"].value_counts().sort_index())
        with col2:
            st.subheader("Por Módulo")
            df_geral["MÓDULO"] = df_geral["MÓDULO"].astype(str).str.strip()
            st.bar_chart(df_geral["MÓDULO"].value_counts().sort_index())

        st.divider()
        st.subheader("📥 Gerar e Exportar Relatório")
        st.caption(
            "Selecione um ou mais valores em cada filtro para combinar relatórios "
            "(ex.: várias versões e vários manuais ao mesmo tempo). Deixe em branco "
            "para incluir todos os valores daquele campo."
        )

        col_f1, col_f2, col_f3 = st.columns(3)
        with col_f1:
            f_tipo = st.multiselect("Tipo Demanda:", sorted(df_geral["TIPO DEMANDA"].unique().tolist()), key="rel_tipo")
            f_modulo = st.multiselect("Módulo:", sorted(df_geral["MÓDULO"].unique().tolist()), key="rel_modulo")
        with col_f2:
            f_manual = st.multiselect("Manual:", sorted(df_geral["MANUAL"].unique().tolist()), key="rel_manual")
            f_montadora = st.multiselect("Montadora:", sorted(df_geral["MONTADORA"].unique().tolist()), key="rel_montadora")
        with col_f3:
            f_versao = st.multiselect("Versão:", sorted(df_geral["VERSÃO"].unique().tolist()), key="rel_versao")
            formato = st.radio("Formato de exportação:", ["Excel (.xlsx)", "PDF (.pdf)"])

        df_export = df_geral.copy()
        if f_tipo:
            df_export = df_export[df_export["TIPO DEMANDA"].isin(f_tipo)]
        if f_modulo:
            df_export = df_export[df_export["MÓDULO"].isin(f_modulo)]
        if f_manual:
            df_export = df_export[df_export["MANUAL"].isin(f_manual)]
        if f_montadora:
            df_export = df_export[df_export["MONTADORA"].isin(f_montadora)]
        if f_versao:
            df_export = df_export[df_export["VERSÃO"].isin(f_versao)]

        colunas_export = [c for c in df_export.columns if c != "_row"]
        df_export = df_export[colunas_export]

        st.write(f"**Registros encontrados:** {len(df_export)}")
        st.dataframe(df_export, use_container_width=True, hide_index=True)

        if df_export.empty:
            st.warning("⚠️ Nenhum registro corresponde aos filtros selecionados.")
        else:
            partes_filtro = []
            if f_tipo: partes_filtro.append(f"Tipo: {', '.join(f_tipo)}")
            if f_modulo: partes_filtro.append(f"Módulo: {', '.join(f_modulo)}")
            if f_manual: partes_filtro.append(f"Manual: {', '.join(f_manual)}")
            if f_montadora: partes_filtro.append(f"Montadora: {', '.join(f_montadora)}")
            if f_versao: partes_filtro.append(f"Versão: {', '.join(f_versao)}")
            filtros_texto = " | ".join(partes_filtro) if partes_filtro else "Todos os registros"

            if formato == "Excel (.xlsx)":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_export.to_excel(writer, index=False, sheet_name="Demandas")
                buffer.seek(0)
                st.download_button(
                    "📥 Baixar Excel",
                    data=buffer.getvalue(),
                    file_name=f"relatorio_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
                    mime="application/vnd.ms-excel"
                )
            else:  # PDF
                buffer = gerar_pdf_demandas(df_export, colunas_export, filtros_texto)
                st.download_button(
                    "📥 Baixar PDF",
                    data=buffer.getvalue(),
                    file_name=f"relatorio_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                    mime="application/pdf"
                )