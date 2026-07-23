import streamlit as st
import pandas as pd
from config import carregar_dados_demandas

st.set_page_config(page_title="Dashboard Visual", layout="wide")
st.title("📊 Dashboard Visual")

# --- CARREGAR DADOS ---
try:
    df_demandas = carregar_dados_demandas()

    # Limpar e padronizar a coluna TIPO DEMANDA
    df_demandas["TIPO DEMANDA"] = df_demandas["TIPO DEMANDA"].str.strip().str.upper()

except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.stop()

if df_demandas.empty:
    st.warning("⚠️ Nenhuma demanda cadastrada.")
    st.stop()

# --- FILTRO DE VERSÃO ---
col1, col2 = st.columns([3, 1])

with col1:
    st.subheader("🔍 Filtro")

with col2:
    versoes = ["Todas"] + sorted(df_demandas["VERSÃO"].unique().tolist())
    versao_selecionada = st.selectbox("Versão", versoes, key="versao")

# Aplicar filtro
if versao_selecionada != "Todas":
    df_filtered = df_demandas[df_demandas["VERSÃO"] == versao_selecionada]
else:
    df_filtered = df_demandas.copy()

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .card-kpi {
        padding: 20px;
        border-radius: 0px;
        text-align: center;
        margin-bottom: 15px;
        color: white;
        font-weight: bold;
    }

    .card-kpi-titulo {
        font-size: 14px;
        margin-bottom: 10px;
        letter-spacing: 1px;
    }

    .card-kpi-valor {
        font-size: 42px;
        font-weight: bold;
    }

    .card-verde { background-color: #00AA44; }
    .card-vermelho { background-color: #DD0000; }
    .card-azul { background-color: #0066DD; }

    .card-versao {
        padding: 12px 15px;
        border-radius: 0px;
        margin-bottom: 8px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        color: white;
        font-weight: bold;
        font-size: 13px;
        border-left: 5px solid;
    }

    .versao-claro { 
        background-color: #87CEEB;
        border-left-color: #0066DD;
    }

    .versao-escuro { 
        background-color: #4A90E2;
        border-left-color: #0044AA;
    }

    .card-versoes-titulo {
        padding: 12px 15px;
        background-color: #333333;
        color: white;
        font-weight: bold;
        font-size: 13px;
        margin-bottom: 8px;
        border-radius: 0px;
        letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- KPIs PRINCIPAIS ---
st.divider()

col1, col2, col3 = st.columns(3)

with col1:
    novas = len(df_filtered[df_filtered["TIPO DEMANDA"] == "NOVO"])
    st.markdown(f"""
    <div class="card-kpi card-verde">
        <div class="card-kpi-titulo">NOVAS DEMANDAS</div>
        <div class="card-kpi-valor">{novas}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    correcoes = len(df_filtered[df_filtered["TIPO DEMANDA"] == "CORREÇÃO"])
    st.markdown(f"""
    <div class="card-kpi card-vermelho">
        <div class="card-kpi-titulo">CORREÇÕES</div>
        <div class="card-kpi-valor">{correcoes}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    upgrades = len(df_filtered[df_filtered["TIPO DEMANDA"] == "MELHORIA"])
    st.markdown(f"""
    <div class="card-kpi card-azul">
        <div class="card-kpi-titulo">UPGRADES</div>
        <div class="card-kpi-valor">{upgrades}</div>
    </div>
    """, unsafe_allow_html=True)

# --- VERSÕES ---
st.divider()

# Título de Versões
st.markdown("""
<div class="card-versoes-titulo">VERSÕES</div>
""", unsafe_allow_html=True)

versoes = df_demandas["VERSÃO"].value_counts().sort_index()

# Cores alternadas para as versões
for idx, (versao, quantidade) in enumerate(versoes.items()):
    classe = 'versao-claro' if idx % 2 == 0 else 'versao-escuro'
    st.markdown(f"""
    <div class="card-versao {classe}">
        <span>{versao}</span>
        <span>{quantidade}</span>
    </div>
    """, unsafe_allow_html=True)

# --- TABELA DETALHADA ---
st.divider()
st.subheader("📋 Detalhes das Demandas")

col1, col2 = st.columns([3, 1])

with col1:
    busca = st.text_input("🔍 Buscar demandas").strip().lower()

with col2:
    limite = st.number_input("Linhas a exibir", min_value=5, max_value=100, value=20)

# Aplicar busca
if busca:
    colunas_busca = [c for c in df_filtered.columns if c != "_row"]
    df_display = df_filtered[
        df_filtered[colunas_busca].astype(str)
        .apply(lambda x: x.str.contains(busca, case=False, regex=False, na=False))
        .any(axis=1)
    ]
else:
    df_display = df_filtered

# Exibir tabela
colunas_visiveis = [c for c in df_display.columns if c != "_row"]
st.dataframe(
    df_display[colunas_visiveis].head(limite),
    use_container_width=True,
    hide_index=True
)

st.write(f"**Total de registros exibidos:** {min(limite, len(df_display))} de {len(df_display)}")