import streamlit as st
import pandas as pd
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
# IMPORTANTE: Importamos as variáveis e funções do seu novo arquivo de configuração
from config import sheet_demandas, carregar_dados_demandas, LISTA_TIPOS, LISTA_MODULOS, LISTA_MANUAIS, LISTA_MONTADORAS, LISTA_VERSOES

st.set_page_config(page_title="Controle de Demandas", layout="wide")

st.title("📋 Controle de Demandas")

# --- INTERFACE POR ABAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
])

# Para facilitar, apelidamos a planilha de 'sheet' como no seu código original
sheet = sheet_demandas 
# E criamos uma função local para carregar (usando a que veio do config)
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
            data_linkagem = data_obj.strftime("%d/%m/%Y") if data_obj else ""
            capitulo = st.text_input("Capítulo")
            montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
            versao = st.selectbox("Versão", LISTA_VERSOES)
        
        if st.form_submit_button("Salvar Nova Demanda"):
            sheet.insert_row([demanda, tipo, modulo, manual, data_linkagem, capitulo, montadora, versao], index=2)
            st.success("Salvo com sucesso!")
            st.cache_data.clear() 
            st.rerun()

    st.divider()
    st.subheader("📋 Demandas Cadastradas Recentemente")
    df_atualizado = carregar_dados()
    st.dataframe(df_atualizado.head(10), use_container_width=True, hide_index=True)

with tab2:
        st.subheader("🔍 Busca Avançada")
        df = carregar_dados()
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
            st.dataframe(final, use_container_width=True)
        else:
            col_1, col_2 = st.columns(2)
            with col_1: coluna_alvo = st.selectbox("Selecione o campo para buscar:", df.columns.tolist())
            with col_2: valor_busca = st.text_input("Digite o valor para busca:")
            if valor_busca:
                resultado = df[df[coluna_alvo].astype(str).str.contains(valor_busca, case=False)]
                st.write(f"Resultados para '{valor_busca}' em {coluna_alvo}:")
                st.dataframe(resultado, use_container_width=True)

    with tab3:
        st.subheader("Alterar Demanda Existente")
        df_edit = carregar_dados()
        demanda_selecionada = st.selectbox("Selecione a demanda para editar:", options=df_edit["DEMANDA"].tolist(), key="edit_select")
        dados_atuais = df_edit[df_edit["DEMANDA"] == demanda_selecionada].iloc[0]

        with st.form("form_editar"):
            col1, col2 = st.columns(2)
            with col1:
                nova_demanda = st.text_input("Demanda", value=str(dados_atuais["DEMANDA"]))
                novo_tipo = st.selectbox("Tipo", LISTA_TIPOS, index=LISTA_TIPOS.index(dados_atuais["TIPO DEMANDA"]) if dados_atuais["TIPO DEMANDA"] in LISTA_TIPOS else 0)
                novo_modulo = st.selectbox("Módulo", LISTA_MODULOS, index=LISTA_MODULOS.index(dados_atuais["MÓDULO"]) if dados_atuais["MÓDULO"] in LISTA_MODULOS else 0)
                novo_manual = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados_atuais["MANUAL"]) if dados_atuais["MANUAL"] in LISTA_MANUAIS else 0)
            with col2:
                data_str = str(dados_atuais["DATA LINKAGEM"])
                data_val = datetime.strptime(data_str, '%Y-%m-%d') if data_str and '-' in data_str else datetime.now()
                nova_data = str(st.date_input("Data Linkagem", value=data_val))
                novo_capitulo = st.text_input("Capítulo", value=str(dados_atuais["CAPITULO"]))
                nova_montadora = st.selectbox("Montadora", LISTA_MONTADORAS, index=LISTA_MONTADORAS.index(dados_atuais["MONTADORA"]) if dados_atuais["MONTADORA"] in LISTA_MONTADORAS else 0)
                nova_versao = st.selectbox("Versão", LISTA_VERSOES, index=LISTA_VERSOES.index(dados_atuais["VERSÃO"]) if dados_atuais["VERSÃO"] in LISTA_VERSOES else 0)
            
            if st.form_submit_button("Salvar Alterações"):
                try:
                    busca_str = str(demanda_selecionada)
                    cell = sheet.find(busca_str)
                    sheet.update(range_name=f"A{cell.row}:H{cell.row}", values=[[nova_demanda, novo_tipo, novo_modulo, novo_manual, nova_data, novo_capitulo, nova_montadora, nova_versao]])
                    st.success("Dados atualizados com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                except Exception as e:
                    st.error(f"Erro detalhado: {e}")

    with tab4:
        st.header("🗑️ Excluir Demanda")
        try:
            df_temp = pd.DataFrame(sheet.get_all_records(expected_headers=["DEMANDA", "TIPO DEMANDA", "MÓDULO", "MANUAL", "DATA LINKAGEM", "CAPITULO", "MONTADORA", "VERSÃO"]))
            demandas_disponiveis = df_temp["DEMANDA"].unique().tolist()
            demanda_selecionada = st.selectbox("1. Selecione a Demanda", [""] + demandas_disponiveis)
            if demanda_selecionada:
                datas_disponiveis = df_temp[df_temp["DEMANDA"] == demanda_selecionada]["DATA LINKAGEM"].unique().tolist()
                data_selecionada = st.selectbox("2. Selecione a Data", [""] + datas_disponiveis)
                if data_selecionada:
                    capitulos_disponiveis = df_temp[(df_temp["DEMANDA"] == demanda_selecionada) & (df_temp["DATA LINKAGEM"] == data_selecionada)]["CAPITULO"].unique().tolist()
                    capitulo_selecionado = st.selectbox("3. Selecione o Capítulo", [""] + capitulos_disponiveis)
                    if capitulo_selecionado:
                        with st.form("confirmar_exclusao"):
                            st.warning(f"Você tem certeza que deseja excluir a demanda: **{demanda_selecionada}**?")
                            if st.form_submit_button("Confirmar e Excluir Definitivamente"):
                                filtro = (df_temp["DEMANDA"] == demanda_selecionada) & (df_temp["DATA LINKAGEM"] == data_selecionada) & (df_temp["CAPITULO"] == capitulo_selecionado)
                                resultado = df_temp[filtro]
                                if not resultado.empty:
                                    sheet.delete_rows(resultado.index[0] + 2)
                                    st.success("Demanda excluída com sucesso!")
                                    st.rerun()
                                else:
                                    st.error("Erro: Registro não encontrado.")
        except Exception as e:
            st.error(f"Erro ao carregar filtros: {e}")

    with tab5:
        st.header("📊 Relatórios e Exportação")
        df_geral = carregar_dados()
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

        df_export = df_geral.copy()
        if filtro_versao != "Todas": df_export = df_export[df_export["VERSÃO"] == filtro_versao]
        if filtro_modulo != "Todos": df_export = df_export[df_export["MÓDULO"] == filtro_modulo]

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
            for i, row in df_export.iterrows():
                c.drawString(100, y, f"{row['DEMANDA']} - {row['MÓDULO']} - {row['VERSÃO']}")
                y -= 20
                if y < 50: c.showPage(); y = 800
            c.save()
            st.download_button("📥 Baixar PDF", data=buffer.getvalue(), file_name="relatorio.pdf", mime="application/pdf")# ... (Continue colando o restante das abas tab2, tab3, tab4 e tab5 aqui)