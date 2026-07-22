import streamlit as st
import pandas as pd
import logging
from datetime import datetime
from config import carregar_dados_demandas, carregar_dados_modelos, carregar_dados_capitulos

logger = logging.getLogger(__name__)

class AlertasSistema:
    """Gerencia alertas e notificações do sistema."""

    def __init__(self):
        self.alertas = []
        self.avisos = []
        self.info = []

    def verificar_todos_alertas(self):
        """Executa todas as verificações de alerta."""
        self.alertas = []
        self.avisos = []
        self.info = []

        self._verificar_demandas_sem_capitulo()
        self._verificar_capitulos_duplicados()
        self._verificar_modelos_duplicados()
        self._verificar_capitulos_nao_utilizados()
        self._verificar_modelos_sem_demanda()
        self._verificar_demandas_recentes()
        self._verificar_versoes_obsoletas()

        return {
            "alertas": self.alertas,
            "avisos": self.avisos,
            "info": self.info
        }

    def _verificar_demandas_sem_capitulo(self):
        """Alerta: Demandas sem capítulo associado."""
        try:
            df = carregar_dados_demandas()
            sem_cap = df[df["CAPITULO"].isna() | (df["CAPITULO"].astype(str).str.strip() == "")]

            if not sem_cap.empty:
                self.alertas.append({
                    "tipo": "DEMANDA_SEM_CAPITULO",
                    "severidade": "ALTA",
                    "mensagem": f"⚠️ {len(sem_cap)} demanda(s) sem capítulo associado",
                    "detalhes": sem_cap["DEMANDA"].tolist()[:5],
                    "acao": "Edite as demandas e adicione capítulos"
                })
                logger.warning(f"Encontradas {len(sem_cap)} demandas sem capítulo")
        except Exception as e:
            logger.error(f"Erro ao verificar demandas sem capítulo: {e}")

    def _verificar_capitulos_duplicados(self):
        """Alerta: Capítulos duplicados."""
        try:
            df = carregar_dados_capitulos()
            duplicatas = df[df.duplicated(subset=["MANUAL", "CAPITULO"], keep=False)]

            if not duplicatas.empty:
                self.alertas.append({
                    "tipo": "CAPITULOS_DUPLICADOS",
                    "severidade": "MÉDIA",
                    "mensagem": f"⚠️ {len(duplicatas)} capítulo(s) duplicado(s) encontrado(s)",
                    "detalhes": duplicatas[["MANUAL", "CAPITULO"]].drop_duplicates().values.tolist()[:5],
                    "acao": "Remova os capítulos duplicados"
                })
                logger.warning(f"Encontrados {len(duplicatas)} capítulos duplicados")
        except Exception as e:
            logger.error(f"Erro ao verificar capítulos duplicados: {e}")

    def _verificar_modelos_duplicados(self):
        """Alerta: Modelos duplicados."""
        try:
            df = carregar_dados_modelos()
            duplicatas = df[df.duplicated(subset=["MÓDULO", "MANUAL", "MONTADORA", "MODELO"], keep=False)]

            if not duplicatas.empty:
                self.alertas.append({
                    "tipo": "MODELOS_DUPLICADOS",
                    "severidade": "MÉDIA",
                    "mensagem": f"⚠️ {len(duplicatas)} modelo(s) duplicado(s) encontrado(s)",
                    "detalhes": duplicatas["MODELO"].unique().tolist()[:5],
                    "acao": "Remova os modelos duplicados"
                })
                logger.warning(f"Encontrados {len(duplicatas)} modelos duplicados")
        except Exception as e:
            logger.error(f"Erro ao verificar modelos duplicados: {e}")

    def _verificar_capitulos_nao_utilizados(self):
        """Aviso: Capítulos cadastrados mas não utilizados em demandas."""
        try:
            df_cap = carregar_dados_capitulos()
            df_dem = carregar_dados_demandas()

            capitulos_utilizados = set(df_dem["CAPITULO"].unique())
            capitulos_cadastrados = set(df_cap["CAPITULO"].unique())

            nao_utilizados = capitulos_cadastrados - capitulos_utilizados

            if nao_utilizados:
                self.avisos.append({
                    "tipo": "CAPITULOS_NAO_UTILIZADOS",
                    "severidade": "BAIXA",
                    "mensagem": f"ℹ️ {len(nao_utilizados)} capítulo(s) não utilizado(s) em demandas",
                    "detalhes": list(nao_utilizados)[:5],
                    "acao": "Considere remover capítulos não utilizados"
                })
                logger.info(f"Encontrados {len(nao_utilizados)} capítulos não utilizados")
        except Exception as e:
            logger.error(f"Erro ao verificar capítulos não utilizados: {e}")

    def _verificar_modelos_sem_demanda(self):
        """Aviso: Modelos cadastrados mas sem demanda associada."""
        try:
            df_mod = carregar_dados_modelos()
            df_dem = carregar_dados_demandas()

            # Criar chave única para modelos
            modelos_em_demandas = set(
                df_dem.apply(
                    lambda x: f"{x['MÓDULO']}|{x['MANUAL']}|{x['MONTADORA']}|{x['CAPITULO']}",
                    axis=1
                )
            )

            modelos_cadastrados = set(
                df_mod.apply(
                    lambda x: f"{x['MÓDULO']}|{x['MANUAL']}|{x['MONTADORA']}|{x['CAPITULO']}",
                    axis=1
                )
            )

            sem_demanda = modelos_cadastrados - modelos_em_demandas

            if sem_demanda:
                self.avisos.append({
                    "tipo": "MODELOS_SEM_DEMANDA",
                    "severidade": "BAIXA",
                    "mensagem": f"ℹ️ {len(sem_demanda)} modelo(s) sem demanda associada",
                    "detalhes": list(sem_demanda)[:5],
                    "acao": "Verifique se esses modelos ainda são necessários"
                })
                logger.info(f"Encontrados {len(sem_demanda)} modelos sem demanda")
        except Exception as e:
            logger.error(f"Erro ao verificar modelos sem demanda: {e}")

    def _verificar_demandas_recentes(self):
        """Info: Resumo de demandas recentes (últimos 7 dias)."""
        try:
            df = carregar_dados_demandas()

            # Converter data
            df_temp = df.copy()
            df_temp["DATA_LINKAGEM"] = pd.to_datetime(
                df_temp["DATA LINKAGEM"],
                format="%d/%m/%Y",
                errors="coerce"
            )

            # Filtrar últimos 7 dias
            data_limite = pd.Timestamp.now() - pd.Timedelta(days=7)
            recentes = df_temp[df_temp["DATA_LINKAGEM"] >= data_limite]

            if not recentes.empty:
                self.info.append({
                    "tipo": "DEMANDAS_RECENTES",
                    "severidade": "INFO",
                    "mensagem": f"ℹ️ {len(recentes)} demanda(s) criada(s) nos últimos 7 dias",
                    "detalhes": recentes["DEMANDA"].tolist()[:5],
                    "acao": "Verifique as demandas recentes"
                })
                logger.info(f"Encontradas {len(recentes)} demandas recentes")
        except Exception as e:
            logger.error(f"Erro ao verificar demandas recentes: {e}")

    def _verificar_versoes_obsoletas(self):
        """Aviso: Versões antigas com muitas demandas."""
        try:
            df = carregar_dados_demandas()

            # Contar demandas por versão
            demandas_por_versao = df["VERSÃO"].value_counts()

            # Versões antigas (2024 ou anteriores)
            versoes_antigas = [v for v in demandas_por_versao.index if str(v).startswith("2024")]

            if versoes_antigas:
                total_antigas = demandas_por_versao[versoes_antigas].sum()
                self.avisos.append({
                    "tipo": "VERSOES_OBSOLETAS",
                    "severidade": "BAIXA",
                    "mensagem": f"ℹ️ {total_antigas} demanda(s) em versão(s) obsoleta(s)",
                    "detalhes": versoes_antigas[:5],
                    "acao": "Considere migrar demandas para versões mais recentes"
                })
                logger.info(f"Encontradas {total_antigas} demandas em versões obsoletas")
        except Exception as e:
            logger.error(f"Erro ao verificar versões obsoletas: {e}")


def exibir_alertas_streamlit():
    """Exibe alertas no Streamlit com formatação visual."""
    try:
        alertas_sistema = AlertasSistema()
        resultado = alertas_sistema.verificar_todos_alertas()

        alertas = resultado["alertas"]
        avisos = resultado["avisos"]
        info = resultado["info"]

        # Exibir alertas (severidade ALTA)
        if alertas:
            st.subheader("🚨 Alertas Críticos")
            for alerta in alertas:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.error(alerta["mensagem"])
                        st.write(f"**Ação recomendada:** {alerta['acao']}")
                        if alerta["detalhes"]:
                            st.write(f"**Exemplos:** {', '.join(map(str, alerta['detalhes']))}")
                    with col2:
                        st.write(f"**Tipo:** {alerta['tipo']}")
            st.divider()

        # Exibir avisos (severidade MÉDIA/BAIXA)
        if avisos:
            st.subheader("⚠️ Avisos")
            for aviso in avisos:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.warning(aviso["mensagem"])
                        st.write(f"**Ação recomendada:** {aviso['acao']}")
                        if aviso["detalhes"]:
                            st.write(f"**Exemplos:** {', '.join(map(str, aviso['detalhes'][:3]))}")
                    with col2:
                        st.write(f"**Tipo:** {aviso['tipo']}")
            st.divider()

        # Exibir informações
        if info:
            st.subheader("ℹ️ Informações")
            for informacao in info:
                with st.container():
                    col1, col2 = st.columns([4, 1])
                    with col1:
                        st.info(informacao["mensagem"])
                        if informacao["detalhes"]:
                            st.write(f"**Exemplos:** {', '.join(map(str, informacao['detalhes'][:3]))}")
                    with col2:
                        st.write(f"**Tipo:** {informacao['tipo']}")

        # Se não há alertas
        if not alertas and not avisos and not info:
            st.success("✅ Nenhum alerta no momento. Sistema operacional!")

        return resultado

    except Exception as e:
        logger.error(f"Erro ao exibir alertas: {e}")
        st.error(f"❌ Erro ao verificar alertas: {str(e)}")
        return {"alertas": [], "avisos": [], "info": []}


def exibir_alertas_sidebar():
    """Exibe resumo de alertas na sidebar."""
    try:
        alertas_sistema = AlertasSistema()
        resultado = alertas_sistema.verificar_todos_alertas()

        total_alertas = len(resultado["alertas"])
        total_avisos = len(resultado["avisos"])

        with st.sidebar:
            st.divider()
            st.subheader("🔔 Notificações")

            if total_alertas > 0:
                st.error(f"🚨 {total_alertas} alerta(s) crítico(s)")

            if total_avisos > 0:
                st.warning(f"⚠️ {total_avisos} aviso(s)")

            if total_alertas == 0 and total_avisos == 0:
                st.success("✅ Tudo normal")

            st.divider()

    except Exception as e:
        logger.error(f"Erro ao exibir alertas na sidebar: {e}")