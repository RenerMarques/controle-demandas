import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re

# --- IDs DAS PLANILHAS ---
ID_DEMANDAS = "10F1PqOSXUj_tbN7qrm9qXKnKJQ7xcHUmtIOB72FpWaM"
ID_MODELOS = "1fYwQ2uoqXY6QJm0Kk9dW2vX0tjgbSuTeFNfONe8UWMs"
ID_CAPITULOS = "1TN-tegne416QaqJQiTV9kr6f5AS332XkUMmv4_FsRaU"  # <--- COLOQUE O ID DA PLANILHA DE CAPITULOS AQUI


# --- CONEXÃO ---
@st.cache_resource
def conectar_gsheets():
    """
    Autentica no Google Sheets. Encapsulado em try/except porque isso roda
    no import de config.py (ou seja, em toda página) — se a credencial
    falhar ou a API estiver instável, é melhor mostrar uma mensagem clara
    e parar a execução do que deixar o app quebrar com traceback cru.
    """
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        return gspread.authorize(creds)
    except Exception as e:
        st.error(f"Não foi possível conectar ao Google Sheets: {e}")
        st.stop()


client = conectar_gsheets()


def _abrir_planilha(id_planilha, worksheet_name=None, worksheet_index=0):
    """Abre uma worksheet com tratamento de erro (ID errado, sem permissão, etc.)."""
    try:
        arquivo = client.open_by_key(id_planilha)
        if worksheet_name:
            return arquivo.worksheet(worksheet_name)
        return arquivo.get_worksheet(worksheet_index)
    except Exception as e:
        st.error(f"Erro ao abrir a planilha ({id_planilha}): {e}")
        st.stop()


# --- CONEXÃO COM AS ABAS ---
sheet_demandas = _abrir_planilha(ID_DEMANDAS)
sheet_modelos = _abrir_planilha(ID_MODELOS)
sheet_capitulos = _abrir_planilha(ID_CAPITULOS, worksheet_name="Capitulos")

# --- LISTAS GLOBAIS (inalteradas) ---
LISTA_TIPOS = ["NOVA", "CORREÇÃO", "UPGRADE"]
LISTA_MODULOS = ["SIMPLO", "ELETRICOS", "HIBRIDOS", "TRACTOR", "MOTOS"]
LISTA_MANUAIS = ["ABS/ASR/ESP", "CÂMBIO", "CÂMBIO TRUCK", "TABELA DE GÁS TRUCK", "TABELA DE GÁS", "CLIMA CAR", "CLIMA TRUCK", "CÓDIGO DE FALHAS", "ELECTRA", "ELECTRA TRUCK", "HIBRIDOS", "INJEÇÃO", "DIESEL", "ARLA", "LOCAR", "LOCAR TRUCK", "LUBRITEC", "MIX", "MIX - AIRBAG", "MIX - ALARMES", "MIX - IMOBILIZADOR", "MIX - RESETS", "MOTORES", "MOTORES - LINHA LEVE", "MOTORES - LINHA PESADA", "MT PRO", "PICO SCOPE", "REVISA CAR", "TABELA DE TORQUES DAS RODAS", "TORKS - DIREÇÃO", "TORKS TRUCK - DIREÇÃO", "TORKS - FREIOS", "TORKS TRUCK - FREIOS", "TORKS - SUSPENSÃO", "TORKS TRUCK - SUSPENSÃO", "TORKS TRUCK", "SCOPE TRUCK (MT PRO)", "SCOPE TRUCK (PICO SCOPE)", "SINCRO", "SINCRO - CORREIAS", "SINCRO - CORRENTES", "SINCRO - POLY-V", "MOTORES TRACTOR", "CLIMA TRACTOR", "SINCRO TRACTOR", "ELECTRA TRACTOR", "INJEÇÃO TRACTOR", "CÂMBIO TRACTOR", "MT PRO TRACTOR", "PICO SCOPE TRACTOR", "CODIGO DE FALHAS TRACTOR", "LUBRITEC MOTOS", "CODIGO DE FALHAS MOTOS", "INJEÇÃO MOTOS", "ELECTRA MOTOS", "ABS MOTOS", "MOTORES MOTOS", "ELETRICOS", "ELETRICOS - TORKS", "ELETRICOS - LUBRITEC", "ELETRICOS - REVISA", "ELETRICOS - LOCAR", "ELETRICOS - RESETS", "ELETRICOS - ABS", "ELETRICOS - AC", "ELETRICOS - INTERLOCK", "ELETRICOS - CÓDIGO DE FALHAS", "H&E - TORKS", "H&E - CÓDIGO DE FALHAS", "H&E - ELECTRA", "H&E - SINCRO", "H&E - LOCAR", "H&E - RESETS", "H&E - MT PRO", "H&E - ABS", "H&E - AC", "H&E - INTERLOCK", "H&E", "H&E - INJEÇÃO", "H&E - MOTORES", "H&E - LUBRITEC", "H&E - REVISA CAR", "TORKS"]
LISTA_MONTADORAS = ["  ", "AGRALE", "ALFA ROMEO", "AUDI", "BMW", "BYD", "CHERY", "CHEVROLET", "CHRYSLER", "CITROEN", "DAEWOO", "DAF", "DAIHATSU", "DODGE", "DUCATI", "EFFA", "FIAT", "FORD", "FOTON", "GWM", "HARLEY DAVIDSON", "HONDA", "HUMMER", "HYUNDAI", "INTERNATIONAL", "ISUZU", "IVECO", "JAC MOTORS", "JAECOO", "JAGUAR", "JEEP", "KAWASAKI", "KIA", "LAND ROVER", "LEXUS", "LIFAN", "MAN", "MASERATI", "MAZDA", "MERCEDES-BENZ TRUCK", "MERCEDES-BENZ", "MG MOTORS", "MINI", "MITSUBISHI", "NISSAN", "PEUGEOT", "PORSCHE", "RAM", "RENAULT", "SCANIA", "SEAT", "SMART", "SSANGYONG", "SUBARU", "SUZUKI", "TROLLER", "TOYOTA", "VOLVO", "VOLVO TRUCK", "VOLKSWAGEN", "VOLKSWAGEN TRUCK", "YAMAHA", "JOHN DEERE", "VALTRA", "MASSEY FERGUSON", "NEW HOLLAND", "MAXION-PERKINS", "CASE"]
LISTA_VERSOES = ["2024/1", "2024/2", "2024/3", "2025/1", "2025/2", "2025/3", "2026/1", "2026/2", "2026/3", "2027/1", "2027/2", "2027/3", "2024/1 T", "2024/2 T", "2024/3 T", "2025/1 T", "2025/2 T", "2025/3 T", "2026/1 T", "2026/2 T", "2026/3 T", "2027/1 T", "2027/2 T", "2027/3 T", "2024/1 H&E", "2024/2 H&E", "2024/3 H&E", "2025/1 H&E", "2025/2 H&E", "2025/3 H&E", "2026/1 H&E", "2026/2 H&E", "2026/3 H&E", "2027/1 H&E", "2027/2 H&E", "2027/3 H&E", "2024/1 M", "2024/2 M", "2024/3 M", "2025/1 M", "2025/2 M", "2025/3 M", "2026/1 M", "2026/2 M", "2026/3 M", "2027/1 M", "2027/2 M", "2027/3 M"]


# --- FUNÇÕES DE CARREGAMENTO ---
def _carregar_com_row_id(sheet):
    """
    Carrega os dados da planilha preservando o número REAL da linha na
    planilha (coluna '_row'). Isso é o que permite que as páginas de
    edição/exclusão localizem um registro com precisão, em vez de usar
    sheet.find(texto) (que pega a primeira ocorrência de um valor
    duplicado) ou um índice posicional recalculado depois de já ter
    passado tempo desde o carregamento.

    Uso nas páginas, por exemplo em vez de:
        cell = sheet_capitulos.find(cap_sel)
        sheet_capitulos.update(range_name=f"A{cell.row}:C{cell.row}", ...)
    passa a ser:
        linha_alvo = dados["_row"]  # já vem no registro selecionado
        sheet_capitulos.update(range_name=f"A{linha_alvo}:C{linha_alvo}", ...)
    """
    valores = sheet.get_all_values()
    if not valores or len(valores) < 2:
        return pd.DataFrame()
    header, linhas = valores[0], valores[1:]
    df = pd.DataFrame(linhas, columns=header)
    df["_row"] = range(2, len(df) + 2)  # linha 1 da planilha é o cabeçalho
    return df


@st.cache_data(ttl=3600)
def carregar_dados_demandas():
    return _carregar_com_row_id(sheet_demandas)


@st.cache_data(ttl=3600)
def carregar_dados_modelos():
    return _carregar_com_row_id(sheet_modelos)


@st.cache_data(ttl=600)
def carregar_dados_capitulos():
    return _carregar_com_row_id(sheet_capitulos)


@st.cache_data(ttl=3600)
def carregar_maiores_capitulos():
    df = carregar_dados_demandas()
    if df.empty or "CAPITULO" not in df.columns or "MANUAL" not in df.columns:
        return pd.DataFrame(columns=["MANUAL", "CAPITULO", "CAP_NUM"])

    # Função para extrair apenas a parte numérica inicial (ex: "53A" vira 53)
    def extrair_numero(valor):
        valor_str = str(valor)
        match = re.match(r"(\d+)", valor_str)
        return int(match.group(1)) if match else 0

    df = df.copy()
    df['CAP_NUM'] = df['CAPITULO'].apply(extrair_numero)

    # Agrupamos pelo manual e pegamos o índice da linha que tem o maior CAP_NUM
    idx_maximos = df.groupby('MANUAL')['CAP_NUM'].idxmax()
    maiores = df.loc[idx_maximos, ['MANUAL', 'CAPITULO', 'CAP_NUM']]

    return maiores