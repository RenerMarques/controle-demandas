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

