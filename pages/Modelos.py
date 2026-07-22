import streamlit as st
import pandas as pd
import io
import logging
import gspread
from datetime import datetime
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from config import (
    sheet_modelos, carregar_dados_modelos,
    LISTA_MODULOS, LISTA_MANUAIS, LISTA_MONTADORAS
)

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Gestão de Modelos", layout="wide")
st.title("📋 Controle de Modelos")

COLUNAS_ESPERADAS = ["MÓDULO", "MANUAL", "CAPITULO", "MONTADORA", "MODELO"]

# --- FUNÇÕES AUXILIARES ---
def get_selectbox_index(lista, valor, nome_campo):
    """Retorna o índice seguro para selectbox."""
    try:
        return lista.index(valor)
    except ValueError:
        st.warning(f"⚠️ '{valor}' não está na lista de {nome_campo}. Usando padrão.")
        logger.warning(f"Valor '{valor}' não encontrado em {nome_campo}")
        return 0


def validar_modelo(modulo, manual, capitulo, montadora, modelo):
    """Valida campos obrigatórios."""
    erros = []
    if not modelo.strip():
        erros.append("Modelo é obrigatório")
    if not capitulo.strip():
        erros.append("Capítulo é obrigatório")

    if erros:
        st.error("❌ Erros de validação:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True


def validar_dataframe_upload(df):
    """Valida DataFrame do upload."""
    erros = []

    # Verifica colunas
    colunas_faltando = [c for c in COLUNAS_ESPERADAS if c not in df.columns]
    if colunas_faltando:
        erros.append(f"Colunas faltando: {', '.join(colunas_faltando)}")

    # Verifica linhas vazias
    if not df.empty and df[COLUNAS_ESPERADAS].isnull().all(axis=1).any():
        erros.append("Há linhas completamente vazias")

    # Verifica campo MODELO obrigatório
    if not df.empty and (df["MODELO"].isnull().any() or (df["MODELO"].astype(str).str.strip

