from sqlalchemy import create_engine, text
from random import choice
import string

DB_USER = ""
DB_PASSWORD = ""
DB_PORT = 5432
DB_NAME = ""


engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}")

def menu():
    print("""
        1. INSERIR CLIENTES
        2. EDITAR INFORMAÇÕES
        3. CONSULTAR CLIENTES
        4. EXCLUIR CLIENTES
            """)
    escolha = int(input("Escolha (1/2/3/4): "))
    if escolha == 1:
        insercao()
    elif escolha == 2:
        edicao()
    elif escolha == 3:
        consulta()
    elif escolha == 4:
        exclusao()
    else:
        print("Valor não reconhecido. Tente novamente")
        menu()

def insercao():
    """
    Função que insere um cliente na tabela cliente e uma conta bancaria na conta_bancaria.
    """


    cpf = input("Digite o CPF do cliente (apenas numeros): ")
    if len(cpf) != 11:
        print("CPF inválido. Deve ser digitado 11 números.")
        insercao()
    else:
        nome = input("Nome do cliente: ")
        agencia = gera_sequencia(1)
    
    query = """INSERT INTO cliente (cpf, nome) VALUES (:cpf, :nome);
               INSERT INTO conta_bancaria (cpf_cliente, num_agencia, saldo) VALUES (:cpf, :agencia, 0);"""

    with engine.connect() as conn:
        result = conn.execute(text(query), {"cpf": cpf, "nome": nome, "agencia": agencia})

        conn.commit()
        print("Valores inseridos!")

def gera_sequencia(tamanho):
    """
    Função que escolhe um número aleatório entre 1 e 2.
    """

    sequencia = ''
    digitos = string.digits[1:3]
    for i in range(tamanho):
        sequencia += str(choice(digitos))
    return sequencia

def edicao():
    """
    Função que edita um número de telefone de um cliente.
    """
    print("VAMOS EDITAR O NÚMERO DE TELEFONE DO CLIENTE")

    cpf = input("CPF do cliente: ")

    query_consulta = """
            SELECT t.id, c.nome, t.ddd, t.numero
            FROM cliente c
            JOIN telefone t
            ON c.cpf = t.cpf_cliente
            WHERE c.cpf = :cpf;
            """

    
    with engine.connect() as conn:
        result = conn.execute(text(query_consulta), {"cpf", cpf})
        for raw in result:
            print(raw)
        
        id = input("Digite o id do telefone que será alterado: ")
        ddd_novo = input("Digite o novo ddd: ")
        numero_novo = input("Digite o novo número: ")

        query_update = """
            UPDATE telefone
            SET ddd = :ddd_novo, numero = :numero_novo
            WHERE id = :id;
            """

        conn.execute(text(query_update), {"id": id, "ddd_novo": ddd_novo, "numero_novo": numero_novo})
        conn.commit()

def consulta():
    """
    Função que nos mostra nome do cliente, agencia, conta e telefone.
    """

    cpf = input("Digite o CPF do cliente: ")

    query = """
            SELECT c.nome, cb.num_agencia, cb.numero, t.ddd, t.numero
            FROM cliente c
            JOIN conta_bancaria cb
            ON c.cpf = cb.cpf_cliente
            JOIN telefone t
            ON c.cpf = t.cpf_cliente
            WHERE c.cpf = :cpf;
            """

    with engine.connect() as conn:
        result = conn.execute(text(query), {"cpf": cpf})
        print("(name, num_agencia, numero_conta, ddd, telefone)")
        for raw in result:
            print(raw)

def exclusao():
    """
    exclui um telefone do cliente
    """
    cpf = input("Digite o CPF do cliente: ")

    query_consulta = """
            SELECT t.id, c.nome, t.ddd, t.numero
            FROM cliente c
            JOIN telefone t
            ON c.cpf = t.cpf_cliente
            WHERE c.cpf = :cpf;
            """

    with engine.connect() as conn:
        result = conn.execute(text(query_consulta), {"cpf", cpf})
        for raw in result:
            print(raw)
        
        id = input("Insira o id do telefone que será excluído: ")

        query_exclusao = """
                DELETE 
                FROM telefone
                WHERE id = :id;
                """
    
        conn.execute(text(query_exclusao), {"id": id})
        conn.commit()

menu()