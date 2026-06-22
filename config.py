import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd

# Defina os IDs das suas planilhas aqui
ID_DEMANDAS = "10F1PqOSXUj_tbN7qrm9qXKnKJQ7xcHUmtIOB72FpWaM"
ID_MODELOS = "1fYwQ2uoqXY6QJm0Kk9dW2vX0tjgbSuTeFNfONe8UWMs"
ID_CAPITULOS = "1TN-tegne416QaqJQiTV9kr6f5AS332XkUMmv4_FsRaU" # <--- COLOQUE O ID DA PLANILHA DE CAPITULOS AQUI

# Conexão
@st.cache_resource
def conectar_gsheets():
    creds_dict = st.secrets["gcp_service_account"]
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
        'https://www.googleapis.com/auth/spreadsheets',
        'https://www.googleapis.com/auth/drive'
    ])
    return gspread.authorize(creds)

client = conectar_gsheets()

# Conexão com as abas
sheet_demandas = client.open_by_key(ID_DEMANDAS).get_worksheet(0)
sheet_modelos = client.open_by_key(ID_MODELOS).get_worksheet(0)
sheet_capitulos = client.open_by_key(ID_CAPITULOS).worksheet("Capitulos")

# --- LISTAS GLOBAIS ---
LISTA_TIPOS = ["NOVA", "CORREÇÃO", "UPGRADE"]
LISTA_MODULOS = ["SIMPLO", "ELETRICOS", "HIBRIDOS", "TRACTOR", "MOTOS"]
LISTA_MANUAIS = ["ABS/ASR/ESP", "CÂMBIO", "CÂMBIO TRUCK", "TABELA DE GÁS TRUCK", "TABELA DE GÁS", "CLIMA CAR", "CLIMA TRUCK", "CÓDIGO DE FALHAS", "ELECTRA", "ELECTRA TRUCK", "HIBRIDOS", "INJEÇÃO", "DIESEL", "ARLA", "LOCAR", "LOCAR TRUCK", "LUBRITEC", "MIX", "MIX - AIRBAG", "MIX - ALARMES", "MIX - IMOBILIZADOR", "MIX - RESETS", "MOTORES", "MOTORES - LINHA LEVE", "MOTORES - LINHA PESADA", "MT PRO", "PICO SCOPE", "REVISA CAR", "TABELA DE TORQUES DAS RODAS", "TORKS - DIREÇÃO", "TORKS TRUCK - DIREÇÃO", "TORKS - FREIOS", "TORKS TRUCK - FREIOS", "TORKS - SUSPENSÃO", "TORKS TRUCK - SUSPENSÃO", "TORKS TRUCK", "SCOPE TRUCK (MT PRO)", "SCOPE TRUCK (PICO SCOPE)", "SINCRO", "SINCRO - CORREIAS", "SINCRO - CORRENTES", "SINCRO - POLY-V", "MOTORES TRACTOR", "CLIMA TRACTOR", "SINCRO TRACTOR", "ELECTRA TRACTOR", "INJEÇÃO TRACTOR", "CÂMBIO TRACTOR", "MT PRO TRACTOR", "PICO SCOPE TRACTOR", "CODIGO DE FALHAS TRACTOR", "LUBRITEC MOTOS", "CODIGO DE FALHAS MOTOS", "INJEÇÃO MOTOS", "ELECTRA MOTOS", "ABS MOTOS", "MOTORES MOTOS", "ELETRICOS", "ELETRICOS - TORKS", "ELETRICOS - LUBRITEC", "ELETRICOS - REVISA", "ELETRICOS - LOCAR", "ELETRICOS - RESETS", "ELETRICOS - ABS", "ELETRICOS - AC", "ELETRICOS - INTERLOCK", "ELETRICOS - CÓDIGO DE FALHAS", "H&E - TORKS", "H&E - CÓDIGO DE FALHAS", "H&E - ELECTRA", "H&E - SINCRO", "H&E - LOCAR", "H&E - RESETS", "H&E - MT PRO", "H&E - ABS", "H&E - AC", "H&E - INTERLOCK", "H&E", "H&E - INJEÇÃO", "H&E - MOTORES", "H&E - LUBRITEC", "H&E - REVISA CAR"]
LISTA_MONTADORAS = ["  ", "AGRALE", "ALFA ROMEO", "AUDI", "BMW", "BYD", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DAEWOO", "DAF", "DAIHATSU", "DODGE", "DUCATI", "EFFA", "FIAT", "FORD", "FOTON", "GWM", "HARLEY DAVIDSON", "HONDA", "HUMMER", "HYUNDAI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC MOTORS", "JAECOO", "JAGUAR", "JEEP", "KAWASAKI", "KIA", "LAND ROVER", "LEXUS", "LIFAN", "MAN", "MASERATI", "MAZDA", "MERCEDES-BENZ TRUCK", "MERCEDES-BENZ", "MG MOTORS", "MINI", "MITSUBISHI", "NISSAN", "PEUGEOT", "PORSCHE", "RAM", "RENAULT", "SCANIA", "SEAT", "SMART", "SSANGYONG", "SUBARU", "SUZUKI", "TROLLER", "TOYOTA", "VOLVO", "VOLVO TRUCK", "VOLKSWAGEN", "VOLKSWAGEN TRUCK", "YAMAHA", "JOHN DEERE", "VALTRA", "MASSEY FERGUSON", "NEW HOLLAND", "MAXION-PERKINS", "CASE"]
LISTA_VERSOES = ["2024/1", "2024/2", "2024/3", "2025/1", "2025/2", "2025/3", "2026/1", "2026/2", "2026/3", "2027/1", "2027/2", "2027/3", "2024/1 T", "2024/2 T", "2024/3 T", "2025/1 T", "2025/2 T", "2025/3 T", "2026/1 T", "2026/2 T", "2026/3 T", "2027/1 T", "2027/2 T", "2027/3 T", "2024/1 H&E", "2024/2 H&E", "2024/3 H&E", "2025/1 H&E", "2025/2 H&E", "2025/3 H&E", "2026/1 H&E", "2026/2 H&E", "2026/3 H&E", "2027/1 H&E", "2027/2 H&E", "2027/3 H&E", "2024/1 M", "2024/2 M", "2024/3 M", "2025/1 M", "2025/2 M", "2025/3 M", "2026/1 M", "2026/2 M", "2026/3 M", "2027/1 M", "2027/2 M", "2027/3 M"]

# --- FUNÇÕES DE CARREGAMENTO ---
@st.cache_data(ttl=3600)
def carregar_dados_demandas():
    return pd.DataFrame(sheet_demandas.get_all_records())

@st.cache_data(ttl=3600)
def carregar_dados_modelos():
    return pd.DataFrame(sheet_modelos.get_all_records())

@st.cache_data(ttl=600)
def carregar_dados_capitulos():
    return pd.DataFrame(sheet_capitulos.get_all_records())