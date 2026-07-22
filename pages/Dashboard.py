import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import logging
from config import carregar_dados_demandas, carregar_dados_modelos, carregar_dados_capitulos

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Dashboard Analítico", layout="wide")
st.title("📊 Dashboard Analítico")
st.markdown("Análise completa de demandas, modelos e capítulos")

# --- CARREGAR DADOS ---
try:
    df_demandas = carregar_dados_demandas()
    df_modelos = carregar_dados_modelos()
    df_capitulos = carregar_dados_capitulos()
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    logger.error(f"Erro ao carregar dados para dashboard: {e}", exc_info=True)
    st.stop()

if df_demandas.empty:
    st.warning("⚠️ Nenhuma demanda cadastrada. Dashboard indisponível.")
    st.stop()

# --- FILTROS GLOBAIS ---
st.subheader("🔍 Filtros Globais")
col1, col2, col3, col4 = st.columns(4)

with col1:
    versoes = ["Todas"] + sorted(df_demandas["VERSÃO"].unique().tolist())
    versao_selecionada = st.selectbox("Versão", versoes)

with col2:
    modulos = ["Todos"] + sorted(df_demandas["MÓDULO"].unique().tolist())
    modulo_selecionado = st.selectbox("Módulo", modulos)

with col3:
    tipos = ["Todos"] + sorted(df_demandas["TIPO DEMANDA"].unique().tolist())
    tipo_selecionado = st.selectbox("Tipo", tipos)

with col4:
    montadoras = ["Todas"] + sorted(df_demandas["MONTADORA"].unique().tolist())
    montadora_selecionada = st.selectbox("Montadora", montadoras)

# --- APLICAR FILTROS ---
df_filtered = df_demandas.copy()

if versao_selecionada != "Todas":
    df_filtered = df_filtered[df_filtered["VERSÃO"] == versao_selecionada]

if modulo_selecionado != "Todos":
    df_filtered = df_filtered[df_filtered["MÓDULO"] == modulo_selecionado]

if tipo_selecionado != "Todos":
    df_filtered = df_filtered[df_filtered["TIPO DEMANDA"] == tipo_selecionado]

if montadora_selecionada != "Todas":
    df_filtered = df_filtered[df_filtered["MONTADORA"] == montadora_selecionada]

# --- KPIs PRINCIPAIS ---
st.divider()
st.subheader("📈 KPIs Principais")

col1, col2, col3, col4, col5 = st.columns(5)

with col1:
    st.metric(
        "Total de Demandas",
        len(df_filtered),
        delta=len(df_filtered) - len(df_demandas) if len(df_filtered) != len(df_demandas) else 0
    )

with col2:
    total_modelos = len(df_modelos)
    st.metric("Total de Modelos", total_modelos)

with col3:
    total_capitulos = len(df_capitulos)
    st.metric("Total de Capítulos", total_capitulos)

with col4:
    manuais_unicos = df_filtered["MANUAL"].nunique()
    st.metric("Manuais Únicos", manuais_unicos)

with col5:
    montadoras_unicas = df_filtered["MONTADORA"].nunique()
    st.metric("Montadoras Únicas", montadoras_unicas)

# --- GRÁFICOS LINHA 1 ---
st.divider()
st.subheader("📊 Análise por Versão")

col1, col2 = st.columns(2)

with col1:
    # Demandas por Versão
    demandas_por_versao = df_filtered["VERSÃO"].value_counts().sort_index()
    fig_versao = px.bar(
        x=demandas_por_versao.index,
        y=demandas_por_versao.values,
        labels={"x": "Versão", "y": "Quantidade"},
        title="Demandas por Versão",
        color=demandas_por_versao.values,
        color_continuous_scale="Viridis"
    )
    fig_versao.update_layout(showlegend=False, hovermode='x unified')
    st.plotly_chart(fig_versao, use_container_width=True)

with col2:
    # Tipo de Demanda por Versão
    tipo_versao = pd.crosstab(df_filtered["VERSÃO"], df_filtered["TIPO DEMANDA"])
    fig_tipo_versao = px.bar(
        tipo_versao,
        title="Tipo de Demanda por Versão",
        barmode="stack",
        labels={"value": "Quantidade", "index": "Versão"}
    )
    st.plotly_chart(fig_tipo_versao, use_container_width=True)

# --- GRÁFICOS LINHA 2 ---
st.divider()
st.subheader("🔧 Análise por Módulo")

col1, col2 = st.columns(2)

with col1:
    # Demandas por Módulo
    demandas_por_modulo = df_filtered["MÓDULO"].value_counts()
    fig_modulo = px.pie(
        values=demandas_por_modulo.values,
        names=demandas_por_modulo.index,
        title="Distribuição de Demandas por Módulo",
        hole=0.3
    )
    st.plotly_chart(fig_modulo, use_container_width=True)

with col2:
    # Modelos por Módulo
    modelos_por_modulo = df_modelos["MÓDULO"].value_counts()
    fig_modelos_modulo = px.bar(
        x=modelos_por_modulo.index,
        y=modelos_por_modulo.values,
        labels={"x": "Módulo", "y": "Quantidade"},
        title="Modelos por Módulo",
        color=modelos_por_modulo.values,
        color_continuous_scale="Blues"
    )
    fig_modelos_modulo.update_layout(showlegend=False)
    st.plotly_chart(fig_modelos_modulo, use_container_width=True)

# --- GRÁFICOS LINHA 3 ---
st.divider()
st.subheader("📚 Análise de Manuais")

col1, col2 = st.columns(2)

with col1:
    # Top 10 Manuais mais usados
    top_manuais = df_filtered["MANUAL"].value_counts().head(10)
    fig_manuais = px.barh(
        x=top_manuais.values,
        y=top_manuais.index,
        labels={"x": "Quantidade", "y": "Manual"},
        title="Top 10 Manuais Mais Usados",
        color=top_manuais.values,
        color_continuous_scale="Greens"
    )
    fig_manuais.update_layout(showlegend=False)
    st.plotly_chart(fig_manuais, use_container_width=True)

with col2:
    # Capítulos por Manual
    capitulos_por_manual = df_filtered["MANUAL"].value_counts().head(10)
    fig_cap_manual = px.bar(
        x=capitulos_por_manual.index,
        y=capitulos_por_manual.values,
        labels={"x": "Manual", "y": "Capítulos"},
        title="Capítulos por Manual (Top 10)",
        color=capitulos_por_manual.values,
        color_continuous_scale="Oranges"
    )
    fig_cap_manual.update_layout(xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_cap_manual, use_container_width=True)

# --- GRÁFICOS LINHA 4 ---
st.divider()
st.subheader("🏭 Análise de Montadoras")

col1, col2 = st.columns(2)

with col1:
    # Top Montadoras
    top_montadoras = df_filtered["MONTADORA"].value_counts().head(10)
    fig_montadoras = px.bar(
        x=top_montadoras.index,
        y=top_montadoras.values,
        labels={"x": "Montadora", "y": "Quantidade"},
        title="Top 10 Montadoras",
        color=top_montadoras.values,
        color_continuous_scale="Reds"
    )
    fig_montadoras.update_layout(xaxis_tickangle=-45, showlegend=False)
    st.plotly_chart(fig_montadoras, use_container_width=True)

with col2:
    # Heatmap: Módulo vs Montadora
    heatmap_data = pd.crosstab(df_filtered["MÓDULO"], df_filtered["MONTADORA"])
    fig_heatmap = px.imshow(
        heatmap_data,
        labels=dict(x="Montadora", y="Módulo", color="Quantidade"),
        title="Heatmap: Módulo vs Montadora",
        color_continuous_scale="YlOrRd"
    )
    st.plotly_chart(fig_heatmap, use_container_width=True)

# --- ANÁLISE TEMPORAL ---
st.divider()
st.subheader("📅 Análise Temporal")

# Converter data para datetime
try:
    df_filtered_temp = df_filtered.copy()
    df_filtered_temp["DATA_LINKAGEM"] = pd.to_datetime(
        df_filtered_temp["DATA LINKAGEM"],
        format="%d/%m/%Y",
        errors="coerce"
    )
    df_filtered_temp = df_filtered_temp.dropna(subset=["DATA_LINKAGEM"])

    if not df_filtered_temp.empty:
        # Demandas por Data
        demandas_por_data = df_filtered_temp.groupby(df_filtered_temp["DATA_LINKAGEM"].dt.date).size()

        fig_timeline = px.line(
            x=demandas_por_data.index,
            y=demandas_por_data.values,
            labels={"x": "Data", "y": "Demandas"},
            title="Demandas ao Longo do Tempo",
            markers=True
        )
        fig_timeline.update_layout(hovermode='x unified')
        st.plotly_chart(fig_timeline, use_container_width=True)
except Exception as e:
    logger.warning(f"Erro ao processar análise temporal: {e}")
    st.warning("⚠️ Não foi possível processar análise temporal")

# --- TABELA DETALHADA ---
st.divider()
st.subheader("📋 Detalhes das Demandas")

# Opções de visualização
col1, col2 = st.columns([3, 1])

with col1:
    busca = st.text_input("🔍 Buscar em demandas filtradas").strip().lower()

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

# --- EXPORTAR RELATÓRIO ---
st.divider()
st.subheader("📥 Exportar Dados Filtrados")

col1, col2 = st.columns(2)

with col1:
    csv = df_display[colunas_visiveis].to_csv(index=False, encoding='utf-8-sig')
    st.download_button(
        "📥 Baixar CSV",
        csv,
        f"dashboard_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
        "text/csv"
    )

with col2:
    import io
    buffer = io.BytesIO()
    with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
        df_display[colunas_visiveis].to_excel(writer, index=False, sheet_name='Demandas')
    buffer.seek(0)
    st.download_button(
        "📥 Baixar Excel",
        buffer.getvalue(),
        f"dashboard_filtrado_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx",
        "application/vnd.ms-excel"
    )