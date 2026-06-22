import streamlit as st

# Configurações globais do sistema
st.set_page_config(
    page_title="Gestão Integrada", 
    layout="wide",
    page_icon="📊"
)

# Título e Introdução
st.title("Bem-vindo ao Sistema de Gestão Integrada")
st.markdown("""
Esta é a plataforma central para controle de processos. 
Utilize o **menu lateral** (à esquerda) para navegar entre os módulos:

* **Controle de Demandas**: Gerencie e acompanhe as demandas em andamento.
* **Lista de Modelos**: Consulte, adicione ou edite a base de modelos.
""")

# Opcional: Adicionar alguma informação de status ou boas-vindas visual
st.info("💡 Dica: O menu lateral foi gerado automaticamente a partir da pasta 'pages/'.")

# Opcional: Você pode colocar uma imagem aqui se quiser um visual mais profissional
st.image("Demanda.png", width=300)