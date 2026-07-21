import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from config import sheet_demandas, carregar_dados_demandas, LISTA_TIPOS, LISTA_MODULOS, LISTA_MANUAIS, LISTA_MONTADORAS, LISTA_VERSOES

st.set_page_config(page_title="Controle de Demandas", layout="wide")

st.title("📋 Controle de Demandas")


def parse_data_flexivel(data_str):
    """Interpreta a data tanto no formato novo (ISO, AAAA-MM-DD) quanto no
    formato antigo (DD/MM/AAAA), para não quebrar a edição de registros
    salvos antes desta revisão."""
    data_str = str(data_str).strip()
    for formato in ("%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(data_str, formato)
        except ValueError:
            continue
    return datetime.now()


# --- INTERFACE POR ABAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
])

sheet = sheet_demandas


def carregar_dados():
    return carregar_dados_demandas()


with tab1:
    st.subheader("Nova Demanda")
    with st.form("form_adicionar", clear_on_submit=True):
        col1, col2 = st.columns(2)
        with col1:
            demanda = st.text_input("Demanda")
            tipo = st.selectbox("Tipo", LISTA_TIPOS)
            modulo = st.selectbox("Módulo", LISTA_MODULOS)
            manual = st.selectbox("Manual", LISTA_MANUAIS)
        with col2:
            data_obj = st.date_input("Data Linkagem")
            capitulo = st.text_input("Capítulo")
            montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
            versao = st.selectbox("Versão", LISTA_VERSOES)

        if st.form_submit_button("Salvar Nova Demanda"):
            if not demanda.strip():
                st.error("O campo Demanda é obrigatório.")
            elif not capitulo.strip():
                st.error("O campo Capítulo é obrigatório.")
            else:
                # Data salva em formato ISO (AAAA-MM-DD) daqui para frente.
                data_linkagem = data_obj.strftime("%Y-%m-%d") if data_obj else ""
                try:
                    sheet.insert_row(
                        [demanda, tipo, modulo, manual, data_linkagem, capitulo, montadora, versao],
                        index=2,
                    )
                    st.cache_data.clear()
                    st.success("Salvo com sucesso!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro ao salvar: {e}")

    st.divider()
    st.subheader("📋 Demandas Cadastradas Recentemente")
    df_atualizado = carregar_dados()
    if not df_atualizado.empty:
        st.dataframe(df_atualizado.drop(columns=["_row"]).head(10), use_container_width=True, hide_index=True)
    else:
        st.info("Nenhuma demanda cadastrada ainda.")

with tab2:
    st.subheader("🔍 Busca Avançada")
    df = carregar_dados()

    if df.empty:
        st.info("Nenhuma demanda cadastrada ainda.")
    else:
        modo_busca = st.radio("Escolha o método de busca:", ["Filtros em Cascata", "Busca por Campo Específico"], horizontal=True)

        if modo_busca == "Filtros em Cascata":
            st.info("Utilize os filtros abaixo para filtrar os dados:")
            col_a, col_b, col_c = st.columns(3)
            with col_a:
                mod_sel = st.selectbox("Módulo", ["Todos"] + df["MÓDULO"].unique().tolist())
                df_f1 = df if mod_sel == "Todos" else df[df["MÓDULO"] == mod_sel]
                tipo_sel = st.selectbox("Tipo", ["Todos"] + df_f1["TIPO DEMANDA"].unique().tolist())
                df_f2 = df_f1 if tipo_sel == "Todos" else df_f1[df_f1["TIPO DEMANDA"] == tipo_sel]
            with col_b:
                mont_sel = st.selectbox("Montadora", ["Todas"] + df_f2["MONTADORA"].unique().tolist())
                df_f3 = df_f2 if mont_sel == "Todas" else df_f2[df_f2["MONTADORA"] == mont_sel]
                man_sel = st.selectbox("Manual", ["Todos"] + df_f3["MANUAL"].unique().tolist())
                df_f4 = df_f3 if man_sel == "Todos" else df_f3[df_f3["MANUAL"] == man_sel]
            with col_c:
                dem_sel = st.selectbox("Demanda", ["Todas"] + df_f4["DEMANDA"].unique().tolist())
                final = df_f4 if dem_sel == "Todas" else df_f4[df_f4["DEMANDA"] == dem_sel]
            st.divider()
            st.dataframe(final.drop(columns=["_row"]), use_container_width=True)
        else:
            colunas_visiveis = [c for c in df.columns if c != "_row"]
            col_1, col_2 = st.columns(2)
            with col_1:
                coluna_alvo = st.selectbox("Selecione o campo para buscar:", colunas_visiveis)
            with col_2:
                valor_busca = st.text_input("Digite o valor para busca:")
            if valor_busca:
                resultado = df[df[coluna_alvo].astype(str).str.contains(valor_busca, case=False, regex=False, na=False)]
                st.write(f"Resultados para '{valor_busca}' em {coluna_alvo}:")
                st.dataframe(resultado.drop(columns=["_row"]), use_container_width=True)

with tab3:
    st.subheader("Alterar Demanda Existente")
    df_edit = carregar_dados()

    if df_edit.empty:
        st.info("Nenhuma demanda cadastrada ainda.")
    else:
        demanda_selecionada = st.selectbox("Selecione a demanda para editar:", options=df_edit["DEMANDA"].tolist(), key="edit_select")
        dados_atuais = df_edit[df_edit["DEMANDA"] == demanda_selecionada].iloc[0]
        linha_alvo = dados_atuais["_row"]

        with st.form("form_editar"):
            col1, col2 = st.columns(2)
            with col1:
                nova_demanda = st.text_input("Demanda", value=str(dados_atuais["DEMANDA"]))
                novo_tipo = st.selectbox("Tipo", LISTA_TIPOS, index=LISTA_TIPOS.index(dados_atuais["TIPO DEMANDA"]) if dados_atuais["TIPO DEMANDA"] in LISTA_TIPOS else 0)
                novo_modulo = st.selectbox("Módulo", LISTA_MODULOS, index=LISTA_MODULOS.index(dados_atuais["MÓDULO"]) if dados_atuais["MÓDULO"] in LISTA_MODULOS else 0)
                novo_manual = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados_atuais["MANUAL"]) if dados_atuais["MANUAL"] in LISTA_MANUAIS else 0)
            with col2:
                data_val = parse_data_flexivel(dados_atuais["DATA LINKAGEM"])
                nova_data_obj = st.date_input("Data Linkagem", value=data_val)
                novo_capitulo = st.text_input("Capítulo", value=str(dados_atuais["CAPITULO"]))
                nova_montadora = st.selectbox("Montadora", LISTA_MONTADORAS, index=LISTA_MONTADORAS.index(dados_atuais["MONTADORA"]) if dados_atuais["MONTADORA"] in LISTA_MONTADORAS else 0)
                nova_versao = st.selectbox("Versão", LISTA_VERSOES, index=LISTA_VERSOES.index(dados_atuais["VERSÃO"]) if dados_atuais["VERSÃO"] in LISTA_VERSOES else 0)

            if st.form_submit_button("Salvar Alterações"):
                if not nova_demanda.strip():
                    st.error("O campo Demanda é obrigatório.")
                else:
                    nova_data = nova_data_obj.strftime("%Y-%m-%d")
                    try:
                        sheet.update(
                            range_name=f"A{linha_alvo}:H{linha_alvo}",
                            values=[[nova_demanda, novo_tipo, novo_modulo, novo_manual, nova_data, novo_capitulo, nova_montadora, nova_versao]],
                        )
                        st.cache_data.clear()
                        st.success("Dados atualizados com sucesso!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao atualizar: {e}")

with tab4:
    st.header("🗑️ Excluir Demanda")
    df_del = carregar_dados()

    if df_del.empty:
        st.info("Nenhuma demanda cadastrada ainda.")
    else:
        demanda_selecionada = st.selectbox("1. Selecione a Demanda", [""] + df_del["DEMANDA"].unique().tolist())
        if demanda_selecionada:
            df_f1 = df_del[df_del["DEMANDA"] == demanda_selecionada]
            data_selecionada = st.selectbox("2. Selecione a Data", [""] + df_f1["DATA LINKAGEM"].unique().tolist())
            if data_selecionada:
                df_f2 = df_f1[df_f1["DATA LINKAGEM"] == data_selecionada]
                capitulo_selecionado = st.selectbox("3. Selecione o Capítulo", [""] + df_f2["CAPITULO"].unique().tolist())
                if capitulo_selecionado:
                    registro = df_f2[df_f2["CAPITULO"] == capitulo_selecionado].iloc[0]
                    with st.form("confirmar_exclusao"):
                        st.warning(f"Você tem certeza que deseja excluir a demanda: **{demanda_selecionada}**?")
                        confirmar = st.checkbox("Confirmo que quero excluir este registro permanentemente.")
                        if st.form_submit_button("Confirmar e Excluir Definitivamente"):
                            if not confirmar:
                                st.error("Marque a confirmação antes de excluir.")
                            else:
                                try:
                                    sheet.delete_rows(int(registro["_row"]))
                                    st.cache_data.clear()
                                    st.success("Demanda excluída com sucesso!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Erro ao excluir: {e}")

with tab5:
    st.header("📊 Relatórios e Exportação")
    df_geral = carregar_dados().copy()

    if df_geral.empty:
        st.info("Nenhuma demanda cadastrada ainda.")
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
            filtro_versao = st.selectbox("Versão:", ["Todas"] + df_geral["VERSÃO"].unique().tolist())
            filtro_modulo = st.selectbox("Módulo:", ["Todos"] + df_geral["MÓDULO"].unique().tolist())
        with formato_sel:
            formato = st.radio("Formato de exportação:", ["Excel (.xlsx)", "PDF (.pdf)"])

        df_export = df_geral.drop(columns=["_row"]).copy()
        if filtro_versao != "Todas":
            df_export = df_export[df_export["VERSÃO"] == filtro_versao]
        if filtro_modulo != "Todos":
            df_export = df_export[df_export["MÓDULO"] == filtro_modulo]

        if formato == "Excel (.xlsx)":
            buffer = io.BytesIO()
            with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                df_export.to_excel(writer, index=False)
            st.download_button("📥 Baixar Excel", data=buffer.getvalue(), file_name="relatorio.xlsx", mime="application/vnd.ms-excel")
        elif formato == "PDF (.pdf)":
            buffer = io.BytesIO()
            c = canvas.Canvas(buffer, pagesize=A4)
            c.drawString(100, 800, "Relatório de Demandas")
            y = 750
            for _, row in df_export.iterrows():
                c.drawString(100, y, f"{row['DEMANDA']} - {row['MÓDULO']} - {row['VERSÃO']}")
                y -= 20
                if y < 50:
                    c.showPage()
                    y = 800
            c.save()
            st.download_button("📥 Baixar PDF", data=buffer.getvalue(), file_name="relatorio.pdf", mime="application/pdf")