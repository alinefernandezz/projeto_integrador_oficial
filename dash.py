import numpy as np
import streamlit as st
import pandas as pd
import plotly.express as px
from query import *
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError
import base64
import smtplib
import email.message

# Inicialização do Streamlit
st.set_page_config(page_title="Dashboard", layout="wide")

# Função para exibir a interface
def exibir_interface():
    st.title("Dashboard com Notificações por E-mail")

# Consulta no banco de dados
query = "SELECT * FROM tb_registro"

# Carregar os dados do MySQL
df = conexao(query)

# Botão para atualização dos dados
if st.button("Atualizar dados"):
    df = conexao(query)



def obter_dados_mais_recentes():
    query = """
    SELECT temperatura, umidade, co2, poeira
    FROM tb_registro
    ORDER BY tempo_registro DESC
    LIMIT 1
    """
    # Execute a consulta no banco de dados para obter os valores mais recentes
    dados = conexao(query)
    
    if dados.empty:
        return None  # Se não houver dados, retorna None
    
    # Retorne os valores mais recentes como uma tupla
    return dados.iloc[0]  # Pega o primeiro registro que é o mais recente


# Seleção de colunas X e Y
colunaX = st.sidebar.selectbox("Eixo X", options=["umidade", "temperatura", "pressao", "altitude", "co2", "poeira"], index=0)
colunaY = st.sidebar.selectbox("Eixo Y", options=["umidade", "temperatura", "pressao", "altitude", "co2", "poeira"], index=1)

# Filtro de range (slider) para atributos
st.sidebar.header("Selecione o filtro")
atributos = ["temperatura", "umidade", "altitude", "pressao", "co2", "poeira"]
filtros_range = {}

for atributo in atributos:
    filtros_range[atributo] = st.sidebar.slider(
        f"{atributo.capitalize()}",
        min_value=float(df[atributo].min()),
        max_value=float(df[atributo].max()),
        value=(float(df[atributo].min()), float(df[atributo].max())),
        step=0.1
    )

# Aplicação dos filtros
df_selecionado = df.copy()
for atributo, (min_val, max_val) in filtros_range.items():
    df_selecionado = df_selecionado[
        (df_selecionado[atributo] >= min_val) & (df_selecionado[atributo] <= max_val)
    ]

# Função para exibir informações
def Home():
    with st.expander("Tabela"):
        mostrarDados = st.multiselect("Filtros:", df_selecionado.columns, default=[], key="showData_home")
        if mostrarDados:
            st.write(df_selecionado[mostrarDados])

    if not df_selecionado.empty:
        media_umidade = df_selecionado['umidade'].mean()
        media_temperatura = df_selecionado['temperatura'].mean()
        media_co2 = df_selecionado['co2'].mean()

        media1, media2, media3 = st.columns(3, gap='large')
        with media1:
            st.info('Média de Registros de Umidade')
            st.metric(label='Média', value=f'{media_umidade:.2f}')
        with media2:
            st.info('Média de Registros de Temperatura')
            st.metric(label='Média', value=f'{media_temperatura:.2f}')
        with media3:
            st.info('Média de Registros de CO2')
            st.metric(label='Média', value=f'{media_co2:.2f}')
        st.markdown("""-------------------""")

    # Botão para exportar dados
    if not df_selecionado.empty:
        col1, col2 = st.columns(2)
        with col1:
            st.download_button(
                label="Baixar Dados Filtrados (CSV)",
                data=df_selecionado.to_csv(index=False).encode('utf-8'),
                file_name='dados_filtrados.csv',
                mime='text/csv'
            )

        # Botão para exportar relatório estatístico
        with col2:
            if not df_selecionado.empty:
                descricao_estatisticas = df_selecionado.describe().transpose()
                st.download_button(
                    label="Baixar Relatório Estatístico (CSV)",
                    data=descricao_estatisticas.to_csv().encode('utf-8'),
                    file_name='relatorio_estatistico.csv',
                    mime='text/csv'
                )
####### INICIANDO INTEGRACAO COM GMAIL #############
def enviar_email(assunto, destinatario, corpo_email, remetente, senha):
    try:
        # Configuração da mensagem de e-mail
        msg = email.message.Message()
        msg['Subject'] = assunto
        msg['From'] = remetente
        msg['To'] = destinatario
        msg.add_header('Content-Type', 'text/html')
        msg.set_payload(corpo_email)

        # Conexão com o servidor SMTP
        with smtplib.SMTP('smtp.gmail.com', 587) as s:
            s.starttls()
            s.login(remetente, senha)
            s.sendmail(remetente, destinatario, msg.as_string().encode('utf-8'))
        print(f'E-mail enviado para {destinatario} com o assunto: "{assunto}"')

    except Exception as e:
        print(f"Erro ao enviar e-mail: {e}")

# Função para verificar condições e enviar alertas personalizados
def verificar_condicoes_e_enviar_email(temperatura, umidade, co2, poeira, remetente, senha):
    limite_temperatura = 30
    limite_umidade = 20
    limite_co2 = 1000
    limite_poeira = 150

    # Condições e mensagens personalizadas
    if temperatura > limite_temperatura:
        assunto = "Alerta: Temperatura Alta"
        corpo_email = f"""
        <p>A temperatura está acima do limite!</p>
        <p><b>Temperatura Atual:</b> {temperatura}°C</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

    if umidade < limite_umidade:
        assunto = "Alerta: Umidade Baixa"
        corpo_email = f"""
        <p>A umidade está abaixo do limite!</p>
        <p><b>Umidade Atual:</b> {umidade}%</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

    if co2 > limite_co2:
        assunto = "Alerta: Nível de CO2 Alto"
        corpo_email = f"""
        <p>O nível de CO2 está acima do limite!</p>
        <p><b>CO2 Atual:</b> {co2} ppm</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandesb12@gmail.com', corpo_email, remetente, senha)

    if poeira > limite_poeira:
        assunto = "Alerta: Concentração de Poeira Alta"
        corpo_email = f"""
        <p>A concentração de poeira está acima do limite!</p>
        <p><b>Poeira Atual:</b> {poeira} µg/m³</p>
        <p>Por favor, tome as medidas necessárias.</p>
        """
        enviar_email(assunto, 'aline.fernandes.02032002@gmail.com', corpo_email, remetente, senha)

if __name__ == "__main__":
    # Obter os dados mais recentes do banco de dados
    dados_mais_recentes = obter_dados_mais_recentes()

    if dados_mais_recentes is not None:
        temperatura_atual = dados_mais_recentes['temperatura']
        umidade_atual = dados_mais_recentes['umidade']
        co2_atual = dados_mais_recentes['co2']
        poeira_atual = dados_mais_recentes['poeira']
    else:
        # Caso não haja dados no banco de dados, defina valores padrão ou gere um erro
        temperatura_atual = 0
        umidade_atual = 0
        co2_atual = 0
        poeira_atual = 0


    # Credenciais do remetente
    email_remetente = "sprespiraoficial@gmail.com"
    senha_remetente = "ysxv ulgy vfjq tvei"

    # Verificar condições e enviar alertas
    verificar_condicoes_e_enviar_email(
        temperatura_atual, 
        umidade_atual, 
        co2_atual, 
        poeira_atual, 
        email_remetente, 
        senha_remetente
    )

################## INICIANDO GRAFICOS #####################

# Função para exibir gráficos
def graficos():
    st.title('Dashboard de Monitoramento')

    aba1, aba2, aba4 = st.tabs(['Gráfico de Barras', 'Gráfico de Dispersão', 'Gráfico de Histograma'])

    # Gráfico de Barras
    with aba1:
        if df_selecionado.empty:
            st.write('Nenhum dado está disponível para gerar o gráfico')
        else:
            try:
                grupo_dados = df_selecionado.groupby(by=[colunaX]).size().reset_index(name="contagem")

                fig_barras = px.bar(
                    grupo_dados,
                    x=colunaX,
                    y="contagem",
                    title=f"Contagem de Registros por {colunaX.capitalize()}",
                    color_discrete_sequence=["#228B22"],
                    template="plotly_white"
                )
                st.plotly_chart(fig_barras, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar o gráfico de barras: {e}")

    # Gráfico de Dispersão
    with aba2:
        if df_selecionado.empty:
            st.write('Nenhum dado está disponível para gerar o gráfico de dispersão')
        elif colunaX == colunaY:
            st.warning('Selecione uma opção diferente para os eixos X e Y')
        else:
            try:
                fig_disp = px.scatter(
                    df_selecionado,
                    x=colunaX,
                    y=colunaY,
                    title=f"Gráfico de Dispersão: {colunaX.capitalize()} vs {colunaY.capitalize()}",
                    color_discrete_sequence=["#AF0000"],
                    template="plotly_white"
                )
                st.plotly_chart(fig_disp, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar o gráfico de dispersão: {e}")

    # Gráfico de Histograma
    with aba4:
        if df_selecionado.empty:
            st.write('Nenhum dado está disponível para gerar o gráfico de histograma')
        else:
            try:
                fig_hist = px.histogram(
                    df_selecionado,
                    x=colunaX,
                    title=f"Distribuição de {colunaX.capitalize()}",
                    color_discrete_sequence=["#FFA500"],
                    template="plotly_white"
                )
                st.plotly_chart(fig_hist, use_container_width=True)
            except Exception as e:
                st.error(f"Erro ao criar o gráfico de histograma: {e}")
########## ENCERRANDO GRAFICOS ######################################

# Função de início
def mainPy():
    Home()
    graficos()


if __name__ == '__main__':
    mainPy()
