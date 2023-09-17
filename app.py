from flask import Flask, render_template, request, flash, redirect, session, url_for
from flask_sqlalchemy import SQLAlchemy
from datetime import datetime
import matplotlib.pyplot as plt


app = Flask(__name__)
app.config['SECRET_KEY'] = "minha-chave"
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///../database/mirandaeletronicos.db'
db = SQLAlchemy(app)


#CLASSES E TABELAS

class Usuarios(db.Model):
    __tablename__ = "usuarios"
    id_usuario = db.Column(db.Integer, primary_key=True) #Inclui administrador, cliente e fornecedor.
    tipo = db.Column(db.String(20))
    email = db.Column(db.String(150), unique=True)
    senha = db.Column(db.String(100))
    nome = db.Column(db.String(100))
    nif = db.Column(db.Integer)
    tel = db.Column(db.Integer)
    morada = db.Column(db.String(200))

    def __init__(self, tipo, email, senha, nome, nif, tel, morada):
        self.tipo = tipo
        self.email = email
        self.senha = senha
        self.nome = nome
        self.nif = nif
        self.tel = tel
        self.morada = morada

    def __repr__(self):
        return "Usuário: {}, id: {}".format(self.nome, self.id_usuario)

class Produtos(db.Model):
    __tablename__ = "produtos"
    id_produto = db.Column(db.Integer, primary_key=True)
    id_fornecedor = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    nome_produto = db.Column(db.String(100), unique=True)
    descricao_produto = db.Column(db.String(200))
    preco_iva = db.Column(db.Float) #Preço definido para a venda a clientes, com iva já incluído
    preco_compra = db.Column(db.Float) #Preço no qual o produto foi comprado pelo fornecedor
    qtd_stock = db.Column(db.Integer)
    lugar_armazem = db.Column(db.String(100))

    fornecedor = db.relationship('Usuarios', foreign_keys=id_fornecedor) #Relacionamento entre a tabela "usuarios" e o id_fornecedor da tabela "produtos"

    def __init__(self, nome_produto, descricao_produto, preco_iva, preco_compra, qtd_stock, lugar_armazem, id_forncedor):
        self.nome_produto = nome_produto
        self.descricao_produto = descricao_produto
        self.preco_iva = preco_iva #Preço definido para a venda a clientes, com iva já incluído
        self.preco_compra = preco_compra #Preço no qual o produto foi comprado pelo fornecedor
        self.qtd_stock = qtd_stock
        self.lugar_armazem = lugar_armazem
        self.id_fornecedor = id_forncedor

#Propriedade para calcular se o estoque está a menos de 20%

    @property
    def alerta(self):
        max_stock = 80
        return self.qtd_stock <= (0.2 * max_stock)

    def __repr__(self):
        return "{}".format(self.nome_produto)


class Compra(db.Model):
    __tablename__ = "compras"
    id_compra = db.Column(db.Integer, primary_key=True)
    id_fornecedor = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    id_administrador = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    data_compra = db.Column(db.Date)
    nome_produto = db.Column(db.String, db.ForeignKey('produtos.nome_produto'))
    preco_compra = db.Column(db.Float, db.ForeignKey('produtos.preco_iva'))
    quantidade = db.Column(db.Integer)
    desconto = db.Column(db.Float)
    valor_total = db.Column(db.Float)

    produto = db.relationship('Produtos', foreign_keys=nome_produto)
    fornecedor = db.relationship('Usuarios', foreign_keys=id_fornecedor) 
    administrador = db.relationship('Usuarios', foreign_keys=id_administrador)

    def __init__(self, id_administrador, data_compra, nome_produto, preco_compra, quantidade, id_fornecedor):
        self.id_administrador = id_administrador
        self.data_compra = data_compra
        self.nome_produto = nome_produto
        self.preco_compra = preco_compra
        self.quantidade = quantidade
        self.desconto = 0.0
        self.id_fornecedor = id_fornecedor

    def __repr__(self):
        return "Nº: {}, produto: {}, {} und(s) e valor de: {}€".format(self.id_compra, self.nome_produto, self.quantidade, self.valor_total)

class Venda(db.Model):
    __tablename__ = "vendas"
    id_venda = db.Column(db.Integer, primary_key=True)
    id_cliente = db.Column(db.Integer, db.ForeignKey('usuarios.id_usuario'))
    data_venda = db.Column(db.Date)
    nome_produto = db.Column(db.String, db.ForeignKey('produtos.nome_produto'))
    preco_iva = db.Column(db.Float, db.ForeignKey('produtos.preco_iva'))
    quantidade = db.Column(db.Integer)
    desconto = db.Column(db.Float)
    valor_total = db.Column(db.Float)

    produto = db.relationship('Produtos', foreign_keys=nome_produto)
    cliente = db.relationship('Usuarios', foreign_keys=id_cliente)

    def __init__(self, id_cliente, data_venda, nome_produto, preco_iva, quantidade):
        self.id_cliente = id_cliente
        self.data_venda = data_venda
        self.nome_produto = nome_produto
        self.preco_iva = preco_iva
        self.quantidade = quantidade
        self.desconto = 0.0

    def __repr__(self):
        return "Nº de pedido: {}, produto: {}, {} und(s) e no valor de {}€".format(self.id_venda, self.nome_produto,self.quantidade, self.preco_iva)


    
#LISTAS DE USUÁRIOS, PRODUTOS E INFORMAÇÕES PARA O BANCO DE DADOS

lista_de_usuarios = [Usuarios("Cliente", "joanapessoa@email.com", "joana1", "Joana Pessoa", 123456789, 987654321, "Rua Central, nº 3, Coimbra-Portugal"),
                     Usuarios("Fornecedor", "titanprodutos@email.com", "titan1", "Titan Produtos Especializados", 896745341, 675432123, "Avenida do Porto, nº 123, Coimbra-Portugal"),
                     Usuarios("Administrador", "luismiranda@email.com", "luis1", "Luis Miranda", 234567891, 198765423, "Rua Centenária, nº 25, Coimbra-Portugal"),
                    ]

lista_de_produtos = [Produtos("Tablet Apple", "Cor branca, tela 10'", 1000, 500, 5, "A1", 3),
                     Produtos("JBL GO", "Cor preta, 330g", 50, 25, 10, "B1", 3),
                     Produtos("Portátil Asus", "Cor cinzenta, tela 17'", 800, 400, 10, "A1", 3),
                     Produtos("Telemóvel Samsung", "Cor preta, 8gb", 600, 300, 5, "B1", 3),
                     Produtos("Mochila + Rato HP", "Cor preta", 40, 20, 10, "A1", 3)
                     ]



#FUNÇÕES


#Função para calcular o valor total da compra do cliente

def calcular_valor_total(preco_iva, quantidade):
        valor_total_cliente = (preco_iva * quantidade)
        return valor_total_cliente   


#Função para calcular o valor total da compra do administrador

def calcular_valor_total_adm(preco_compra, quantidade):
        valor_total_adm = (preco_compra * quantidade)
        return valor_total_adm 


#Função para calcular a quantidade em stock

def calcular_stock(stock, quantidade):
    stock_inicial = stock
    stock_final = (stock_inicial - quantidade)
    return stock_final



#CRIAÇÃO DO BANCO DE DADOS

with app.app_context():
    db.create_all() #Criação das tabelas
    #db.session.add_all(lista_de_usuarios) #Criação da lista de usuários
    #db.session.add_all(lista_de_produtos) #Criação da lista de produtos
    db.session.commit()



#LOGIN E AUTENTICAÇÃO PARA OS TIPOS DE USUÁRIOS

#Rota de login

@app.route('/')
def home():
    return render_template("login.html")


#Rota de autenticação dos usuários de acordo com o tipo, email e senha.

@app.route('/autenticar', methods=['POST'])
def autenticar():
    consulta_produtos = db.session.query(Produtos)
    email = request.form.get('email')
    senha = request.form.get('senha')
    consulta_usuarios = db.session.query(Usuarios)
    consulta_usuarios = consulta_usuarios.filter_by(email=email, senha=senha).first()
    if consulta_usuarios is not None:
        id_usuario = consulta_usuarios.id_usuario
        if consulta_usuarios.tipo == "Administrador":
            return redirect(url_for('adicionar_produto_adm', id_usuario=id_usuario))
        elif consulta_usuarios.tipo == "Fornecedor":
            return render_template("fornecedor.html", consulta_produtos=consulta_produtos)
        elif consulta_usuarios.tipo == "Cliente":
            return redirect(url_for('adicionar_produto', id_usuario=id_usuario))
    else:
        flash("E-mail ou senha inválido(s).")
        return redirect("/")




#ROTAS CLIENTES

#Rota carrinho cliente

@app.route('/cart')
def cart():
    if 'cart' not in session:
        session['cart'] = []
    return render_template('carrinhocliente.html', cart=session['cart'])


#Rota onde o cliente compra os produtos e os adiciona em um carrinho
#Também controla o estoque
  


@app.route('/adicionar_produto/<id_usuario>', methods=['GET', 'POST'])
def adicionar_produto(id_usuario):
    consulta_produtos = [
        {'nome_produto': 'Tablet Apple', 'imagem': 'tablet_apple.jpg', 'descricao_produto': 'Cor branca, tela 10', 'preco_iva': '1000'},
        {'nome_produto': 'JBL GO', 'imagem': 'jbl_go.jpg', 'descricao_produto': 'Cor preta, 330g', 'preco_iva': '50 '},
        {'nome_produto': 'Portátil Asus', 'imagem': 'portatil_asus.jpg', 'descricao_produto': 'Cor cinzenta, tela 17', 'preco_iva': '800 '},
        {'nome_produto': 'Telemóvel Samsung', 'imagem': 'telemovel_samsung.jpg', 'descricao_produto': 'Cor preta, 8gb', 'preco_iva': '600 '},
        {'nome_produto': 'Mochila + Rato HP', 'imagem': 'mochila_+_rato.jpg', 'descricao_produto': 'Cor preta', 'preco_iva': '40 '},
    ]

    if request.method != 'POST':
        return render_template("cliente.html", id_usuario=id_usuario, consulta_produtos=consulta_produtos)
    else:
        produto = request.form.get('nome_produto')
        quantidade = request.form.get('quantidade')
        consulta_preco = db.session.query(Produtos.preco_iva).filter_by(nome_produto=produto).first()
        data_venda = datetime.today()
        if consulta_preco is not None:
            preco_iva = consulta_preco.preco_iva
            pedido = Venda(id_cliente=id_usuario, data_venda=data_venda, nome_produto=produto, quantidade=quantidade, preco_iva=preco_iva)
            db.session.add(pedido)
            db.session.commit()
            valor_venda = calcular_valor_total(pedido.preco_iva, pedido.quantidade)
            pedido.valor_venda = valor_venda
            db.session.add(pedido)
            db.session.commit()
            stock = calcular_stock(pedido.produto.qtd_stock, int(quantidade))
            pedido.produto.qtd_stock = stock
            db.session.add(pedido.produto)
            db.session.commit()
            flash('Produto adicionado com sucesso!', 'success')
            return redirect(url_for('adicionar_produto', id_usuario=id_usuario))
        else:
            flash('Erro. Escolha o produto e a quantidade.', 'error')
            return render_template("cliente.html", id_usuario=id_usuario, consulta_produtos=consulta_produtos)



   
#Rota para criar o carrinho do cliente

@app.route('/carrinho/<id_usuario>', methods=['GET', 'POST'])
def carrinho(id_usuario):
    global pedido
    consulta_produtos = db.session.query(Produtos)
    pedido_total = db.session.query(Venda).filter_by(id_cliente=id_usuario)
    if pedido_total is not None:
        for pedido in pedido_total:
            valor_total_cliente = calcular_valor_total(pedido.preco_iva, pedido.quantidade)
            pedido.valor_total = valor_total_cliente
            db.session.add(pedido)
            db.session.commit()
    if request.method != 'POST':
        return render_template("carrinhocliente.html", id_usuario=id_usuario, pedido_total=pedido_total, consulta_produtos=consulta_produtos)
    else:
        return render_template("carrinhocliente.html", id_usuario=id_usuario, pedido_total=pedido_total, consulta_produtos=consulta_produtos)


#Rota para excluir um produto do carrinho do cliente

@app.route('/excluir_produto/<id_usuario>/<id_venda>', methods=['GET', 'POST'])
def excluir_pedido(id_usuario, id_venda):
    pedidos = db.session.query(Venda).filter_by(id_venda=id_venda).first()
    produtos_stock = db.session.query(Produtos).join(Venda, Produtos.nome_produto == Venda.nome_produto).filter_by(nome_produto=pedidos.nome_produto)
    if pedidos and produtos_stock is not None:
        for produtos in produtos_stock:
            stock = pedidos.quantidade + int(produtos.qtd_stock)
            produtos.qtd_stock = stock
            db.session.add(produtos)
            db.session.commit()
        db.session.delete(pedidos)
        db.session.commit()
    return redirect(url_for('carrinho', id_usuario=id_usuario, id_venda=id_venda))


#Rota para alterar o pedido do carrinho do cliente

@app.route('/alterar_pedido/<id_usuario>/<id_venda>/<nova_quantidade>', methods=['GET'])
def alterar_pedido(id_usuario, id_venda, nova_quantidade):
    pedidos = db.session.query(Venda).filter_by(id_venda=id_venda).first()
    produto_stock = db.session.query(Produtos).filter_by(nome_produto=pedidos.nome_produto).first()
    if pedidos  and produto_stock is not None:
        if int(pedidos.quantidade) > int(nova_quantidade):
            stock = (int(pedidos.quantidade) - int(nova_quantidade)) + produto_stock.qtd_stock
        else:
            stock = (int(nova_quantidade) - int(pedidos.quantidade)) -(produto_stock.qtd_stock)
            stock = (stock * -1)
        pedidos.quantidade = nova_quantidade
        db.session.add(pedidos)
        db.session.commit()
        produto_stock.qtd_stock = stock
        db.session.add(produto_stock)
        db.session.commit()
    return redirect(url_for('carrinho', id_usuario=id_usuario, id_venda=id_venda))


#Rota para confirmar a compra do cliente

@app.route('/confirmar_compra', methods=['POST'])
def confirmar_compra():
    return render_template('fimcompracliente.html')


#Rota para o cliente sair e também para retornar ao login

@app.route('/sair', methods=['GET'])
def sair():
    session.clear()
    return render_template('login.html')



#ROTAS ADMINISTRADOR


#Rota para o administrador realizar compras para atualizar o estoque e adicionar os produtos ao carrinho

# Rota para adicionar produto pelo administrador
@app.route('/adicionar_produto_adm/<id_usuario>', methods=['GET', 'POST'])
def adicionar_produto_adm(id_usuario):
    consulta_produtos = db.session.query(
    Produtos.id_produto,
    Produtos.nome_produto,
    Produtos.descricao_produto,
    Produtos.preco_compra,
    Produtos.preco_iva,  
    Produtos.id_fornecedor,
    Produtos.qtd_stock,
    Produtos.lugar_armazem,  
    )

    consulta_produtos = [
        {
            'id_produto': str(produto.id_produto),
            'nome_produto': produto.nome_produto,
            'descricao_produto': produto.descricao_produto,
            'preco_compra': produto.preco_compra,
            'preco_iva': produto.preco_iva, 
            'id_fornecedor': produto.id_fornecedor,
            'qtd_stock': produto.qtd_stock,
            'lugar_armazem': produto.lugar_armazem 
        }
        for produto in consulta_produtos
    ]
    
    estoque_baixo_limite = 10  # Defina o limite de estoque baixo conforme necessário
    lista_baixo_stock = [produto for produto in consulta_produtos if produto['qtd_stock'] < estoque_baixo_limite]
    
    if request.method != 'POST':
        return render_template("administrador.html", id_usuario=id_usuario, consulta_produtos=consulta_produtos, lista_baixo_stock=lista_baixo_stock)
    else:
        produto = request.form.get('nome_produto')
        quantidade = request.form.get('quantidade')
        consulta_preco = db.session.query(Produtos.preco_compra, Produtos.id_fornecedor).filter_by(nome_produto=produto).first()
        data_compra = datetime.today()
        if consulta_preco is not None:
            preco_compra = consulta_preco.preco_compra
            id_fornecedor = consulta_preco.id_fornecedor
            pedido = Compra(id_administrador=id_usuario, data_compra=data_compra, nome_produto=produto, quantidade=quantidade, preco_compra=preco_compra, id_fornecedor=id_fornecedor)
            db.session.add(pedido)
            db.session.commit()
            return redirect(url_for('adicionar_produto_adm', id_usuario=id_usuario))
        else:
            "Erro. Escolha o produto e a quantidade."
            return render_template("administrador.html", id_usuario=id_usuario, consulta_produtos=consulta_produtos, lista_baixo_stock=lista_baixo_stock, flash_message="Erro. Escolha o produto e a quantidade.")



# Defina a nova rota para a página "Dados Clientes e Fornecedor"
@app.route('/dados_clientes_fornecedor')
def dados_clientes_fornecedor():
    # Dados do fornecedor
    dados_fornecedor = {
        'nome': 'Titan Equipamentos Especializados',
        'nif': '896745341',
        'contacto': '675432123',
        'morada': 'Avenida do Porto, nº 123, Coimbra-Portugal'
    }
    
    # Dados dos clientes ativos
    dados_clientes = [
        {
            'id': '1',
            'nome': 'Joana Pessoa',
            'nif': '123456789',
            'contacto': '987654321',
            'morada': 'Rua Central, nº 3, Coimbra-Portugal'
        },
        {
            'id': '2',
            'nome': 'Jose Ortega',
            'nif': '134567234',
            'contacto': '123456789',
            'morada': 'Rua da Boa Hora, nº 56, Coimbra-Portugal'
        }
    ]
    
    # Renderize a página com os dados
    return render_template('dados_clientes_fornecedor.html', dados_fornecedor=dados_fornecedor, dados_clientes=dados_clientes)


# Rota para carrinho do administrador
@app.route('/carrinho_adm/<id_usuario>', methods=['GET', 'POST'])
def carrinho_adm(id_usuario):
    global pedido
    consulta_produtos = db.session.query(Produtos)
    pedido_total_adm = db.session.query(Compra).filter_by(id_administrador=id_usuario)
    
    if pedido_total_adm is not None:
        for pedido in pedido_total_adm:
            valor_total_adm = calcular_valor_total_adm(pedido.preco_compra, pedido.quantidade)
            pedido.valor_total = valor_total_adm
            db.session.add(pedido)
            db.session.commit()
        
        flash("Produto adicionado ao carrinho com sucesso!", "success")  # Adiciona a mensagem flash
        
        return render_template("carrinhoadm.html", id_usuario=id_usuario, pedido_total_adm=pedido_total_adm, consulta_produtos=consulta_produtos)
    else:
        return render_template("carrinhoadm.html", id_usuario=id_usuario, pedido_total_adm=pedido_total_adm, consulta_produtos=consulta_produtos)



#Rota para excluir produtos do carrinho do administrador

@app.route('/excluir_produto_adm/<id_usuario>/<id_compra>', methods=['GET', 'POST'])
def excluir_pedido_adm(id_usuario, id_compra):
    pedidos = db.session.query(Compra).filter_by(id_compra=id_compra).first()
    produtos_stock = db.session.query(Produtos).join(Compra, Produtos.nome_produto == Compra.nome_produto).filter_by(nome_produto=pedidos.nome_produto)
    if pedidos and produtos_stock is not None:
        for produtos in produtos_stock:
            stock = pedidos.quantidade + int(produtos.qtd_stock)
            produtos.qtd_stock = stock
            db.session.add(produtos)
            db.session.commit()
        db.session.delete(pedidos)
        db.session.commit()
    return redirect(url_for('carrinho_adm', id_usuario=id_usuario))


#Rota para alterar o pedido do carrinho do administrador

@app.route('/alterar_pedido_adm/<id_usuario>/<id_compra>/<nova_quantidade>', methods=['GET'])
def alterar_pedido_adm(id_usuario, id_compra, nova_quantidade):
    pedidos = db.session.query(Compra).filter_by(id_compra=id_compra).first()
    produto_stock = db.session.query(Produtos).filter_by(nome_produto=pedidos.nome_produto).first()
    if pedidos and produto_stock is not None:
        if int(pedidos.quantidade) > int(nova_quantidade):
            stock = (int(pedidos.quantidade) - int(nova_quantidade)) + produto_stock.qtd_stock
        else:
            stock = (int(nova_quantidade) - int(pedidos.quantidade)) - produto_stock.qtd_stock
            stock = (stock * -1)
        pedidos.quantidade = nova_quantidade
        db.session.add(pedidos)
        db.session.commit()
        produto_stock.qtd_stock = stock
        db.session.add(produto_stock)
        db.session.commit()
    return redirect(url_for('carrinho_adm', id_usuario=id_usuario, id_compra=id_compra))


#Rota para confirmar a compra do administrador

@app.route('/confirmar_compra_adm', methods=['POST'])
def confirmar_compra_adm():
    return render_template('fimcompraadm.html')


#Rota para sair da página do administrador, fazendo o logout

@app.route('/sair_adm', methods=['GET'])
def exit_adm():
    return render_template('login.html')



#ROTAS DE GRÁFICOS


#Rota para gerar o gráfico de compras na página do administrador
#Ou seja, o que ele comprou do Fornecedor

@app.route('/grafico_compras')
def grafico_compras():
    produtos = db.session.query(Compra.nome_produto, db.func.sum(Compra.quantidade)).group_by(Compra.nome_produto).all()
    produtos = dict(produtos)
    nomes = list(produtos.keys())
    quantidades = list(produtos.values())
    
    cores = ['teal', 'navy', 'orange', 'blue', 'purple']

  
    lista_cores = [cores[i % len(cores)] for i in range(len(nomes))] 

    plt.figure(figsize=(7, 6.5))
    plt.bar(nomes, quantidades, color=lista_cores)
    plt.xlabel('Produtos', fontweight='bold')
    plt.ylabel('Quantidade', fontweight='bold')
    plt.xticks(rotation = 10) 
    plt.title('Gráfico de Custo', fontweight='bold')
    plt.gca().set_facecolor('#f0f0f0')

    #plt.savefig('static/img_graficos/grafico_compras.png')

    return render_template('grafico_compras.html')

#Rota para gerar gráfico de vendas na página do fornecedor
#Ou seja, o que o fornecedor vendeu ao Administrador

@app.route('/grafico_vendas_fornecedor')
def grafico_vendas_fornecedor():
    produtos = db.session.query(Compra.nome_produto, db.func.sum(Compra.quantidade)).group_by(Compra.nome_produto).all()
    produtos = dict(produtos)
    nomes = list(produtos.keys())
    quantidades = list(produtos.values())

    # Definir cores para cada barra
    cores = ['navy', 'orange', 'blue', 'purple', 'teal']
    lista_cores = [cores[i % len(cores)] for i in range(len(nomes))]

    plt.figure(figsize=(7,6))
    # Criar o gráfico de barras
    plt.bar(nomes, quantidades, color=lista_cores, alpha=0.5)
    plt.xlabel('Produtos', fontweight='bold')
    plt.ylabel('Quantidade', fontweight='bold')
    plt.xticks(rotation=8)
    plt.title('Gráfico de Vendas', fontweight='bold')
    plt.gca().set_facecolor('#f0f0f0')

    #plt.savefig('static/img_graficos/grafico_vendas_fornecedor.png')

    return render_template('grafico_vendas_fornecedor.html')

#Rota para gerar o gráfico de vendas para o administrador
#Ou seja, o que os clientes compraram na Loja

@app.route('/grafico_vendas')
def grafico_vendas():
    vendas = db.session.query(Venda.nome_produto, db.func.sum(Venda.quantidade)).group_by(Venda.nome_produto).all()
    vendas = dict(vendas)
    produtos = list(vendas.keys())
    quantidades = list(vendas.values())

    cores = ['orange', 'blue', 'navy', 'purple', 'teal']
    lista_cores = [cores[i % len(cores)] for i in range(len(produtos))]

    plt.figure(figsize=(7, 6)) # tamanho da figura
    plt.bar(produtos, quantidades, color=lista_cores) # adicionando as cores à lista de cores
    plt.xlabel('Produtos', fontweight='bold')
    plt.ylabel('Quantidade', fontweight='bold')
    plt.xticks(rotation=8)
    plt.title('Gráfico de Vendas', fontweight='bold')
    plt.gca().set_facecolor('#f0f0f0')

    #plt.savefig('static/img_graficos/grafico_vendas.png')

    return render_template('grafico_vendas.html')



#Função para calcular o lucro de acordo com as vendas para gerar o gráfico de lucros para o administrador

def calcular_lucro(preco_iva, preco_compra, quantidade):
    custo_total = preco_compra * quantidade
    valor_total = calcular_valor_total(preco_iva, quantidade)
    lucro = valor_total - custo_total
    return lucro


#Rota para gerar o gráfico de lucro para o administrador

@app.route('/grafico_lucro')
def grafico_lucro():
    vendas = Venda.query.all()

    lucros = []
    for venda in vendas:
        preco_iva = venda.preco_iva  #Preço com IVA da venda
        preco_compra = venda.produto.preco_compra  #Preço de compra do produto relacionado à venda
        quantidade = venda.quantidade
        
        lucro = calcular_lucro(preco_iva, preco_compra, quantidade)
        lucros.append(lucro)

    plt.figure(figsize=(7, 6))
    plt.fill_between(range(1, len(lucros) + 1), lucros, color='green', alpha=0.3)
    plt.xlabel('Venda', fontweight='bold')
    plt.ylabel('Lucro', fontweight='bold')
    plt.title('Lucro de Vendas', fontweight='bold')
    plt.gca().set_facecolor('#f0f0f0')

    #plt.savefig('static/img_graficos/grafico_lucro.png')  #Salva o gráfico em um arquivo

    return render_template('grafico_lucro.html')


#Rota para o Administrador voltar para a página inicial do Administrador

@app.route('/voltar_administrador')
def voltar_administrador():
    consulta_produtos = db.session.query(Produtos)
    return render_template('administrador.html', consulta_produtos=consulta_produtos)


#Rota para o Fornecedor voltar para a página inicial do Fornecedor

@app.route('/voltar_fornecedor', methods=['GET', 'POST'])
def voltar_fornecedor():
    if request.method == 'POST':
        # Lógica para lidar com a requisição POST
        consulta_produtos = db.session.query(Produtos)
        return render_template('fornecedor.html', consulta_produtos=consulta_produtos)
    else:
        # Lógica para lidar com a requisição GET
        consulta_produtos = db.session.query(Produtos)
        return render_template('fornecedor.html', consulta_produtos=consulta_produtos)

#Rota para o Cliente voltar para a página inicial do Cliente

@app.route('/voltar_cliente')
def voltar_cliente():
    consulta_produtos = db.session.query(Produtos)
    return render_template('cliente.html', consulta_produtos=consulta_produtos)


#Rota para o Administrador acessar a página do Cliente de maneira muito simples, sem de facto acesso.

@app.route('/acessar_pag_cliente/<id_usuario>')
def acessar_pag_cliente(id_usuario):
    consulta_produtos = db.session.query(Produtos)
    return redirect(url_for('adicionar_produto', id_usuario=id_usuario, consulta_produtos=consulta_produtos))

#Rota para o Administrador acessar a página do fornecedor de maneira muito simples, sem de facto acesso.

@app.route('/acessar_pag_fornecedor')
def acessar_pag_fornecedor():
    consulta_produtos = db.session.query(Produtos)
    return render_template('fornecedor.html', consulta_produtos=consulta_produtos)

#Rota para o Administrador voltar as compras depois de ter finalizado a compra
@app.route('/voltar_compras/<id_usuario>', methods=['GET'])
def voltar_compras(id_usuario):
    return redirect(url_for('adicionar_produto', id_usuario=id_usuario))







#O debug inicia a app
if __name__ == '__main__':
    app.run(debug=True)