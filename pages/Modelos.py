import streamlit as st
import pandas as pd
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from config import sheet_modelos, carregar_dados_modelos, LISTA_MODULOS, LISTA_MANUAIS, LISTA_MONTADORAS

st.set_page_config(page_title="Gestão de Modelos", layout="wide")

st.title("📋 Controle de Modelos")

COLUNAS_ESPERADAS = ["MÓDULO", "MANUAL", "CAPITULO", "MONTADORA", "MODELO"]

# Abas
tab_m1, tab_m2, tab_m3, tab_m4, tab_m5 = st.tabs(["➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"])

with tab_m1:
    st.subheader("➕ Adicionar Modelos")
    modo_add = st.radio("Método de cadastro:", ["Manual", "Upload em Lote (Excel)"], horizontal=True)

    if modo_add == "Manual":
        with st.form("form_add_modelo", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                m_modulo = st.selectbox("Módulo", LISTA_MODULOS)
                m_manual = st.selectbox("Manual", LISTA_MANUAIS)
                m_capitulo = st.text_input("Capítulo")
            with col2:
                m_montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
                m_modelo = st.text_input("Modelo")

            if st.form_submit_button("Salvar Modelo"):
                if not m_modelo.strip():
                    st.error("O campo Modelo é obrigatório.")
                else:
                    try:
                        sheet_modelos.insert_row([m_modulo, m_manual, m_capitulo, m_montadora, m_modelo], index=2)
                        st.cache_data.clear()
                        st.success("Modelo salvo!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao salvar: {e}")
    else:
        st.info("O arquivo Excel deve conter as colunas: MÓDULO, MANUAL, CAPITULO, MONTADORA, MODELO")
        uploaded_file = st.file_uploader("Escolha o arquivo Excel", type=["xlsx"])
        if uploaded_file is not None:
            try:
                df_up = pd.read_excel(uploaded_file)
            except Exception as e:
                st.error(f"Não foi possível ler o arquivo: {e}")
                df_up = None

            if df_up is not None:
                colunas_faltando = [c for c in COLUNAS_ESPERADAS if c not in df_up.columns]
                if colunas_faltando:
                    st.error(f"O arquivo está sem as colunas: {', '.join(colunas_faltando)}")
                else:
                    st.dataframe(df_up[COLUNAS_ESPERADAS].head(10), use_container_width=True, hide_index=True)
                    st.caption(f"{len(df_up)} linha(s) prontas para importação.")
                    if st.button("Confirmar Importação em Lote"):
                        dados_formatados = df_up[COLUNAS_ESPERADAS].fillna("").values.tolist()
                        try:
                            sheet_modelos.insert_rows(dados_formatados, row=2)
                            st.cache_data.clear()
                            st.success(f"{len(dados_formatados)} modelo(s) importado(s)!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro na importação: {e}")

with tab_m2:
    st.subheader("🔍 Busca Avançada de Modelos")
    df_mod = carregar_dados_modelos()

    if df_mod.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        modo_busca_m = st.radio("Escolha o método de busca:", ["Filtros em Cascata", "Busca por Campo Específico"], key="radio_mod", horizontal=True)

        if modo_busca_m == "Filtros em Cascata":
            c1, c2, c3 = st.columns(3)
            with c1:
                mod_sel = st.selectbox("Módulo", ["Todos"] + df_mod["MÓDULO"].unique().tolist())
                man_sel = st.selectbox("Manual", ["Todos"] + df_mod["MANUAL"].unique().tolist())
            with c2:
                mont_sel = st.selectbox("Montadora", ["Todas"] + df_mod["MONTADORA"].unique().tolist())
                cap_sel = st.selectbox("Capítulo", ["Todos"] + df_mod["CAPITULO"].unique().tolist())
            with c3:
                model_sel = st.selectbox("Modelo", ["Todos"] + df_mod["MODELO"].unique().tolist())

            final_mod = df_mod.copy()
            if mod_sel != "Todos": final_mod = final_mod[final_mod["MÓDULO"] == mod_sel]
            if man_sel != "Todos": final_mod = final_mod[final_mod["MANUAL"] == man_sel]
            if mont_sel != "Todas": final_mod = final_mod[final_mod["MONTADORA"] == mont_sel]
            if cap_sel != "Todos": final_mod = final_mod[final_mod["CAPITULO"] == cap_sel]
            if model_sel != "Todos": final_mod = final_mod[final_mod["MODELO"] == model_sel]
            st.dataframe(final_mod.drop(columns=["_row"]), use_container_width=True, hide_index=True)
        else:
            colunas_visiveis = [c for c in df_mod.columns if c != "_row"]
            c1, c2 = st.columns([1, 2])
            with c1:
                coluna_alvo = st.selectbox("Selecione o campo:", colunas_visiveis, key="col_mod")
            with c2:
                valor_busca = st.text_input("Digite o valor para busca:", key="val_mod", placeholder="Ex: Ford")

            if valor_busca:
                resultado_mod = df_mod[df_mod[coluna_alvo].astype(str).str.contains(valor_busca, case=False, regex=False, na=False)]
                st.dataframe(resultado_mod[colunas_visiveis], use_container_width=True, hide_index=True)
            else:
                st.info("Digite um termo para começar a busca.")

with tab_m3:
    st.subheader("📝 Editar Modelo")
    df_mod = carregar_dados_modelos()

    if df_mod.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        modelo_sel = st.selectbox("Selecione o Modelo para editar:", df_mod["MODELO"].tolist())

        if modelo_sel:
            dados = df_mod[df_mod["MODELO"] == modelo_sel].iloc[0]
            linha_alvo = dados["_row"]
            with st.form("form_edit_m"):
                n_mod = st.selectbox("Módulo", LISTA_MODULOS, index=LISTA_MODULOS.index(dados["MÓDULO"]) if dados["MÓDULO"] in LISTA_MODULOS else 0)
                n_man = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados["MANUAL"]) if dados["MANUAL"] in LISTA_MANUAIS else 0)
                n_cap = st.text_input("Capítulo", value=dados["CAPITULO"])
                n_mon = st.selectbox("Montadora", LISTA_MONTADORAS, index=LISTA_MONTADORAS.index(dados["MONTADORA"]) if dados["MONTADORA"] in LISTA_MONTADORAS else 0)
                n_model = st.text_input("Modelo", value=dados["MODELO"])

                if st.form_submit_button("Atualizar"):
                    if not n_model.strip():
                        st.error("O campo Modelo é obrigatório.")
                    else:
                        try:
                            sheet_modelos.update(range_name=f"A{linha_alvo}:E{linha_alvo}", values=[[n_mod, n_man, n_cap, n_mon, n_model]])
                            st.cache_data.clear()
                            st.success("Atualizado!")
                            st.rerun()
                        except Exception as e:
                            st.error(f"Erro ao atualizar: {e}")

with tab_m4:
    st.subheader("🗑️ Excluir Modelo")
    df_mod = carregar_dados_modelos()

    if df_mod.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        m_del = st.selectbox("Selecione o Modelo a excluir", [""] + df_mod["MODELO"].tolist())

        if m_del:
            registro = df_mod[df_mod["MODELO"] == m_del].iloc[0]
            confirmar = st.checkbox("Confirmo que quero excluir este registro permanentemente.", key="confirma_del_modelo")
            if st.button("Confirmar Exclusão"):
                if not confirmar:
                    st.error("Marque a confirmação antes de excluir.")
                else:
                    try:
                        sheet_modelos.delete_rows(int(registro["_row"]))
                        st.cache_data.clear()
                        st.success("Excluído!")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao excluir: {e}")

with tab_m5:
    st.header("📊 Relatórios Detalhados")
    df_mod_geral = carregar_dados_modelos().copy()

    if df_mod_geral.empty:
        st.info("Nenhum modelo cadastrado ainda.")
    else:
        # --- 1. FILTROS DINÂMICOS ---
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
            formato = st.radio("Formato de Exportação:", ["Excel (.xlsx)", "PDF (.pdf)"], horizontal=True)

        # Aplicar filtros
        df_exp = df_mod_geral.drop(columns=["_row"]).copy()
        if f_mod != "Todos": df_exp = df_exp[df_exp["MÓDULO"] == f_mod]
        if f_man != "Todos": df_exp = df_exp[df_exp["MANUAL"] == f_man]
        if f_mon != "Todas": df_exp = df_exp[df_exp["MONTADORA"] == f_mon]
        if f_cap != "Todos": df_exp = df_exp[df_exp["CAPITULO"] == f_cap]
        if f_mod_ex != "Todos": df_exp = df_exp[df_exp["MODELO"] == f_mod_ex]

        # --- 2. VISUALIZAÇÃO NA TELA ---
        st.divider()
        st.write(f"### Visualização: {len(df_exp)} registros encontrados")
        st.dataframe(df_exp, use_container_width=True, hide_index=True)
        st.divider()

        # --- 3. EXPORTAÇÃO ---
        if not df_exp.empty:
            if formato == "Excel (.xlsx)":
                buffer = io.BytesIO()
                with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
                    df_exp.to_excel(writer, index=False)
                st.download_button("📥 Baixar Relatório Excel", data=buffer.getvalue(), file_name="relatorio_modelos.xlsx", mime="application/vnd.ms-excel")
            else:  # PDF
                buffer = io.BytesIO()
                c = canvas.Canvas(buffer, pagesize=A4)
                c.setFont("Helvetica-Bold", 16)
                c.drawString(50, 800, "Relatório de Modelos")
                c.setFont("Helvetica", 10)
                y = 750
                for _, row in df_exp.iterrows():
                    linha = f"{row['MÓDULO']} | {row['MANUAL']} | {row['MONTADORA']} | {row['MODELO']}"
                    c.drawString(50, y, linha)
                    y -= 20
                    if y < 50:
                        c.showPage()
                        y = 800
                c.save()
                st.download_button("📥 Baixar Relatório PDF", data=buffer.getvalue(), file_name="relatorio_modelos.pdf", mime="application/pdf")
        else:
            st.warning("Nenhum registro encontrado para exportar.")