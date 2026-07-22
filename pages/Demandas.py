import streamlit as st
import pandas as pd
from datetime import datetime
import io
import logging
import gspread
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from config import (
    sheet_demandas, carregar_dados_demandas,
    LISTA_TIPOS, LISTA_MODULOS, LISTA_MANUAIS,
    LISTA_MONTADORAS, LISTA_VERSOES
)

logger = logging.getLogger(__name__)
st.set_page_config(page_title="Controle de Demandas", layout="wide")
st.title("📋 Controle de Demandas")

# --- FUNÇÕES AUXILIARES ---
def parse_data(data_str):
    """Parse data em múltiplos formatos."""
    if not data_str or pd.isna(data_str):
        return datetime.now().date()

    data_str = str(data_str).strip()
    formatos = ['%d/%m/%Y', '%Y-%m-%d', '%d/%m/%y']

    for fmt in formatos:
        try:
            return datetime.strptime(data_str, fmt).date()
        except ValueError:
            continue

    st.warning(f"⚠️ Não consegui interpretar a data: '{data_str}'")
    logger.warning(f"Data inválida: '{data_str}'")
    return datetime.now().date()


def formatar_data(data_obj):
    """Formata data para DD/MM/YYYY."""
    if isinstance(data_obj, str):
        data_obj = parse_data(data_obj)
    return data_obj.strftime("%d/%m/%Y") if data_obj else ""


def get_selectbox_index(lista, valor, nome_campo):
    """Retorna o índice seguro para selectbox."""
    try:
        return lista.index(valor)
    except ValueError:
        st.warning(f"⚠️ '{valor}' não está na lista de {nome_campo}. Usando padrão.")
        logger.warning(f"Valor '{valor}' não encontrado em {nome_campo}")
        return 0


def validar_demanda(demanda, tipo, modulo, manual, capitulo, montadora, versao):
    """Valida campos obrigatórios."""
    erros = []
    if not demanda.strip():
        erros.append("Demanda é obrigatória")
    if not capitulo.strip():
        erros.append("Capítulo é obrigatório")

    if erros:
        st.error("❌ Erros de validação:\n" + "\n".join(f"• {e}" for e in erros))
        return False
    return True


def gerar_pdf_demandas(df):
    """Gera PDF formatado com tabela de demandas."""
    buffer = io.Bytes

