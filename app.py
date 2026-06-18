import streamlit as st
import pandas as pd
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime

# --- CONFIGURAÇÃO DA CONEXÃO ---
def conectar_gsheets():
    # Isso vai buscar os dados que você colará na aba 'Secrets' do Streamlit Cloud
    creds_dict = st.secrets["gcp_service_account"]
    
    # Prepara as credenciais usando o dicionário
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    
    client = gspread.authorize(creds)
    spreadsheet_id = "10F1PqOSXUj_tbN7qrm9qXKnKJQ7xcHUmtIOB72FpWaM"
    return client.open_by_key(spreadsheet_id).sheet1

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
LISTA_MONTADORAS = ["AGRALE", "ALFA ROMEO", "AUDI", "BMW", "BYD", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DAEWOO", "DAF", "DAIHATSU", "DODGE", "DUCATI", "EFFA", "FIAT", "FORD", "GWM", "HARLEY DAVIDSON", "HONDA", "HUMMER", "HYUNDAI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC MOTORS", "JAGUAR", "JEEP", "KAWASAKI", "KIA", "LAND ROVER", "LEXUS", "LIFAN", "MAN", "MASERATI", "MAZDA", "MERCEDES-BENZ TRUCK", "MERCEDES-BENZ", "MG MOTORS", "MINI", "MITSUBISHI", "NISSAN", "PEUGEOT", "PORSCHE", "RAM", "RENAULT", "SCANIA", "SEAT", "SMART", "SSANGYONG", "SUBARU", "SUZUKI", "TROLLER", "TOYOTA", "VOLVO", "VOLVO TRUCK", "VOLKSWAGEN", "VOLKSWAGEN TRUCK", "YAMAHA", "JOHN DEERE", "VALTRA", "MASSEY FERGUSON", "NEW HOLLAND", "MAXION-PERKINS", "CASE"]
LISTA_VERSOES = ["2024/2", "2024/3", "2025/1", "2025/2", "2025/3"]

# --- INTERFACE POR ABAS ---
tab1, tab2, tab3, tab4 = st.tabs(["➕ Adicionar", "🔍 Buscar", "📝 Editar", "🗑️ Excluir"])

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
            data_linkagem = str(st.date_input("Data Linkagem"))
            capitulo = st.text_input("Capítulo")
            montadora = st.selectbox("Montadora", LISTA_MONTADORAS)
            versao = st.selectbox("Versão", LISTA_VERSOES)
        
        if st.form_submit_button("Salvar Nova Demanda"):
            sheet.insert_row([demanda, tipo, modulo, manual, data_linkagem, capitulo, montadora, versao], index=2)
            st.success("Salvo com sucesso!")
            st.cache_data.clear() # Limpa o cache para atualizar a busca
            st.rerun()

with tab2:
    st.subheader("Visualizar e Filtrar")
    busca = st.text_input("Filtrar por nome da demanda:")
    df = carregar_dados()
    if busca:
        df = df[df['DEMANDA'].astype(str).str.contains(busca, case=False)]
    st.dataframe(df, use_container_width=True)

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
    st.header("Excluir Demanda")
    
    # Exemplo de como capturar as escolhas do usuário antes do botão
    form_exclusao = st.form("form_exclusao")
    with form_exclusao:
        col1, col2, col3 = st.columns(3)
        with col1:
            demanda_selecionada = st.selectbox("Selecione a Demanda", df['Demanda'].unique())
        with col2:
            data_selecionada = st.selectbox("Selecione a Data", df['Data'].unique())
        with col3:
            capitulo_selecionado = st.selectbox("Selecione o Capítulo", df['Capitulo'].unique())
            
        if st.form_submit_button("Excluir Demanda"):
            try:
                # Carrega dados atualizados para garantir que temos o índice certo
                dados = sheet.get_all_records()
                df_atual = pd.DataFrame(dados)
                
                # Aplica o filtro triplo
                filtro = (df_atual['Demanda'] == demanda_selecionada) & \
                         (df_atual['Data'] == data_selecionada) & \
                         (df_atual['Capitulo'] == capitulo_selecionado)
                
                resultado = df_atual[filtro]
                
                if not resultado.empty:
                    # O index do pandas + 2 (cabeçalho + base 1 do gspread)
                    linha_para_excluir = resultado.index[0] + 2
                    
                    sheet.delete_rows(linha_para_excluir)
                    
                    st.success("Demanda excluída com sucesso!")
                    st.cache_data.clear()
                    st.rerun()
                else:
                    st.error("Nenhum registro encontrado com esses critérios!")
                    
            except Exception as e:
                st.error(f"Erro ao processar exclusão: {e}")