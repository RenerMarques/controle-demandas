import streamlit as st
import pandas as pd
from datetime import datetime
import io
import logging
import gspread
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from config import (
    sheet_demandas, carregar_dados_demandas, 
    LISTA_TIPOS, LISTA_MODULOS, LISTA_MANUAIS, 
    LISTA_MONTADORAS, LISTA_VERSOES
)

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Controle de Demandas", layout="wide")
st.title("📋 Controle de Demandas")

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

# --- ABAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
])

# ============ TAB 1: ADICIONAR ============
with tab1:
    st.subheader("Nova Demanda")
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
            col_1, col_2 = st.columns(2)
            with col_1:
                colunas_busca = [c for c in df.columns if c != "_row"]
                coluna_alvo = st.selectbox("Selecione o campo para buscar:", colunas_busca)
            with col_2:
                valor_busca = st.text_input("Digite o valor para busca:").strip()

            if valor_busca:
                resultado = df[df[coluna_alvo].astype(str).str.contains(valor_busca, case=False, na=False)]
                st.write(f"**Resultados para '{valor_busca}' em {coluna_alvo}:** {len(resultado)} encontrados")
                colunas_visiveis = [c for c in resultado.columns if c != "_row"]
                st.dataframe(resultado[colunas_visiveis], use_container_width=True, hide_index=True)

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
        col_sel, formato_sel = st.columns(2)
        with col_sel:
            filtro_versao = st.selectbox("Versão:", ["Todas"] + sorted(df_geral["VERSÃO"].unique().tolist()))
            filtro_modulo = st.selectbox("Módulo:", ["Todos"] + sorted(df_geral["MÓDULO"].unique().tolist()))
        with formato_sel:
            formato = st.radio("Formato de exportação:", ["Excel (.xlsx)", "PDF (.pdf)"])

        df_export = df_geral.copy()
        if filtro_versao != "Todas":
            df_export = df_export[df_export["VERSÃO"] == filtro_versao]
        if filtro_modulo != "Todos":
            df_export = df_export[df_export["MÓDULO"] == filtro_modulo]

        # Remove coluna _row antes de exportar
        colunas_export = [c for c in df_export.columns if c != "_row"]
        df_export = df_export[colunas_export]

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

        elif formato == "PDF (.pdf)":
            buffer = io.BytesIO()
            doc = SimpleDocTemplate(buffer, pagesize=A4)
            elements = []

            # Título
            styles = getSampleStyleSheet()
            title = Paragraph("Relatório de Demandas", styles['Heading1'])
            elements.append(title)
            elements.append(Spacer(1, 12))

            # Tabela
            data = [colunas_export] + df_export.values.tolist()
            table = Table(data, colWidths=[60, 60, 60, 60, 60, 60, 60, 60])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.grey),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.beige),
                ('GRID', (0, 0), (-1, -1), 1, colors.black)
            ]))
            elements.append(table)

            doc.build(elements)
            buffer.seek(0)
            st.download_button(
                "📥 Baixar PDF",
                data=buffer.getvalue(),
                file_name=f"relatorio_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.pdf",
                mime="application/pdf"
            )