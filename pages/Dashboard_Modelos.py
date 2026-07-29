import streamlit as st
from config import carregar_dados_modelos

st.set_page_config(page_title="Dashboard de Modelos", layout="wide")
st.title("🔧 Dashboard de Modelos")
st.caption("Visão consolidada dos modelos cadastrados por módulo, manual e montadora")

# --- CARREGAR DADOS ---
try:
    df_modelos = carregar_dados_modelos()
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    st.stop()

if df_modelos.empty:
    st.warning("⚠️ Nenhum modelo cadastrado.")
    st.stop()

# --- FILTRO ---
col1, col2 = st.columns([3, 1])
with col1:
    st.subheader("🔍 Filtro")
with col2:
    modulos = ["Todos"] + sorted(df_modelos["MÓDULO"].unique().tolist())
    modulo_selecionado = st.selectbox("Módulo", modulos, key="modulo_dash_modelos")

df_filtered = df_modelos if modulo_selecionado == "Todos" else df_modelos[df_modelos["MÓDULO"] == modulo_selecionado]

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
    .card-kpi-titulo { font-size: 14px; margin-bottom: 10px; letter-spacing: 1px; }
    .card-kpi-valor { font-size: 42px; font-weight: bold; }
    .card-verde { background-color: #00AA44; }
    .card-vermelho { background-color: #DD0000; }
    .card-azul { background-color: #0066DD; }
    .card-versao {
        padding: 12px 15px; border-radius: 0px; margin-bottom: 8px;
        display: flex; justify-content: space-between; align-items: center;
        color: white; font-weight: bold; font-size: 13px; border-left: 5px solid;
    }
    .versao-claro { background-color: #87CEEB; border-left-color: #0066DD; }
    .versao-escuro { background-color: #4A90E2; border-left-color: #0044AA; }
    .card-versoes-titulo {
        padding: 12px 15px; background-color: #333333; color: white;
        font-weight: bold; font-size: 13px; margin-bottom: 8px;
        border-radius: 0px; letter-spacing: 1px;
    }
</style>
""", unsafe_allow_html=True)

# --- KPIs PRINCIPAIS ---
st.divider()
col1, col2, col3 = st.columns(3)

with col1:
    st.markdown(f"""
    <div class="card-kpi card-verde">
        <div class="card-kpi-titulo">TOTAL DE MODELOS</div>
        <div class="card-kpi-valor">{len(df_filtered)}</div>
    </div>
    """, unsafe_allow_html=True)

with col2:
    st.markdown(f"""
    <div class="card-kpi card-azul">
        <div class="card-kpi-titulo">MANUAIS ÚNICOS</div>
        <div class="card-kpi-valor">{df_filtered["MANUAL"].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

with col3:
    st.markdown(f"""
    <div class="card-kpi card-vermelho">
        <div class="card-kpi-titulo">MONTADORAS ÚNICAS</div>
        <div class="card-kpi-valor">{df_filtered["MONTADORA"].nunique()}</div>
    </div>
    """, unsafe_allow_html=True)

# --- MODELOS POR MANUAL ---
st.divider()
st.markdown('<div class="card-versoes-titulo">TOP 15 MANUAIS COM MAIS MODELOS</div>', unsafe_allow_html=True)

por_manual = df_filtered["MANUAL"].value_counts().head(15)

for idx, (manual, quantidade) in enumerate(por_manual.items()):
    classe = 'versao-claro' if idx % 2 == 0 else 'versao-escuro'
    st.markdown(f"""
    <div class="card-versao {classe}">
        <span>{manual}</span>
        <span>{quantidade}</span>
    </div>
    """, unsafe_allow_html=True)

# --- TABELA DETALHADA ---
st.divider()
st.subheader("📋 Detalhes dos Modelos")

col1, col2 = st.columns([3, 1])
with col1:
    busca = st.text_input("🔍 Buscar modelos").strip().lower()
with col2:
    limite = st.number_input("Linhas a exibir", min_value=5, max_value=100, value=20)

if busca:
    colunas_busca = [c for c in df_filtered.columns if c != "_row"]
    df_display = df_filtered[
        df_filtered[colunas_busca].astype(str)
        .apply(lambda x: x.str.contains(busca, case=False, regex=False, na=False))
        .any(axis=1)
    ]
else:
    df_display = df_filtered

colunas_visiveis = [c for c in df_display.columns if c != "_row"]
st.dataframe(df_display[colunas_visiveis].head(limite), use_container_width=True, hide_index=True)
st.write(f"**Total de registros exibidos:** {min(limite, len(df_display))} de {len(df_display)}")