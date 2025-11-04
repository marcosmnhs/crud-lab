import streamlit as st
from sqlalchemy import create_engine, text
from random import choice
import string
import pandas as pd

# --- Configuração do Banco de Dados (Segura com st.secrets) ---

try:
    # Tenta carregar as credenciais do Streamlit Secrets
    DB_USER = st.secrets["postgresql"]["user"]
    DB_PASSWORD = st.secrets["postgresql"]["password"]
    DB_HOST = st.secrets["postgresql"]["host"]
    DB_PORT = st.secrets["postgresql"]["port"]
    DB_NAME = st.secrets["postgresql"]["dbname"]
    
    # URL de conexão
    db_url = f"postgresql+psycopg2://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

except KeyError:
    # Se st.secrets não estiver configurado (ex: rodando localmente sem o arquivo)
    st.error("Erro: Credenciais do banco de dados não configuradas no st.secrets.")
    st.stop() # Para a execução do script

@st.cache_resource
def get_engine():
    """Cria e armazena em cache o engine de conexão com o banco."""
    try:
        engine = create_engine(db_url)
        # Testa a conexão
        with engine.connect() as conn:
            pass
        return engine
    except Exception as e:
        st.error(f"Não foi possível conectar ao banco de dados: {e}")
        st.stop()

engine = get_engine()

# --- Funções Auxiliares (do seu código original) ---

def gera_sequencia(tamanho):
    """
    Função que escolhe um número aleatório entre 1 e 2.
    """
    sequencia = ''
    digitos = string.digits[1:3] # '1' ou '2'
    for i in range(tamanho):
        sequencia += str(choice(digitos))
    return sequencia

# --- Páginas da Aplicação ---

def page_inserir():
    """Página para inserir um novo cliente e conta."""
    st.subheader("Inserir Novo Cliente")
    
    with st.form("form_insercao"):
        cpf = st.text_input("CPF (apenas 11 números)", max_chars=11)
        nome = st.text_input("Nome Completo")
        
        submitted = st.form_submit_button("Cadastrar Cliente")

    if submitted:
        if len(cpf) != 11 or not cpf.isdigit():
            st.error("CPF inválido. Deve conter exatamente 11 números.")
        elif not nome:
            st.error("O nome não pode estar em branco.")
        else:
            try:
                agencia = gera_sequencia(1)
                
                query = text("""
                    INSERT INTO cliente (cpf, nome) VALUES (:cpf, :nome);
                    INSERT INTO conta_bancaria (cpf_cliente, num_agencia, saldo) VALUES (:cpf, :agencia, 0);
                """)
                
                with engine.connect() as conn:
                    conn.execute(query, {"cpf": cpf, "nome": nome, "agencia": agencia})
                    conn.commit()
                
                st.success(f"Cliente {nome} (CPF: {cpf}) e conta na agência {agencia} criados com sucesso!")
            
            except Exception as e:
                st.error(f"Erro ao inserir no banco de dados: {e}")
                st.warning("Possível causa: Este CPF já pode estar cadastrado.")

def page_transacao():
    """Página que realiza uma transação"""

    opcoes_transacao = ['Débito', 'Crédito', 'Saque', 'Depósito', 'Transferência']

    st.subheader("Faz uma transferência.")
    
    with st.form("form_insercao"):
        num_conta = st.text_input("Numero da conta", max_chars=3)
        valor = st.number_input("Valor (R$): ", min_value=0.01, max_value=10000.00)
        tipo = st.selectbox(
            label = "Tipo de transação:",
            options=opcoes_transacao,
            index=None,
            placeholder="Selecione uma opção..."
        )
        
        submitted = st.form_submit_button("Realizar transação")

    if submitted:
        if 0 < valor <= 10.000:
            st.error("O valor deve um número maior que 0 e menor que 10.000,01.")
        elif not num_conta:
            st.error("O número da conta não pode estar em branco.")
        elif tipo is None:
            st.error("Preencha o tipo da transação.")
        else:
            try:                
                query = text("""
                    INSERT INTO transacao (num_conta, valor, tipo, data_hora) VALUES (:num_conta, :valor, :tipo, NOW());
                """)
                
                with engine.connect() as conn:
                    conn.execute(query, {"num_conta": num_conta, "valor": valor, "tipo": tipo})
                    conn.commit()
                
                st.success(f"Transação de {tipo} no valor de {valor} e conta número {num_conta} realizada com sucesso!")
            
            except Exception as e:
                st.error(f"Erro ao inserir no banco de dados: {e}")
                st.warning("Possível causa: Este número de conta pode não existir.")

def page_consultar():
    """Página para consultar informações do cliente."""
    st.subheader("Consultar Informações do Cliente")
    
    cpf = st.text_input("Digite o CPF (11 números) ou deixe em branco para buscar todos", max_chars=11)
    
    if st.button("Consultar"):
        
        params = {}
        
        if not cpf: 
            st.info("Buscando todos os clientes...")
            query = text("""
                SELECT 
                    c.nome AS "Nome", 
                    cb.num_agencia AS "Agência", 
                    cb.numero AS "Conta", 
                    t.ddd AS "DDD", 
                    t.numero AS "Telefone"
                FROM cliente c
                LEFT JOIN conta_bancaria cb ON c.cpf = cb.cpf_cliente
                LEFT JOIN telefone t ON c.cpf = t.cpf_cliente;
            """)

        elif len(cpf) == 11 and cpf.isdigit():
            query = text("""
                SELECT 
                    c.nome AS "Nome", 
                    cb.num_agencia AS "Agência", 
                    cb.numero AS "Conta", 
                    t.ddd AS "DDD", 
                    t.numero AS "Telefone"
                FROM cliente c
                LEFT JOIN conta_bancaria cb ON c.cpf = cb.cpf_cliente
                LEFT JOIN telefone t ON c.cpf = t.cpf_cliente
                WHERE c.cpf = :cpf;
            """)
            params = {"cpf": cpf} 

        else:
            st.error("CPF inválido. Deve conter 11 números ou estar totalmente em branco.")
            st.stop() 

        try:
            with engine.connect() as conn:
                
                result = conn.execute(query, params) 
                data = result.fetchall()
            
            if data:
                
                df = pd.DataFrame(data, columns=result.keys())
                st.dataframe(df)
            else:
                st.warning("Nenhum registro encontrado.")
        except Exception as e:
            st.error(f"Erro ao consultar o banco de dados: {e}")

def _buscar_telefones(cpf):
    """Função interna para buscar telefones de um cliente."""
    query_consulta = text("""
        SELECT t.id, t.ddd, t.numero
        FROM cliente c
        JOIN telefone t ON c.cpf = t.cpf_cliente
        WHERE c.cpf = :cpf;
    """)
    with engine.connect() as conn:
        result = conn.execute(query_consulta, {"cpf": cpf})
        return result.mappings().fetchall()

def page_editar():
    """Página para editar um número de telefone."""
    st.subheader("Editar Telefone do Cliente")
    
    cpf = st.text_input("1. Digite o CPF do cliente", max_chars=11, key="cpf_editar")
    
    if len(cpf) == 11 and cpf.isdigit():
        try:
            telefones = _buscar_telefones(cpf)
            
            if not telefones:
                st.info("Cliente não possui telefones cadastrados. (Você pode ter que adicionar a funcionalidade de 'Inserir Telefone' primeiro).")
                return

            st.write("Telefones cadastrados:")
            df_tel = pd.DataFrame(telefones)
            st.dataframe(df_tel)
            
            opcoes_tel = {t['id']: f"ID {t['id']}: ({t['ddd']}) {t['numero']}" for t in telefones}
            
            with st.form("form_edicao"):
                st.write("2. Selecione o telefone e insira os novos dados:")
                
                id_tel = st.selectbox("Telefone para alterar", options=opcoes_tel.keys(), format_func=lambda x: opcoes_tel[x])
                ddd_novo = st.text_input("Novo DDD", max_chars=2)
                numero_novo = st.text_input("Novo Número", max_chars=9)
                
                submitted = st.form_submit_button("Atualizar Telefone")

            if submitted:
                if ddd_novo.isdigit() and numero_novo.isdigit():
                    query_update = text("UPDATE telefone SET ddd = :ddd_novo, numero = :numero_novo WHERE id = :id;")
                    with engine.connect() as conn:
                        conn.execute(query_update, {"id": id_tel, "ddd_novo": ddd_novo, "numero_novo": numero_novo})
                        conn.commit()
                    st.success(f"Telefone ID {id_tel} atualizado com sucesso!")
                    # st.rerun() # Descomente se quiser que a página recarregue
                else:
                    st.error("DDD e Número devem conter apenas dígitos.")

        except Exception as e:
            st.error(f"Erro no processo de edição: {e}")

def page_excluir():
    """Página para excluir um número de telefone."""
    st.subheader("Excluir Telefone do Cliente")
    
    cpf = st.text_input("1. Digite o CPF do cliente", max_chars=11, key="cpf_excluir")
    
    if len(cpf) == 11 and cpf.isdigit():
        try:
            telefones = _buscar_telefones(cpf)
            
            if not telefones:
                st.info("Cliente não possui telefones cadastrados.")
                return

            st.write("Telefones cadastrados:")
            df_tel = pd.DataFrame(telefones)
            st.dataframe(df_tel)
            
            opcoes_tel = {t['id']: f"ID {t['id']}: ({t['ddd']}) {t['numero']}" for t in telefones}
            
            with st.form("form_exclusao"):
                st.write("2. Selecione o telefone para excluir:")
                id_tel = st.selectbox("Telefone para EXCLUIR", options=opcoes_tel.keys(), format_func=lambda x: opcoes_tel[x])
                
                confirmacao = st.checkbox(f"Sim, eu confirmo que desejo excluir o telefone ID {id_tel}.")
                
                submitted = st.form_submit_button("EXCLUIR")

            if submitted:
                if confirmacao:
                    query_exclusao = text("DELETE FROM telefone WHERE id = :id;")
                    with engine.connect() as conn:
                        conn.execute(query_exclusao, {"id": id_tel})
                        conn.commit()
                    st.success(f"Telefone ID {id_tel} excluído com sucesso!")
                else:
                    st.warning("Você deve marcar a caixa de confirmação para excluir.")
                    
        except Exception as e:
            st.error(f"Erro no processo de exclusão: {e}")

# --- Menu Principal (Sidebar) ---

st.set_page_config(page_title="Gestão Bancária", layout="wide")
st.title("🏦 Sistema de Gerenciamento Bancário")

# Opções do menu
menu_opcoes = {
    "Inserir Cliente": page_inserir,
    "Consultar Cliente": page_consultar,
    "Editar Telefone": page_editar,
    "Excluir Telefone": page_excluir,
    "Realizar Transação": page_transacao
}

# Cria o menu na barra lateral
escolha = st.sidebar.radio("Selecione a Operação", menu_opcoes.keys())

# Chama a função da página selecionada
pagina_selecionada = menu_opcoes[escolha]
pagina_selecionada()