import streamlit as st
import gspread
from oauth2client.service_account import ServiceAccountCredentials
import pandas as pd
import re
import logging

logger = logging.getLogger(__name__)

# --- IDs DAS PLANILHAS ---
ID_DEMANDAS = "10F1PqOSXUj_tbN7qrm9qXKnKJQ7xcHUmtIOB72FpWaM"
ID_MODELOS = "1fYwQ2uoqXY6QJm0Kk9dW2vX0tjgbSuTeFNfONe8UWMs"
ID_CAPITULOS = "1TN-tegne416QaqJQiTV9kr6f5AS332XkUMmv4_FsRaU"

# --- CONEXÃO ---
@st.cache_resource
def conectar_gsheets():
    """
    Autentica no Google Sheets usando credenciais do st.secrets.
    Encapsulado em try/except para tratamento de erros.
    """
    try:
        creds_dict = st.secrets["gcp_service_account"]
        creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, [
            'https://www.googleapis.com/auth/spreadsheets',
            'https://www.googleapis.com/auth/drive'
        ])
        client = gspread.authorize(creds)
        logger.info("Conexão com Google Sheets estabelecida com sucesso")
        return client
    except KeyError:
        st.error("❌ Credenciais do Google Sheets não encontradas em st.secrets")
        logger.error("Credenciais do Google Sheets não configuradas")
        st.stop()
    except Exception as e:
        st.error(f"❌ Não foi possível conectar ao Google Sheets: {e}")
        logger.error(f"Erro ao conectar ao Google Sheets: {e}", exc_info=True)
        st.stop()


client = conectar_gsheets()


def _abrir_planilha(id_planilha, worksheet_name=None, worksheet_index=0):
    """Abre uma worksheet com tratamento de erro."""
    try:
        arquivo = client.open_by_key(id_planilha)
        if worksheet_name:
            ws = arquivo.worksheet(worksheet_name)
        else:
            ws = arquivo.get_worksheet(worksheet_index)
        logger.info(f"Planilha aberta com sucesso: {id_planilha}")
        return ws
    except gspread.exceptions.SpreadsheetNotFound:
        st.error(f"❌ Planilha não encontrada (ID: {id_planilha})")
        logger.error(f"Planilha não encontrada: {id_planilha}")
        st.stop()
    except gspread.exceptions.WorksheetNotFound as e:
        st.error(f"❌ Worksheet não encontrada: {e}")
        logger.error(f"Worksheet não encontrada: {e}")
        st.stop()
    except Exception as e:
        st.error(f"❌ Erro ao abrir a planilha: {e}")
        logger.error(f"Erro ao abrir planilha {id_planilha}: {e}", exc_info=True)
        st.stop()


# --- CONEXÃO COM AS ABAS ---
sheet_demandas = _abrir_planilha(ID_DEMANDAS)
sheet_modelos = _abrir_planilha(ID_MODELOS)
sheet_capitulos = _abrir_planilha(ID_CAPITULOS, worksheet_name="Capitulos")

# --- LISTAS GLOBAIS (Corrigidas: sem &) ---
LISTA_TIPOS = ["NOVA", "CORREÇÃO", "UPGRADE"]
LISTA_MODULOS = ["SIMPLO", "ELETRICOS", "HIBRIDOS", "TRACTOR", "MOTOS"]
LISTA_MANUAIS = [
    "ABS/ASR/ESP", "CÂMBIO", "CÂMBIO TRUCK", "TABELA DE GÁS TRUCK", "TABELA DE GÁS",
    "CLIMA CAR", "CLIMA TRUCK", "CÓDIGO DE FALHAS", "ELECTRA", "ELECTRA TRUCK",
    "HIBRIDOS", "INJEÇÃO", "DIESEL", "ARLA", "LOCAR", "LOCAR TRUCK", "LUBRITEC",
    "MIX", "MIX - AIRBAG", "MIX - ALARMES", "MIX - IMOBILIZADOR", "MIX - RESETS",
    "MOTORES", "MOTORES - LINHA LEVE", "MOTORES - LINHA PESADA", "MT PRO",
    "PICO SCOPE", "REVISA CAR", "TABELA DE TORQUES DAS RODAS", "TORKS - DIREÇÃO",
    "TORKS TRUCK - DIREÇÃO", "TORKS - FREIOS", "TORKS TRUCK - FREIOS",
    "TORKS - SUSPENSÃO", "TORKS TRUCK - SUSPENSÃO", "TORKS TRUCK",
    "SCOPE TRUCK (MT PRO)", "SCOPE TRUCK (PICO SCOPE)", "SINCRO",
    "SINCRO - CORREIAS", "SINCRO - CORRENTES", "SINCRO - POLY-V",
    "MOTORES TRACTOR", "CLIMA TRACTOR", "SINCRO TRACTOR", "ELECTRA TRACTOR",
    "INJEÇÃO TRACTOR", "CÂMBIO TRACTOR", "MT PRO TRACTOR", "PICO SCOPE TRACTOR",
    "CODIGO DE FALHAS TRACTOR", "LUBRITEC MOTOS", "CODIGO DE FALHAS MOTOS",
    "INJEÇÃO MOTOS", "ELECTRA MOTOS", "ABS MOTOS", "MOTORES MOTOS", "ELETRICOS",
    "ELETRICOS - TORKS", "ELETRICOS - LUBRITEC", "ELETRICOS - REVISA",
    "ELETRICOS - LOCAR", "ELETRICOS - RESETS", "ELETRICOS - ABS", "ELETRICOS - AC",
    "ELETRICOS - INTERLOCK", "ELETRICOS - CÓDIGO DE FALHAS", "H&E - TORKS",
    "H&E - CÓDIGO DE FALHAS", "H&E - ELECTRA", "H&E - SINCRO", "H&E - LOCAR",
    "H&E - RESETS", "H&E - MT PRO", "H&E - ABS", "H&E - AC", "H&E - INTERLOCK",
    "H&E", "H&E - INJEÇÃO", "H&E - MOTORES", "H&E - LUBRITEC", "H&E - REVISA CAR", "TORKS"
]
LISTA_MONTADORAS = [
    "  ", "AGRALE", "ALFA ROMEO", "AUDI", "BMW", "BYD", "CHERY", "CHEVROLET",
    "CHRYSLER", "CITROEN", "DAEWOO", "DAF", "DAIHATSU", "DODGE", "DUCATI", "EFFA",
    "FIAT", "FORD", "FOTON", "GWM", "HARLEY DAVIDSON", "HONDA", "HUMMER", "HYUNDAI",
    "INTERNATIONAL", "ISUZU", "IVECO", "JAC MOTORS", "JAECOO", "JAGUAR", "JEEP",
    "KAWASAKI", "KIA", "LAND ROVER", "LEXUS", "LIFAN", "MAN", "MASERATI", "MAZDA",
    "MERCEDES-BENZ TRUCK", "MERCEDES-BENZ", "MG MOTORS", "MINI", "MITSUBISHI",
    "NISSAN", "PEUGEOT", "PORSCHE", "RAM", "RENAULT", "SCANIA", "SEAT", "SMART",
    "SSANGYONG", "SUBARU", "SUZUKI", "TROLLER", "TOYOTA", "VOLVO", "VOLVO TRUCK",
    "VOLKSWAGEN", "VOLKSWAGEN TRUCK", "YAMAHA", "JOHN DEERE", "VALTRA",
    "MASSEY FERGUSON", "NEW HOLLAND", "MAXION-PERKINS", "CASE"
]
LISTA_VERSOES = [
    "2024/1", "2024/2", "2024/3", "2025/1", "2025/2", "2025/3", "2026/1", "2026/2",
    "2026/3", "2027/1", "2027/2", "2027/3", "2024/1 T", "2024/2 T", "2024/3 T",
    "2025/1 T", "2025/2 T", "2025/3 T", "2026/1 T", "2026/2 T", "2026/3 T",
    "2027/1 T", "2027/2 T", "2027/3 T", "2024/1 H&E", "2024/2 H&E", "2024/3 H&E",
    "2025/1 H&E", "2025/2 H&E", "2025/3 H&E", "2026/1 H&E", "2026/2 H&E",
    "2026/3 H&E", "2027/1 H&E", "2027/2 H&E", "2027/3 H&E", "2024/1 M", "2024/2 M",
    "2024/3 M", "2025/1 M", "2025/2 M", "2025/3 M", "2026/1 M", "2026/2 M",
    "2026/3 M", "2027/1 M", "2027/2 M", "2027/3 M"
]

# --- FUNÇÕES DE CARREGAMENTO ---
def _carregar_com_row_id(sheet):
    """
    Carrega os dados da planilha preservando o número REAL da linha.
    Isso permite edição/exclusão precisa sem usar sheet.find().
    """
    try:
        valores = sheet.get_all_values()
        if not valores or len(valores) < 2:
            logger.warning(f"Planilha vazia ou com menos de 2 linhas")
            return pd.DataFrame()

        header, linhas = valores[0], valores[1:]
        df = pd.DataFrame(linhas, columns=header)
        df["_row"] = range(2, len(df) + 2)
        logger.info(f"Dados carregados: {len(df)} registros")
        return df
    except Exception as e:
        logger.error(f"Erro ao carregar dados com row_id: {e}", exc_info=True)
        return pd.DataFrame()


def _validar_colunas(df, colunas_esperadas, nome_sheet):
    """Valida se as colunas esperadas existem no DataFrame."""
    faltantes = set(colunas_esperadas) - set(df.columns)
    if faltantes:
        st.error(f"❌ Colunas faltando em {nome_sheet}: {', '.join(faltantes)}")
        logger.error(f"Colunas faltando em {nome_sheet}: {faltantes}")
        st.stop()
    return df


@st.cache_data(ttl=3600)
def carregar_dados_demandas():
    """Carrega dados de demandas com validação."""
    df = _carregar_com_row_id(sheet_demandas)
    if not df.empty:
        colunas_esperadas = ["DEMANDA", "TIPO DEMANDA", "MÓDULO", "MANUAL", "DATA LINKAGEM", "CAPITULO", "MONTADORA", "VERSÃO"]
        df = _validar_colunas(df, colunas_esperadas, "Demandas")
    return df


@st.cache_data(ttl=3600)
def carregar_dados_modelos():
    """Carrega dados de modelos com validação."""
    df = _carregar_com_row_id(sheet_modelos)
    if not df.empty:
        colunas_esperadas = ["MÓDULO", "MANUAL", "CAPITULO", "MONTADORA", "MODELO"]
        df = _validar_colunas(df, colunas_esperadas, "Modelos")
    return df


@st.cache_data(ttl=600)
def carregar_dados_capitulos():
    """Carrega dados de capítulos com validação."""
    df = _carregar_com_row_id(sheet_capitulos)
    if not df.empty:
        colunas_esperadas = ["MANUAL", "CAPITULO", "USADO NA DEMANDA"]
        df = _validar_colunas(df, colunas_esperadas, "Capítulos")
    return df


@st.cache_data(ttl=3600)
def carregar_maiores_capitulos():
    """Carrega os maiores capítulos por manual."""
    try:
        df = carregar_dados_demandas()
        if df.empty or "CAPITULO" not in df.columns or "MANUAL" not in df.columns:
            return pd.DataFrame(columns=["MANUAL", "CAPITULO", "CAP_NUM"])

        def extrair_numero(valor):
            """Extrai a parte numérica inicial de um capítulo."""
            valor_str = str(valor).strip()
            match = re.match(r"(\d+)", valor_str)
            if match:
                return int(match.group(1))
            logger.warning(f"Capítulo com formato inválido: '{valor_str}'")
            return 0

        df = df.copy()
        df['CAP_NUM'] = df['CAPITULO'].apply(extrair_numero)

        idx_maximos = df.groupby('MANUAL')['CAP_NUM'].idxmax()
        maiores = df.loc[idx_maximos, ['MANUAL', 'CAPITULO', 'CAP_NUM']]

        return maiores
    except Exception as e:
        logger.error(f"Erro ao carregar maiores capítulos: {e}", exc_info=True)
        return pd.DataFrame(columns=["MANUAL", "CAPITULO", "CAP_NUM"])


def invalidar_cache():
    """Invalida o cache manualmente após edições."""
    st.cache_data.clear()
    logger.info("Cache invalidado manualmente")