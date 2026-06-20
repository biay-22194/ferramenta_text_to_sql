import mysql.connector
import psycopg2
from vanna.legacy.ollama import Ollama
from vanna.legacy.chromadb import ChromaDB_VectorStore

BANCO_ATIVO = 'mysql'  # Opções disponíveis: 'mysql' ou 'postgres'

# Inicialização do Vanna
class SistemaVanna(ChromaDB_VectorStore, Ollama):
    def __init__(self, config=None):
        ChromaDB_VectorStore.__init__(self, config=config)
        Ollama.__init__(self, config=config)

# Modelo de IA usado e apontando para a pasta onde a memória ficará salva
vn = SistemaVanna(config={
    'model': 'qwen2.5:3b',
    'path': './memoria_vanna'
})

# Treinamento de regras, documentação e queries de exemplo
print(" Salvando regras, documentação e exemplos na memória...")

vn.train(documentation="A tabela 'instructor' armazena os IDs, nomes, departamentos e salários de cada instrutor ou professor.")
vn.train(documentation="A tabela 'classroom' armazena em qual prédio a sala de aula está localizada, seu número e capacidade. ")
vn.train(documentation="A tabela 'advisor' faz referência a qual professor é orientador de qual aluno.")
vn.train(documentation="A tabela 'course' traz informações gerais sobre os cursos, como o ID, título ou nome do curso, a qual departamento pertence e o número de créditos.")
vn.train(documentation="A tabela 'department' mostra em qual prédio cada departamento está localizado, além de seu orçamento.")
vn.train(documentation="A tabela 'prereq' faz referência a qual curso ou disciplina é pré-requisito para outra. Ou seja, você só pode cursar determinada disciplina, se já tiver feito a outra que é pré-requisito.")
vn.train(documentation="A tabela 'section' diz respeito à informações de quando uma disciplina foi ofertada.")
vn.train(documentation="A tabela 'student' contém informações dos alunos, como ID, nome, a qual departamento o aluno pertence e a quantidade de créditos que ele possui.")
vn.train(documentation="A tabela 'takes' faz referência a quais disciplinas um aluno fez, além de informações como período de tempo em que foi cursado e nota na disciplina.")
vn.train(documentation="A tabela 'teaches' faz referência a quais disciplinas um professor ministrou, além de informações como período de tempo.")
vn.train(documentation="A tabela 'time_slot' armazena os blocos de horário das aulas.")

vn.train(
        question="Listar os departamentos e cursos, mostrando os nomes dos cursos, dos seus departamentos e dos edifícios dos departamentos.",
        sql="SELECT d.dept_name, d.building, c.title AS course_title FROM department d JOIN course c ON d.dept_name = c.dept_name ORDER BY d.dept_name, c.title;"
    )
vn.train(
        question="Listar os cursos que um professor ministra",
        sql="SELECT i.name AS instructor_name, c.title AS course_title, t.semester, t.year FROM instructor i JOIN teaches t ON i.ID = t.ID JOIN course c ON t.course_id = c.course_id AND t.sec_id = c.sec_id AND t.dept_name = c.dept_name ORDER BY i.name, t.year DESC, t.semester DESC;"
)
vn.train(
        question="Listar os alunos de cada curso",
        sql="SELECT c.title AS course_title, s.name AS student_name FROM course c JOIN takes t ON c.course_id = t.course_id AND c.sec_id = t.sec_id AND c.dept_name = t.dept_name JOIN student s ON t.ID = s.ID ORDER BY c.title, s.name;"
    )
vn.train(
        question="Listar os departamentos que possuem a string “sci” como parte do seu nome.",
        sql="SELECT dept_name, building, budget FROM department WHERE dept_name LIKE '%sci%';"
    )
vn.train(
        question="Listar a soma dos salários dos professores de cada departamento, mostrando o nome do departamento e a soma salarial",
        sql="SELECT d.dept_name, SUM(i.salary) AS total_instructor_salary FROM department d JOIN instructor i ON d.dept_name = i.dept_name GROUP BY d.dept_name ORDER BY d.dept_name;"
    )
vn.train(
    question="quantos alunos tem",
    sql="SELECT COUNT(ID) AS total_alunos FROM student;"
)
vn.train(
    question="Qual a quantidade total de alunos matriculados?",
    sql="SELECT COUNT(ID) AS total_alunos FROM student;"
)
# Funções de extração de metadados (DDL)
DB_HOST = 'localhost'
DB_USER = 'user'
DB_PASS = 'senha'     
DB_NAME = 'university'

def extrair_metadados_mysql():
    print("\n Conectando ao MySQL (Porta 3306)...")
    vn.connect_to_mysql(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=3306)
    
    conn = mysql.connector.connect(host=DB_HOST, user=DB_USER, password=DB_PASS, database=DB_NAME, port=3306)
    cursor = conn.cursor()
    cursor.execute("SHOW TABLES")
    tabelas = [row[0] for row in cursor.fetchall()]

    print("Saving MySQL structures to vector memory...")
    for tabela in tabelas:
        cursor.execute(f"SHOW CREATE TABLE {tabela}")
        resultado = cursor.fetchone()
        if resultado:
            vn.train(ddl=resultado[1])
            print(f"  [+] Tabela aprendida: {tabela}")
    cursor.close()
    conn.close()

def extrair_metadados_postgres():
    print("\n Conectando ao PostgreSQL (Porta 5432)...")
    vn.connect_to_postgres(host=DB_HOST, dbname=DB_NAME, user=DB_USER, password=DB_PASS, port=5432)
    
    conn = psycopg2.connect(host=DB_HOST, database=DB_NAME, user=DB_USER, password=DB_PASS, port=5432)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT table_name FROM information_schema.tables 
        WHERE table_schema = 'public' AND table_type = 'BASE TABLE';
    """)
    tabelas = [row[0] for row in cursor.fetchall()]
    
    print("Saving PostgreSQL structures to vector memory...")
    for tabela in tabelas:
        cursor.execute(f"""
            SELECT column_name, data_type, is_nullable FROM information_schema.columns
            WHERE table_schema = 'public' AND table_name = '{tabela}';
        """)
        colunas = cursor.fetchall()
        
        schema_texto = f"Table: {tabela}\nColumns:\n"
        for col in colunas:
            schema_texto += f"  - {col[0]} ({col[1]}) {'NULL' if col[2] == 'YES' else 'NOT NULL'}\n"
        
        vn.train(ddl=schema_texto)
        print(f"  [+] Tabela aprendida: {tabela}")
    cursor.close()
    conn.close()

# Execução dinâmica
if BANCO_ATIVO.lower() == 'mysql':
    extrair_metadados_mysql()
elif BANCO_ATIVO.lower() == 'postgres':
    extrair_metadados_postgres()
else:
    print(" Erro: BANCO_ATIVO inválido. Escolha 'mysql' ou 'postgres'.")

print("\n Treinamento concluído com sucesso!")