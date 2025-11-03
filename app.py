from sqlalchemy import create_engine, text
from random import choice
import string

# -----------------------------------------------------------------
# ATENÇÃO: Insira suas credenciais do banco de dados aqui
# -----------------------------------------------------------------
DB_USER = "marcos"
DB_PASSWORD = "senha123"
DB_PORT = 5432
DB_NAME = "bnbb"
# -----------------------------------------------------------------


try:
    engine = create_engine(f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@localhost:{DB_PORT}/{DB_NAME}")

    with engine.connect() as conn:
        pass
    print("Conexão com o banco de dados bem-sucedida!")
except Exception as e:
    print(f"Erro ao conectar ao banco de dados: {e}")
    print("Verifique suas credenciais (DB_USER, DB_PASSWORD, DB_NAME) no topo do script.")
    exit()

def menu():
    print("""
        1. INSERIR CLIENTES
        2. EDITAR INFORMAÇÕES
        3. CONSULTAR CLIENTES
        4. EXCLUIR CLIENTES
        5. SAIR
            """)
    try:
        escolha = int(input("Escolha (1/2/3/4/5): "))
        if escolha == 1:
            insercao()
        elif escolha == 2:
            edicao()
        elif escolha == 3:
            consulta()
        elif escolha == 4:
            exclusao()
        elif escolha == 5:
            print("Encerrando o programa.")
            return
        else:
            print("Valor não reconhecido. Tente novamente")
    except ValueError:
        print("Entrada inválida. Digite apenas números (1-5).")

    menu()

def insercao():
    """
    Função que insere um cliente na tabela cliente e uma conta bancaria na conta_bancaria.
    """
    cpf = input("Digite o CPF do cliente (apenas numeros): ")
    if len(cpf) != 11 or not cpf.isdigit():
        print("CPF inválido. Deve ser digitado 11 números.")
        return
    
    nome = input("Nome do cliente: ")
    agencia = gera_sequencia(1)
    
    query_cliente = "INSERT INTO cliente (cpf, nome) VALUES (:cpf, :nome)"
    query_conta = "INSERT INTO conta_bancaria (cpf_cliente, num_agencia, saldo) VALUES (:cpf, :agencia, 0)"

    try:
        with engine.connect() as conn:
            conn.execute(text(query_cliente), {"cpf": cpf, "nome": nome})
            conn.execute(text(query_conta), {"cpf": cpf, "agencia": agencia})
            conn.commit()
            
        print(f"Cliente {nome} e conta na agência {agencia} inseridos com sucesso!")
        
    except Exception as e:
        print(f"\n--- Erro ao inserir ---")
        print(f"Detalhe: {e}")
        print("Possível causa: O CPF informado já existe no banco de dados.\n")


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
    if len(cpf) != 11 or not cpf.isdigit():
        print("CPF inválido.")
        return

    query_consulta = """
            SELECT t.id, c.nome, t.ddd, t.numero
            FROM cliente c
            JOIN telefone t
            ON c.cpf = t.cpf_cliente
            WHERE c.cpf = :cpf;
            """
    
    try:
        with engine.connect() as conn:
            
            result = conn.execute(text(query_consulta), {"cpf": cpf})
            telefones = result.fetchall() 
            
            if not telefones:
                print("Nenhum telefone encontrado para este CPF.")
                return

            print("Telefones encontrados:")
            for raw in telefones:
                print(f"  ID: {raw.id}, Nome: {raw.nome}, Telefone: ({raw.ddd}) {raw.numero}")
            
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
            print("Telefone atualizado com sucesso!")
            
    except Exception as e:
        print(f"\n--- Erro ao editar ---")
        print(f"Detalhe: {e}\n")


def consulta():
    """
    Função que nos mostra nome do cliente, agencia, conta e telefone.
    """
    cpf = input("Digite o CPF do cliente (ou deixe em branco para buscar todos): ")

    params = {}
    
    query_base = """
            SELECT c.nome, cb.num_agencia, cb.numero, t.ddd, t.numero
            FROM cliente c
            LEFT JOIN conta_bancaria cb ON c.cpf = cb.cpf_cliente
            LEFT JOIN telefone t ON c.cpf = t.cpf_cliente
            """
            
    if not cpf:
        
        query = text(query_base + ";")
    
    elif len(cpf) == 11 and cpf.isdigit():
        query = text(query_base + " WHERE c.cpf = :cpf;")
        params = {"cpf": cpf}
        
    else:
        print("CPF inválido. Deve ter 11 números ou estar em branco.")
        return

    try:
        with engine.connect() as conn:
            result = conn.execute(query, params)
            
            print("\n(Nome, Agência, Conta, DDD, Telefone)")
            print("-" * 50)
            
            dados = result.fetchall()
            if not dados:
                print("Nenhum resultado encontrado.")
            else:
                for raw in dados:
                    print(raw)
            print("-" * 50)
            
    except Exception as e:
        print(f"\n--- Erro ao consultar ---")
        print(f"Detalhe: {e}\n")


def exclusao():
    """
    exclui um telefone do cliente
    """
    print("VAMOS EXCLUIR UM TELEFONE DO CLIENTE")
    
    cpf = input("Digite o CPF do cliente: ")
    if len(cpf) != 11 or not cpf.isdigit():
        print("CPF inválido.")
        return

    query_consulta = """
            SELECT t.id, c.nome, t.ddd, t.numero
            FROM cliente c
            JOIN telefone t
            ON c.cpf = t.cpf_cliente
            WHERE c.cpf = :cpf;
            """
    
    try:
        with engine.connect() as conn:
        
            result = conn.execute(text(query_consulta), {"cpf": cpf})
            telefones = result.fetchall()

            if not telefones:
                print("Nenhum telefone encontrado para este CPF.")
                return

            print("Telefones encontrados:")
            for raw in telefones:
                print(f"  ID: {raw.id}, Nome: {raw.nome}, Telefone: ({raw.ddd}) {raw.numero}")
            
            id = input("Insira o id do telefone que será excluído: ")

            query_exclusao = "DELETE FROM telefone WHERE id = :id;"
        
            conn.execute(text(query_exclusao), {"id": id})
            conn.commit()
            print("Telefone excluído com sucesso!")
            
    except Exception as e:
        print(f"\n--- Erro ao excluir ---")
        print(f"Detalhe: {e}\n")

if __name__ == "__main__":
    menu()