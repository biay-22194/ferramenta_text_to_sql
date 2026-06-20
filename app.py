import streamlit as st
import os 
import contextlib
import mysql.connector
import psycopg2
from vanna.legacy.ollama import Ollama
from vanna.legacy.chromadb import ChromaDB_VectorStore
import logging

# Desativa os logs do Vanna e do ambiente de execução
logging.getLogger('vanna').setLevel(logging.ERROR)

BANCO_ATIVO = 'mysql' # Opções: 'mysql' ou 'postgres'

# Cria a classe unindo o ChromaDB (vetores) e o Ollama (LLM local)
class SistemaVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Cache de recursos: monitora o argumento 'banco'. Se ele mudar, refaz a conexão
@st.cache_resource
def iniciar_sistema(banco):
    # Inicializa o Vanna com a memória salva
    vn = SistemaVanna(config={
        'model': 'qwen2.5:3b',
        'path': './memoria_vanna'
    })

    # Cala os prints internos do Vanna no terminal
    vn.verbose = False
    # Autoriza a IA a usar os dados para montar queries
    vn.allow_llm_to_see_data = True
    
    # Dados comuns de autenticação
    DB_HOST = 'localhost'
    DB_USER = 'user'
    DB_PASS = 'senha'     
    DB_NAME = 'university'  
    
    # Roteamento baseado na sua escolha
    if banco.lower() == 'mysql':
        vn.connect_to_mysql(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=3306)
    elif banco.lower() == 'postgres':
        vn.connect_to_postgres(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=5432)
        
    return vn

# Inicializa o sistema passando a sua escolha do topo do arquivo
vn = iniciar_sistema(BANCO_ATIVO)

#Interface gráfica
def main():
    # Configura o título e ícone da página na aba do navegador
    st.set_page_config(page_title="Ferramenta de Text-to-SQL")
    
    # Cabeçalho da interface
    st.title("Assistente de Banco de Dados")
    st.markdown("Faça perguntas em linguagem natural: ")
    st.divider() # Linha horizontal
    
    # Caixa de texto para o usuário digitar a pergunta
    pergunta = st.text_input("Qual a sua dúvida?")
    
    # Botão de ação
    if st.button("Gerar Resposta"):
        if pergunta: 
            with st.spinner(" Processando com qwen2.5:3b..."):
                try:
                    # 1. Silencia o terminal e gera o SQL
                    with open(os.devnull, 'w') as f, contextlib.redirect_stdout(f), contextlib.redirect_stderr(f):
                        query_sql = vn.generate_sql(question=pergunta)
                    
                    # 2. Mostra a Query gerada na tela
                    st.subheader("Query SQL Gerada:")
                    st.code(query_sql, language="sql")
                    
                    # Executa a query no MySQL e guarda o resultado em 'df_resultado'
                    df_resultado = vn.run_sql(query_sql)
                    
                    # 3. Mostra a tabela de resultados na tela
                    st.subheader("Resultados do Banco:")
                    st.table(df_resultado)
                    
                except Exception as e:
                    # Mostra o erro na caixa vermelha se algo falhar
                    st.error(f"Erro ao processar a pergunta: {e}")
        else:
            st.warning("Por favor, digite uma pergunta antes de buscar.")

if __name__ == '__main__':
    main()