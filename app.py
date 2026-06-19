import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import io
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas

# --- CONFIGURAÇÃO DA CONEXÃO ---
def conectar_gsheets():
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    client = gspread.authorize(creds)
    spreadsheet_id = "10F1PqOSXUj_tbN7qrm9qXKnKJQ7xcHUmtIOB72FpWaM"
    
    # Abre o arquivo e seleciona a primeira aba explicitamente
    spreadsheet = client.open_by_key(spreadsheet_id)
    return spreadsheet.get_worksheet(0) # 0 é a primeira aba

sheet = conectar_gsheets()

@st.cache_data(ttl=10) # Cache curto para refletir edições rápido
def carregar_dados():
    data = sheet.get_all_records(expected_headers=[
        "DEMANDA", "TIPO DEMANDA", "MÓDULO", "MANUAL", 
        "DATA LINKAGEM", "CAPITULO", "MONTADORA", "VERSÃO"
    ])
    return pd.DataFrame(data)

st.set_page_config(page_title="Controle de Demandas", layout="wide")
st.title("📋 Controle de Demandas")

# Definição das listas de opções para reuso nos formulários
LISTA_TIPOS = ["NOVA", "CORREÇÃO", "UPGRADE"]
LISTA_MODULOS = ["SIMPLO", "ELETRICOS", "HIBRIDOS", "TRACTOR", "MOTOS"]
LISTA_MANUAIS = ["ABS/ASR/ESP", "CÂMBIO", "CÂMBIO TRUCK", "TABELA DE GÁS TRUCK", "TABELA DE GÁS", "CLIMA CAR", "CLIMA TRUCK", "CÓDIGO DE FALHAS", "ELECTRA", "ELECTRA TRUCK", "INJEÇÃO", "DIESEL", "ARLA", "LOCAR", "LOCAR TRUCK", "LUBRITEC", "MIX", "MIX - AIRBAG", "MIX - ALARMES", "MIX - IMOBILIZADOR", "MIX - RESETS", "MOTORES", "MOTORES - LINHA LEVE", "MOTORES - LINHA PESADA", "MT PRO", "PICO SCOPE", "REVISA CAR", "TABELA DE TORQUES DAS RODAS", "TORKS - DIREÇÃO", "TORKS TRUCK - DIREÇÃO", "TORKS - FREIOS", "TORKS TRUCK - FREIOS", "TORKS - SUSPENSÃO", "TORKS TRUCK - SUSPENSÃO", "TORKS TRUCK", "SCOPE TRUCK (MT PRO)", "SCOPE TRUCK (PICO SCOPE)", "SINCRO", "SINCRO - CORREIAS", "SINCRO - CORRENTES", "SINCRO - POLY-V", "MOTORES TRACTOR", "CLIMA TRACTOR", "SINCRO TRACTOR", "ELECTRA TRACTOR", "INJEÇÃO TRACTOR", "CÂMBIO TRACTOR", "MT PRO TRACTOR", "PICO SCOPE TRACTOR", "CODIGO DE FALHAS TRACTOR", "LUBRITEC MOTOS", "CODIGO DE FALHAS MOTOS", "INJEÇÃO MOTOS", "ELECTRA MOTOS", "ABS MOTOS", "MOTORES MOTOS", "ELETRICOS", "ELETRICOS - TORKS", "ELETRICOS - LUBRITEC", "ELETRICOS - REVISA", "ELETRICOS - LOCAR", "ELETRICOS - RESETS", "ELETRICOS - ABS", "ELETRICOS - AC", "ELETRICOS - INTERLOCK", "ELETRICOS - CÓDIGO DE FALHAS", "H&E - TORKS", "H&E - CÓDIGO DE FALHAS", "H&E - ELECTRA", "H&E - SINCRO", "H&E - LOCAR", "H&E - RESETS", "H&E - MT PRO", "H&E - ABS", "H&E - AC", "H&E - INTERLOCK", "H&E", "H&E - INJEÇÃO", "H&E - MOTORES", "H&E - LUBRITEC", "H&E - REVISA CAR"]
LISTA_MONTADORAS = ["  ", "AGRALE", "ALFA ROMEO", "AUDI", "BMW", "BYD", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DAEWOO", "DAF", "DAIHATSU", "DODGE", "DUCATI", "EFFA", "FIAT", "FORD", "GWM", "HARLEY DAVIDSON", "HONDA", "HUMMER", "HYUNDAI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC MOTORS", "JAGUAR", "JEEP", "KAWASAKI", "KIA", "LAND ROVER", "LEXUS", "LIFAN", "MAN", "MASERATI", "MAZDA", "MERCEDES-BENZ TRUCK", "MERCEDES-BENZ", "MG MOTORS", "MINI", "MITSUBISHI", "NISSAN", "PEUGEOT", "PORSCHE", "RAM", "RENAULT", "SCANIA", "SEAT", "SMART", "SSANGYONG", "SUBARU", "SUZUKI", "TROLLER", "TOYOTA", "VOLVO", "VOLVO TRUCK", "VOLKSWAGEN", "VOLKSWAGEN TRUCK", "YAMAHA", "JOHN DEERE", "VALTRA", "MASSEY FERGUSON", "NEW HOLLAND", "MAXION-PERKINS", "CASE"]
LISTA_VERSOES = ["2024/1", "2024/2", "2024/3", "2025/1", "2025/2", "2025/3", "2026/1", "2026/2", "2026/3", "2027/1", "2027/2", "2027/3", "2024/1 T", "2024/2 T", "2024/3 T", "2025/1 T", "2025/2 T", "2025/3 T", "2026/1 T", "2026/2 T", "2026/3 T", "2027/1 T", "2027/2 T", "2027/3 T", "2024/1 H&E", "2024/2 H&E", "2024/3 H&E", "2025/1 H&E", "2025/2 H&E", "2025/3 H&E", "2026/1 H&E", "2026/2 H&E", "2026/3 H&E", "2027/1 H&E", "2027/2 H&E", "2027/3 H&E", "2024/1 M", "2024/2 M", "2024/3 M", "2025/1 M", "2025/2 M", "2025/3 M", "2026/1 M", "2026/2 M", "2026/3 M", "2027/1 M", "2027/2 M", "2027/3 M"]

# --- INTERFACE POR ABAS ---
tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "➕ Adicionar", 
    "🔍 Buscar", 
    "📝 Editar", 
    "🗑️ Excluir", 
    "📊 Relatórios"
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
            # 1. Captura o objeto date (st.date_input retorna um objeto date, não uma string)
            data_obj = st.date_input("Data Linkagem")
    
            # 2. Converte para o formato brasileiro
            data_linkagem = data_obj.strftime("%d/%m/%Y") if data_obj else ""
            capitulo = st.text_input("Capítulo")
            montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
            versao = st.selectbox("Versão", LISTA_VERSOES)
        
        if st.form_submit_button("Salvar Nova Demanda"):
            sheet.insert_row([demanda, tipo, modulo, manual, data_linkagem, capitulo, montadora, versao], index=2)
            st.success("Salvo com sucesso!")
            st.cache_data.clear() # Limpa o cache para atualizar a busca
            st.rerun()

with tab2:
    st.subheader("🔍 Busca Avançada")
    df = carregar_dados()
    
    # Escolha do método de busca
    modo_busca = st.radio("Escolha o método de busca:", ["Filtros em Cascata", "Busca por Campo Específico"])

    if modo_busca == "Filtros em Cascata":
        st.sidebar.header("Filtros em Cascata")
        
        # 1. Módulo
        mod_sel = st.sidebar.selectbox("Módulo", ["Todos"] + df["MÓDULO"].unique().tolist())
        df_f1 = df if mod_sel == "Todos" else df[df["MÓDULO"] == mod_sel]
        
        # 2. Tipo Demanda
        tipo_sel = st.sidebar.selectbox("Tipo", ["Todos"] + df_f1["TIPO DEMANDA"].unique().tolist())
        df_f2 = df_f1 if tipo_sel == "Todos" else df_f1[df_f1["TIPO DEMANDA"] == tipo_sel]
        
        # 3. Montadora (NOVO)
        mont_sel = st.sidebar.selectbox("Montadora", ["Todas"] + df_f2["MONTADORA"].unique().tolist())
        df_f3 = df_f2 if mont_sel == "Todas" else df_f2[df_f2["MONTADORA"] == mont_sel]
        
        # 4. Manual (NOVO)
        man_sel = st.sidebar.selectbox("Manual", ["Todos"] + df_f3["MANUAL"].unique().tolist())
        df_f4 = df_f3 if man_sel == "Todos" else df_f3[df_f3["MANUAL"] == man_sel]
        
        # 5. Demanda
        dem_sel = st.sidebar.selectbox("Demanda", ["Todas"] + df_f4["DEMANDA"].unique().tolist())
        
        # Aplicar filtros
        final = df_f4 if dem_sel == "Todas" else df_f4[df_f4["DEMANDA"] == dem_sel]
        st.dataframe(final, use_container_width=True)

    else:
        st.sidebar.header("Busca Específica")
        # Escolhe qual coluna pesquisar
        coluna_alvo = st.sidebar.selectbox("Selecione o campo para buscar:", df.columns.tolist())
        valor_busca = st.sidebar.text_input(f"Digite o valor para {coluna_alvo}:")
        
        if valor_busca:
            resultado = df[df[coluna_alvo].astype(str).str.contains(valor_busca, case=False)]
            st.write(f"Resultados para '{valor_busca}' em {coluna_alvo}:")
            st.dataframe(resultado, use_container_width=True)
        else:
            st.info("Selecione o campo e digite o valor na barra lateral.")

with tab3:
    st.subheader("Alterar Demanda Existente")
    df_edit = carregar_dados()
    demanda_selecionada = st.selectbox("Selecione a demanda para editar:", options=df_edit["DEMANDA"].tolist(), key="edit_select")
    
    # Busca os dados atuais da demanda selecionada para preencher o formulário
    dados_atuais = df_edit[df_edit["DEMANDA"] == demanda_selecionada].iloc[0]

    with st.form("form_editar"):
        col1, col2 = st.columns(2)
        with col1:
            nova_demanda = st.text_input("Demanda", value=str(dados_atuais["DEMANDA"]))
            novo_tipo = st.selectbox("Tipo", LISTA_TIPOS, index=LISTA_TIPOS.index(dados_atuais["TIPO DEMANDA"]) if dados_atuais["TIPO DEMANDA"] in LISTA_TIPOS else 0)
            novo_modulo = st.selectbox("Módulo", LISTA_MODULOS, index=LISTA_MODULOS.index(dados_atuais["MÓDULO"]) if dados_atuais["MÓDULO"] in LISTA_MODULOS else 0)
            novo_manual = st.selectbox("Manual", LISTA_MANUAIS, index=LISTA_MANUAIS.index(dados_atuais["MANUAL"]) if dados_atuais["MANUAL"] in LISTA_MANUAIS else 0)
        with col2:
            # Tratamento de data para evitar erro se estiver vazio
            data_str = str(dados_atuais["DATA LINKAGEM"])
            data_val = datetime.strptime(data_str, '%Y-%m-%d') if data_str and '-' in data_str else datetime.now()
            nova_data = str(st.date_input("Data Linkagem", value=data_val))
            
            novo_capitulo = st.text_input("Capítulo", value=str(dados_atuais["CAPITULO"]))
            nova_montadora = st.selectbox("Montadora", LISTA_MONTADORAS, index=LISTA_MONTADORAS.index(dados_atuais["MONTADORA"]) if dados_atuais["MONTADORA"] in LISTA_MONTADORAS else 0)
            nova_versao = st.selectbox("Versão", LISTA_VERSOES, index=LISTA_VERSOES.index(dados_atuais["VERSÃO"]) if dados_atuais["VERSÃO"] in LISTA_VERSOES else 0)
        
        if st.form_submit_button("Salvar Alterações"):
            try:
                # 1. Garante que o valor seja uma string pura
                busca_str = str(demanda_selecionada)
                
                # 2. Localiza a célula
                cell = sheet.find(busca_str)
                
                # 3. Prepara os novos valores
                novos_valores = [nova_demanda, novo_tipo, novo_modulo, novo_manual, nova_data, novo_capitulo, nova_montadora, nova_versao]
                
                # 4. Atualiza garantindo o formato correto (lista de listas)
                sheet.update(range_name=f"A{cell.row}:H{cell.row}", values=[novos_valores])
                
                st.success("Dados atualizados com sucesso!")
                st.cache_data.clear()
                st.rerun()
            except Exception as e:
                st.error(f"Erro detalhado: {e}")

with tab4:
    st.header("🗑️ Excluir Demanda")
    
    try: # <--- O TRY COMEÇA AQUI
        # Recarrega dados
        df_temp = pd.DataFrame(sheet.get_all_records(expected_headers=["DEMANDA", "TIPO DEMANDA", "MÓDULO", "MANUAL", "DATA LINKAGEM", "CAPITULO", "MONTADORA", "VERSÃO"]))
        
        # Filtros Cascata
        demandas_disponiveis = df_temp["DEMANDA"].unique().tolist()
        demanda_selecionada = st.selectbox("1. Selecione a Demanda", [""] + demandas_disponiveis)
        
        if demanda_selecionada:
            datas_disponiveis = df_temp[df_temp["DEMANDA"] == demanda_selecionada]["DATA LINKAGEM"].unique().tolist()
            data_selecionada = st.selectbox("2. Selecione a Data", [""] + datas_disponiveis)
            
            if data_selecionada:
                capitulos_disponiveis = df_temp[
                    (df_temp["DEMANDA"] == demanda_selecionada) & 
                    (df_temp["DATA LINKAGEM"] == data_selecionada)
                ]["CAPITULO"].unique().tolist()
                
                capitulo_selecionado = st.selectbox("3. Selecione o Capítulo", [""] + capitulos_disponiveis)
                
                # --- O FORMULÁRIO DE CONFIRMAÇÃO ---
                if capitulo_selecionado:
                    with st.form("confirmar_exclusao"):
                        st.warning(f"Você tem certeza que deseja excluir a demanda: **{demanda_selecionada}**?")
                        btn_excluir = st.form_submit_button("Confirmar e Excluir Definitivamente")
                        
                        if btn_excluir:
                            filtro = (df_temp["DEMANDA"] == demanda_selecionada) & \
                                     (df_temp["DATA LINKAGEM"] == data_selecionada) & \
                                     (df_temp["CAPITULO"] == capitulo_selecionado)
                            
                            resultado = df_temp[filtro]
                            
                            if not resultado.empty:
                                linha_para_excluir = resultado.index[0] + 2
                                sheet.delete_rows(linha_para_excluir)
                                st.success("Demanda excluída com sucesso!")
                                st.rerun() 
                            else:
                                st.error("Erro: Registro não encontrado na planilha.")

    except Exception as e: # <--- O EXCEPT AGORA ESTÁ LIGADO AO TRY
        st.error(f"Erro ao carregar filtros: {e}")

with tab5:
    st.header("📊 Relatórios e Exportação")
    df_geral = carregar_dados()
    
    # --- 1. MÉTRICAS E DISTRIBUIÇÃO ---
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("Por Versão")
        
        # Garantimos que a coluna é texto, removemos espaços e só depois ordenamos
        df_geral["VERSÃO"] = df_geral["VERSÃO"].astype(str).str.strip()
        contagem_versao = df_geral["VERSÃO"].value_counts().sort_index()
        
        st.bar_chart(contagem_versao)
        
    with col2:
        st.subheader("Por Módulo")
        # Garantimos que a coluna é texto, removemos espaços e só depois ordenamos
        df_geral["MÓDULO"] = df_geral["MÓDULO"].astype(str).str.strip()
        contagem_modulo = df_geral["MÓDULO"].value_counts().sort_index()
        st.bar_chart(contagem_modulo)

    st.divider()

    # --- 2. GERADOR DE RELATÓRIO FILTRADO ---
    st.subheader("📥 Gerar e Exportar Relatório")
    col_sel, formato_sel = st.columns(2)
    with col_sel:
        filtro_versao = st.selectbox("Versão:", ["Todas"] + df_geral["VERSÃO"].unique().tolist())
        filtro_modulo = st.selectbox("Módulo:", ["Todos"] + df_geral["MÓDULO"].unique().tolist())
    
    with formato_sel:
        formato = st.radio("Formato de exportação:", ["Excel (.xlsx)", "PDF (.pdf)"])

    # Filtragem
    df_export = df_geral.copy()
    if filtro_versao != "Todas": df_export = df_export[df_export["VERSÃO"] == filtro_versao]
    if filtro_modulo != "Todos": df_export = df_export[df_export["MÓDULO"] == filtro_modulo]

    # Lógica de Exportação
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
            texto = f"{row['DEMANDA']} - {row['MÓDULO']} - {row['VERSÃO']}"
            c.drawString(100, y, texto)
            y -= 20
            if y < 50: # Nova página se necessário
                c.showPage()
                y = 800
        c.save()
        st.download_button("📥 Baixar PDF", data=buffer.getvalue(), file_name="relatorio.pdf", mime="application/pdf")