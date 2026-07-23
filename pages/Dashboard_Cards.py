import streamlit as st
import pandas as pd
from config import carregar_dados_demandas

st.set_page_config(page_title="Dashboard Cards", layout="wide")
st.title("📊 Dashboard de Demandas")

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
col1, col2, col3 = st.columns([2, 1, 1])

with col1:
    st.subheader("🔍 Filtros")

with col2:
    montadoras = ["Todas"] + sorted(df_demandas["MONTADORA"].unique().tolist())
    montadora_selecionada = st.selectbox("Montadora", montadoras, key="montadora")

with col3:
    tipos = ["Todos"] + sorted(df_demandas["TIPO DEMANDA"].unique().tolist())
    tipo_selecionado = st.selectbox("Tipo", tipos, key="tipo")

# Aplicar filtros
df_filtered = df_demandas.copy()

if montadora_selecionada != "Todas":
    df_filtered = df_filtered[df_filtered["MONTADORA"] == montadora_selecionada]

if tipo_selecionado != "Todos":
    df_filtered = df_filtered[df_filtered["TIPO DEMANDA"] == tipo_selecionado]

# --- CSS CUSTOMIZADO ---
st.markdown("""
<style>
    .card {
        background-color: #f0f0f0;
        padding: 20px;
        border-radius: 10px;
        text-align: center;
        margin-bottom: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }

    .card-titulo {
        font-size: 14px;
        font-weight: bold;
        color: white;
        margin: 0;
        padding: 8px;
        border-radius: 5px 5px 0 0;
    }

    .card-valor {
        font-size: 36px;
        font-weight: bold;
        color: #333;
        margin: 15px 0;
    }

    .card-verde { background-color: #00AA44; }
    .card-vermelho { background-color: #DD0000; }
    .card-azul { background-color: #0066DD; }
    .card-preto { background-color: #333333; }
    .card-claro { background-color: #87CEEB; }
    .card-escuro { background-color: #4A90E2; }
</style>
""", unsafe_allow_html=True)

# --- KPIs PRINCIPAIS ---
st.divider()
st.subheader("📈 Resumo")

col1, col2, col3 = st.columns(3)

with col1:
    novas = len(df_filtered[df_filtered["TIPO DEMANDA"] == "NOVO"])
    st.markdown(f"""
    <div class="card">
        <div class="card-titulo card-verde">NOVAS DEMANDAS</div>
        <div class="card-valor">{novas}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    correcoes = len(df_filtered[df_filtered["TIPO DEMANDA"] == "CORREÇÃO"])
    st.markdown(f"""
    <div class="card">
        <div class="card-titulo card-vermelho">CORREÇÕES</div>
        <div class="card-valor">{correcoes}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    upgrades = len(df_filtered[df_filtered["TIPO DEMANDA"] == "MELHORIA"])
    st.markdown(f"""
    <div class="card">
        <div class="card-titulo card-azul">UPGRADES</div>
        <div class="card-valor">{upgrades}</div>
    </div>
    """, unsafe_allow_html=True)

# --- VERSÕES ---
st.divider()
st.subheader("📦 VERSÕES")

versoes = df_filtered["VERSÃO"].value_counts().sort_index()

cols = st.columns(1)

with cols[0]:
    for idx, (versao, quantidade) in enumerate(versoes.items()):
        cor_classe = "card-claro" if idx % 2 == 0 else "card-escuro"
        st.markdown(f"""
        <div class="card">
            <div style="
                background-color: #87CEEB if {idx % 2 == 0} else #4A90E2;
                padding: 12px;
                border-radius: 5px;
                display: flex;
                justify-content: space-between;
                align-items: center;
            ">
                <span style="color: white; font-weight: bold; font-size: 16px;">{versao}</span>
                <span style="color: white; font-weight: bold; font-size: 20px;">{quantidade}</span>
            </div>
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