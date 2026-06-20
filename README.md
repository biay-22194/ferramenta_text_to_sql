Para este projeto, foi utilizado o banco de dados "University".

Para a instalação dos recursos, siga:

1. No terminal (Linux/Ubuntu), primeiro instale o Ollama e depois o modelo do Qwen:
```
curl -fsSL https://ollama.com/install.sh | sh
ollama pull qwen2.5:3b
```

2. Criar uma pasta vazia.


3. Dentro dessa pasta, criar um venv e ativá-lo:
```
python3 -m venv venv
source venv/bin/activate
```

4. Com o venv ativado, instale o banco e os pacotes do Vanna:
```
pip install "vanna[chromadb,ollama]" mysql-connector-python
```

5. Instale os drivers de conexão para os bancos de dados MySQL e PostgreSQL:
```
pip install PyMySQL
pip install psycopg2-binary
```

6. Instale a biblioteca gráfica Streamlit:
```
pip install streamlit
```

7. Baixe/copie os arquivos deste github. Para rodar cada um deles faça nessa ordem:
```
python treinar_ia.py
streamlit run app.py
```
