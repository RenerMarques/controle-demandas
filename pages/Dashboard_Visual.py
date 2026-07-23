import streamlit as st
import pandas as pd
from config import carregar_dados_demandas

st.set_page_config(page_title="Dashboard Visual", layout="wide")
st.title("📊 Dashboard Visual")

# --- CARREGAR DADOS ---
try:
    df_demandas = carregar_dados_demandas()
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.stop()

if df_demandas.empty:
    st.warning("⚠️ Nenhuma demanda cadastrada.")
    st.stop()

# --- FILTRO DE MONTADORA ---
st.subheader("🔍 Selecione a Montadora")
montadoras = ["Todas"] + sorted(df_demandas["MONTADORA"].unique().tolist())
montadora_selecionada = st.selectbox("Montadora", montadoras, key="montadora_visual")

# Aplicar filtro
if montadora_selecionada != "Todas":
    df_filtered = df_demandas[df_demandas["MONTADORA"] == montadora_selecionada]
else:
    df_filtered = df_demandas.copy()

# --- FUNÇÃO PARA CRIAR CARD ---
def criar_card(titulo, valor, cor_bg, cor_texto="white"):
    """Cria um card colorido"""
    st.markdown(
        f"""
        <div style="
            background-color: {cor_bg};
            padding: 20px;
            border-radius: 10px;
            text-align: center;
            margin-bottom: 10px;
        ">
            <h3 style="color: {cor_texto}; margin: 0; font-size: 18px;">{titulo}</h3>
            <h1 style="color: {cor_texto}; margin: 10px 0 0 0; font-size: 48px;">{valor}</h1>
        </div>
        """,
        unsafe_allow_html=True
    )

# --- KPIs PRINCIPAIS ---
st.divider()
st.subheader("📈 KPIs Principais")

col1, col2, col3 = st.columns(3)

with col1:
    novas = len(df_filtered[df_filtered["TIPO DEMANDA"] == "NOVO"])
    criar_card("NOVAS DEMANDAS", novas, "#00AA44", "white")

with col2:
    correcoes = len(df_filtered[df_filtered["TIPO DEMANDA"] == "CORREÇÃO"])
    criar_card("CORREÇÕES", correcoes, "#DD0000", "white")

with col3:
    upgrades = len(df_filtered[df_filtered["TIPO DEMANDA"] == "MELHORIA"])
    criar_card("UPGRADES", upgrades, "#0066DD", "white")

# --- VERSÕES ---
st.divider()
st.subheader("📦 VERSÕES")

versoes = df_filtered["VERSÃO"].value_counts().sort_index()

# Cores alternadas para as versões
cores_versoes = ["#87CEEB", "#4A90E2"]  # Azul claro e azul escuro

for idx, (versao, quantidade) in enumerate(versoes.items()):
    cor = cores_versoes[idx % 2]
    criar_card(versao, quantidade, cor, "white")

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