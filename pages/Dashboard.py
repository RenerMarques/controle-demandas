import streamlit as st
import pandas as pd
import plotly.express as px
import io
import logging
from datetime import datetime
from config import carregar_dados_demandas

logger = logging.getLogger(__name__)

st.set_page_config(page_title="Dashboard de Demandas", layout="wide")
st.title("📊 Dashboard de Demandas")
st.caption("Análise completa das demandas cadastradas no sistema")

# --- CARREGAR DADOS ---
try:
    df_demandas = carregar_dados_demandas()
except Exception as e:
    st.error(f"❌ Erro ao carregar dados: {str(e)}")
    logger.error(f"Erro ao carregar dados para dashboard: {e}", exc_info=True)
    st.stop()

if df_demandas.empty:
    st.warning("⚠️ Nenhuma demanda cadastrada. Dashboard indisponível.")
    st.stop()

# --- FILTROS ---
with st.expander("🔍 Filtros", expanded=True):
    col1, col2, col3, col4, col5 = st.columns([1, 1, 1, 1, 0.6])

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

    with col5:
        st.write("")
        st.write("")
        if st.button("🔄 Limpar", use_container_width=True):
            st.rerun()

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

if df_filtered.empty:
    st.info("Nenhum registro encontrado para os filtros selecionados.")
    st.stop()

# --- KPIs ---
with st.container(border=True):
    c1, c2, c3, c4, c5 = st.columns(5)
    c1.metric("📋 Total de Demandas", len(df_filtered))
    c2.metric("🆕 Novas", len(df_filtered[df_filtered["TIPO DEMANDA"] == "NOVA"]))
    c3.metric("🛠️ Correções", len(df_filtered[df_filtered["TIPO DEMANDA"] == "CORREÇÃO"]))
    c4.metric("⬆️ Upgrades", len(df_filtered[df_filtered["TIPO DEMANDA"] == "UPGRADE"]))
    c5.metric("📚 Manuais Únicos", df_filtered["MANUAL"].nunique())

st.write("")

# --- ABAS ---
tab_geral, tab_manuais, tab_temporal, tab_dados = st.tabs([
    "📈 Visão Geral", "📚 Manuais & Montadoras", "📅 Temporal", "📋 Dados"
])

with tab_geral:
    col1, col2 = st.columns(2)
    with col1:
        demandas_por_versao = df_filtered["VERSÃO"].value_counts().sort_index()
        fig_versao = px.bar(
            x=demandas_por_versao.index, y=demandas_por_versao.values,
            labels={"x": "Versão", "y": "Quantidade"},
            title="Demandas por Versão",
            color=demandas_por_versao.values, color_continuous_scale="Blues"
        )
        fig_versao.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_versao, use_container_width=True)

    with col2:
        demandas_por_modulo = df_filtered["MÓDULO"].value_counts()
        fig_modulo = px.pie(
            values=demandas_por_modulo.values, names=demandas_por_modulo.index,
            title="Distribuição por Módulo", hole=0.4
        )
        st.plotly_chart(fig_modulo, use_container_width=True)

    tipo_versao = pd.crosstab(df_filtered["VERSÃO"], df_filtered["TIPO DEMANDA"])
    fig_tipo_versao = px.bar(
        tipo_versao, title="Tipo de Demanda por Versão", barmode="stack",
        labels={"value": "Quantidade", "index": "Versão"}
    )
    st.plotly_chart(fig_tipo_versao, use_container_width=True)

with tab_manuais:
    col1, col2 = st.columns(2)
    with col1:
        top_manuais = df_filtered["MANUAL"].value_counts().head(10).sort_values()
        fig_manuais = px.bar(
            x=top_manuais.values, y=top_manuais.index, orientation="h",
            labels={"x": "Quantidade", "y": "Manual"},
            title="Top 10 Manuais Mais Usados",
            color=top_manuais.values, color_continuous_scale="Greens"
        )
        fig_manuais.update_layout(showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_manuais, use_container_width=True)

    with col2:
        cap_unicos_manual = (
            df_filtered.groupby("MANUAL")["CAPITULO"].nunique()
            .sort_values(ascending=False).head(10)
        )
        fig_cap_manual = px.bar(
            x=cap_unicos_manual.index, y=cap_unicos_manual.values,
            labels={"x": "Manual", "y": "Capítulos Únicos"},
            title="Capítulos Únicos por Manual (Top 10)",
            color=cap_unicos_manual.values, color_continuous_scale="Oranges"
        )
        fig_cap_manual.update_layout(xaxis_tickangle=-45, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_cap_manual, use_container_width=True)

    col3, col4 = st.columns(2)
    with col3:
        top_montadoras = df_filtered["MONTADORA"].value_counts().head(10)
        fig_montadoras = px.bar(
            x=top_montadoras.index, y=top_montadoras.values,
            labels={"x": "Montadora", "y": "Quantidade"},
            title="Top 10 Montadoras",
            color=top_montadoras.values, color_continuous_scale="Reds"
        )
        fig_montadoras.update_layout(xaxis_tickangle=-45, showlegend=False, coloraxis_showscale=False)
        st.plotly_chart(fig_montadoras, use_container_width=True)

    with col4:
        heatmap_data = pd.crosstab(df_filtered["MÓDULO"], df_filtered["MONTADORA"])
        fig_heatmap = px.imshow(
            heatmap_data, labels=dict(x="Montadora", y="Módulo", color="Quantidade"),
            title="Heatmap: Módulo vs Montadora", color_continuous_scale="YlOrRd"
        )
        st.plotly_chart(fig_heatmap, use_container_width=True)

with tab_temporal:
    try:
        df_temp = df_filtered.copy()
        df_temp["DATA_LINKAGEM"] = pd.to_datetime(
            df_temp["DATA LINKAGEM"], format="%d/%m/%Y", errors="coerce"
        )
        df_temp = df_temp.dropna(subset=["DATA_LINKAGEM"])

        if df_temp.empty:
            st.info("Não há datas válidas para exibir a linha do tempo.")
        else:
            demandas_por_data = df_temp.groupby(df_temp["DATA_LINKAGEM"].dt.date).size()
            fig_timeline = px.line(
                x=demandas_por_data.index, y=demandas_por_data.values,
                labels={"x": "Data", "y": "Demandas"},
                title="Demandas ao Longo do Tempo", markers=True
            )
            fig_timeline.update_layout(hovermode='x unified')
            st.plotly_chart(fig_timeline, use_container_width=True)
    except Exception as e:
        logger.warning(f"Erro ao processar análise temporal: {e}")
        st.warning("⚠️ Não foi possível processar a análise temporal.")

with tab_dados:
    col1, col2 = st.columns([3, 1])
    with col1:
        busca = st.text_input("🔍 Buscar em demandas filtradas").strip().lower()
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
    st.caption(f"Exibindo {min(limite, len(df_display))} de {len(df_display)} registro(s).")

    st.divider()
    col_a, col_b = st.columns(2)
    with col_a:
        csv = df_display[colunas_visiveis].to_csv(index=False, encoding='utf-8-sig')
        st.download_button(
            "📥 Baixar CSV", csv,
            f"dashboard_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv", "text/csv"
        )
    with col_b:
        buffer = io.BytesIO()
        with pd.ExcelWriter(buffer, engine='openpyxl') as writer:
            df_display[colunas_visiveis].to_excel(writer, index=False, sheet_name='Demandas')
        buffer.seek(0)
        st.download_button(
            "📥 Baixar Excel", buffer.getvalue(),
            f"dashboard_demandas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx", "application/vnd.ms-excel"
        )