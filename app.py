import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- DEFINA A FUNÇÃO AQUI NO TOPO ---
@st.cache_data(ttl=600)
def carregar_dados_sheet(sheet):
    return pd.DataFrame(sheet.get_all_records())

st.set_page_config(page_title="Gestão Integrada", layout="wide")

# --- CONFIGURAÇÃO DAS CONEXÕES ---
@st.cache_resource
def conectar_gsheets():
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    return gspread.authorize(creds)

client = conectar_gsheets()

# Conexões
try:
    sheet_demandas = client.open_by_key("10F1PqOSXUj_tbN7qrm9qXKnKJQ7xcHUmtIOB72FpWaM").get_worksheet(0)
    sheet_modelos = client.open_by_key("1fYwQ2uoqXY6QJm0Kk9dW2vX0tjgbSuTeFNfONe8UWMs").get_worksheet(0)
    sheet = sheet_demandas # Referência que seu código original espera
except Exception as e:
    st.error(f"Erro ao conectar nas planilhas: {e}")

# Definição das listas
LISTA_TIPOS = ["NOVA", "CORREÇÃO", "UPGRADE"]
LISTA_MODULOS = ["SIMPLO", "ELETRICOS", "HIBRIDOS", "TRACTOR", "MOTOS"]
LISTA_MANUAIS = ["ABS/ASR/ESP", "CÂMBIO", "CÂMBIO TRUCK", "TABELA DE GÁS TRUCK", "TABELA DE GÁS", "CLIMA CAR", "CLIMA TRUCK", "CÓDIGO DE FALHAS", "ELECTRA", "ELECTRA TRUCK", "INJEÇÃO", "DIESEL", "ARLA", "LOCAR", "LOCAR TRUCK", "LUBRITEC", "MIX", "MIX - AIRBAG", "MIX - ALARMES", "MIX - IMOBILIZADOR", "MIX - RESETS", "MOTORES", "MOTORES - LINHA LEVE", "MOTORES - LINHA PESADA", "MT PRO", "PICO SCOPE", "REVISA CAR", "TABELA DE TORQUES DAS RODAS", "TORKS - DIREÇÃO", "TORKS TRUCK - DIREÇÃO", "TORKS - FREIOS", "TORKS TRUCK - FREIOS", "TORKS - SUSPENSÃO", "TORKS TRUCK - SUSPENSÃO", "TORKS TRUCK", "SCOPE TRUCK (MT PRO)", "SCOPE TRUCK (PICO SCOPE)", "SINCRO", "SINCRO - CORREIAS", "SINCRO - CORRENTES", "SINCRO - POLY-V", "MOTORES TRACTOR", "CLIMA TRACTOR", "SINCRO TRACTOR", "ELECTRA TRACTOR", "INJEÇÃO TRACTOR", "CÂMBIO TRACTOR", "MT PRO TRACTOR", "PICO SCOPE TRACTOR", "CODIGO DE FALHAS TRACTOR", "LUBRITEC MOTOS", "CODIGO DE FALHAS MOTOS", "INJEÇÃO MOTOS", "ELECTRA MOTOS", "ABS MOTOS", "MOTORES MOTOS", "ELETRICOS", "ELETRICOS - TORKS", "ELETRICOS - LUBRITEC", "ELETRICOS - REVISA", "ELETRICOS - LOCAR", "ELETRICOS - RESETS", "ELETRICOS - ABS", "ELETRICOS - AC", "ELETRICOS - INTERLOCK", "ELETRICOS - CÓDIGO DE FALHAS", "H&E - TORKS", "H&E - CÓDIGO DE FALHAS", "H&E - ELECTRA", "H&E - SINCRO", "H&E - LOCAR", "H&E - RESETS", "H&E - MT PRO", "H&E - ABS", "H&E - AC", "H&E - INTERLOCK", "H&E", "H&E - INJEÇÃO", "H&E - MOTORES", "H&E - LUBRITEC", "H&E - REVISA CAR"]
LISTA_MONTADORAS = ["  ", "AGRALE", "ALFA ROMEO", "AUDI", "BMW", "BYD", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DAEWOO", "DAF", "DAIHATSU", "DODGE", "DUCATI", "EFFA", "FIAT", "FORD", "GWM", "HARLEY DAVIDSON", "HONDA", "HUMMER", "HYUNDAI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC MOTORS", "JAGUAR", "JEEP", "KAWASAKI", "KIA", "LAND ROVER", "LEXUS", "LIFAN", "MAN", "MASERATI", "MAZDA", "MERCEDES-BENZ TRUCK", "MERCEDES-BENZ", "MG MOTORS", "MINI", "MITSUBISHI", "NISSAN", "PEUGEOT", "PORSCHE", "RAM", "RENAULT", "SCANIA", "SEAT", "SMART", "SSANGYONG", "SUBARU", "SUZUKI", "TROLLER", "TOYOTA", "VOLVO", "VOLVO TRUCK", "VOLKSWAGEN", "VOLKSWAGEN TRUCK", "YAMAHA", "JOHN DEERE", "VALTRA", "MASSEY FERGUSON", "NEW HOLLAND", "MAXION-PERKINS", "CASE"]
LISTA_VERSOES = ["2024/1", "2024/2", "2024/3", "2025/1", "2025/2", "2025/3", "2026/1", "2026/2", "2026/3", "2027/1", "2027/2", "2027/3", "2024/1 T", "2024/2 T", "2024/3 T", "2025/1 T", "2025/2 T", "2025/3 T", "2026/1 T", "2026/2 T", "2026/3 T", "2027/1 T", "2027/2 T", "2027/3 T", "2024/1 H&E", "2024/2 H&E", "2024/3 H&E", "2025/1 H&E", "2025/2 H&E", "2025/3 H&E", "2026/1 H&E", "2026/2 H&E", "2026/3 H&E", "2027/1 H&E", "2027/2 H&E", "2027/3 H&E", "2024/1 M", "2024/2 M", "2024/3 M", "2025/1 M", "2025/2 M", "2025/3 M", "2026/1 M", "2026/2 M", "2026/3 M", "2027/1 M", "2027/2 M", "2027/3 M"]

# --- FUNÇÃO CARREGAR DADOS ---
@st.cache_data(ttl=10)
def carregar_dados():
    return pd.DataFrame(sheet_demandas.get_all_records(expected_headers=["DEMANDA", "TIPO DEMANDA", "MÓDULO", "MANUAL", "DATA LINKAGEM", "CAPITULO", "MONTADORA", "VERSÃO"]))

# --- MENU DE NAVEGAÇÃO ---
st.sidebar.title("🧭 Menu Principal")
escolha = st.sidebar.selectbox("Selecione o Módulo:", ["Controle de Demandas", "Lista de Modelos"])

if escolha == "Lista de Modelos":
    # CARREGUE APENAS UMA VEZ AQUI
    df_mod = carregar_dados_sheet(sheet_modelos)
    # Criando as mesmas abas para o módulo de modelos
    tab_m1, tab_m2, tab_m3, tab_m4, tab_m5 = st.tabs([
        "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
    ])

    with tab_m1:
        st.subheader("➕ Adicionar Modelos")
        
        # Escolha entre manual ou lote
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
                    sheet_modelos.insert_row([m_modulo, m_manual, m_capitulo, m_montadora, m_modelo], index=2)
                    st.success("Modelo salvo com sucesso!")
                    st.rerun()

        else:
            st.info("O arquivo deve conter as colunas: MÓDULO, MANUAL, CAPITULO, MONTADORA, MODELO")
            uploaded_file = st.file_uploader("Escolha seu arquivo Excel", type=["xlsx"])
            
            if uploaded_file is not None:
                df_upload = pd.read_excel(uploaded_file)
                st.write("Pré-visualização dos dados que serão enviados:")
                st.dataframe(df_upload.head())
                
                if st.button("Confirmar Importação em Lote"):
                    try:
                        # Converte o df para lista de listas para o gspread
                        dados_para_inserir = df_upload.values.tolist()
                        sheet_modelos.append_rows(dados_para_inserir)
                        st.success(f"Sucesso! {len(dados_para_inserir)} modelos foram adicionados.")
                        st.rerun()
                    except Exception as e:
                        st.error(f"Erro ao processar arquivo: {e}")

    with tab_m2:
        st.subheader("🔍 Busca Avançada de Modelos")
        st.dataframe(df_mod)
        
        modo_busca_m = st.radio("Escolha o método de busca:", ["Filtros em Cascata", "Busca por Campo Específico"], key="radio_mod", horizontal=True)

        if modo_busca_m == "Filtros em Cascata":
            # Usando colunas mais equilibradas (Grid 3x2)
            c1, c2, c3 = st.columns(3)
            
            with c1:
                mod_sel = st.selectbox("Módulo", ["Todos"] + df_mod["MÓDULO"].unique().tolist())
                man_sel = st.selectbox("Manual", ["Todos"] + df_mod["MANUAL"].unique().tolist())
            with c2:
                mont_sel = st.selectbox("Montadora", ["Todas"] + df_mod["MONTADORA"].unique().tolist())
                cap_sel = st.selectbox("Capítulo", ["Todos"] + df_mod["CAPITULO"].unique().tolist())
            with c3:
                model_sel = st.selectbox("Modelo", ["Todos"] + df_mod["MODELO"].unique().tolist())
                st.info(f"Total: {len(df_mod)} registros")

            # Lógica de Filtragem (mais enxuta)
            final_mod = df_mod.copy()
            if mod_sel != "Todos": final_mod = final_mod[final_mod["MÓDULO"] == mod_sel]
            if man_sel != "Todos": final_mod = final_mod[final_mod["MANUAL"] == man_sel]
            if mont_sel != "Todas": final_mod = final_mod[final_mod["MONTADORA"] == mont_sel]
            if cap_sel != "Todos": final_mod = final_mod[final_mod["CAPITULO"] == cap_sel]
            if model_sel != "Todos": final_mod = final_mod[final_mod["MODELO"] == model_sel]
                
            st.divider()
            st.dataframe(final_mod, use_container_width=True, hide_index=True)

        else:
            # Layout mais limpo para busca específica
            c1, c2 = st.columns([1, 2])
            with c1:
                coluna_alvo = st.selectbox("Selecione o campo:", df_mod.columns.tolist(), key="col_mod")
            with c2:
                valor_busca = st.text_input("Digite o valor para busca:", key="val_mod", placeholder="Ex: Ford")
            
            if valor_busca:
                resultado_mod = df_mod[df_mod[coluna_alvo].astype(str).str.contains(valor_busca, case=False)]
                st.dataframe(resultado_mod, use_container_width=True, hide_index=True)
            else:
                st.info("Digite um termo para começar a busca.")

    with tab_m3:
        st.subheader("📝 Editar Modelo")
        df_mod = pd.DataFrame(sheet_modelos.get_all_records())
        modelo_sel = st.selectbox("Selecione o Modelo para editar:", df_mod["MODELO"].tolist())
        dados = df_mod[df_mod["MODELO"] == modelo_sel].iloc[0]
        with st.form("form_edit_m"):
            n_mod = st.selectbox("Módulo", LISTA_MODULOS, index=LISTA_MODULOS.index(dados["MÓDULO"]))
            n_man = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados["MANUAL"]))
            n_cap = st.text_input("Capítulo", value=dados["CAPITULO"])
            n_mon = st.selectbox("Montadora", LISTA_MONTADORAS, index=LISTA_MONTADORAS.index(dados["MONTADORA"]))
            n_model = st.text_input("Modelo", value=dados["MODELO"])
            if st.form_submit_button("Atualizar"):
                cell = sheet_modelos.find(modelo_sel)
                sheet_modelos.update(range_name=f"A{cell.row}:E{cell.row}", values=[[n_mod, n_man, n_cap, n_mon, n_model]])
                st.success("Atualizado!")
                st.rerun()

    with tab_m4:
        st.subheader("🗑️ Excluir Modelo")
        df_mod = pd.DataFrame(sheet_modelos.get_all_records())
        m_del = st.selectbox("Selecione o Modelo a excluir", [""] + df_mod["MODELO"].tolist())
        if m_del:
            if st.button("Confirmar Exclusão"):
                cell = sheet_modelos.find(m_del)
                sheet_modelos.delete_rows(cell.row)
                st.success("Excluído!")
                st.rerun()

    with tab_m5:
        st.header("📊 Relatórios Detalhados")
        # Carrega os dados uma vez para o relatório
        df_mod_geral = pd.DataFrame(sheet_modelos.get_all_records())
        
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
        df_exp = df_mod_geral.copy()
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
            
            else: # PDF
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
                    if y < 50: c.showPage(); y = 800
                c.save()
                st.download_button("📥 Baixar Relatório PDF", data=buffer.getvalue(), file_name="relatorio_modelos.pdf", mime="application/pdf")
        else:
            st.warning("Nenhum registro encontrado para exportar.")

else:
    st.title("📋 Controle de Demandas")
    
    # --- INTERFACE POR ABAS ---
    tab1, tab2, tab3, tab4, tab5 = st.tabs([
        "➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir", "📊 Relatórios"
    ])

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
            st.download_button("📥 Baixar PDF", data=buffer.getvalue(), file_name="relatorio.pdf", mime="application/pdf")