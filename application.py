import os

import requests
from flask import Flask, request, flash, render_template, session, redirect, url_for
from flask_session import Session
from sqlalchemy import create_engine
from sqlalchemy.orm import scoped_session, sessionmaker

app = Flask(__name__)

# Check for environment variable
if not os.getenv("DATABASE_URL"):
    raise RuntimeError("DATABASE_URL is not set")

# Configure session to use filesystem
app.config["SESSION_PERMANENT"] = False
app.config["SESSION_TYPE"] = "filesystem"
Session(app)

# Set up database
engine = create_engine(os.getenv("DATABASE_URL"))
db = scoped_session(sessionmaker(bind=engine))


# POR DEFINIÇÃO, O GET POR PADRÃO JÁ VEM HABILITADA NO MÉTODO DA ROTA
# REGISTRANDO UMA ROTA COM A FUNÇÃO @app.route(), o 1º parâmetro é caminho da rota e o 2º são os métodos
@app.route("/")
# DEFINIÇÃO DA FUNÇÃO (É A RESPOSTA DA REQUISIÇÃO)
def index():
    # RETORNO DA FUNÇÃO, RENDERIZAR = MOSTRAR/PROCESSAR O ARQUIVO (TRANSFORMAR O HTML NO RESULTADO FINAL, SENÃO IA APARECER O CÓDIGO EM SI)
    return render_template("index.html")


@app.route("/api")
def api():
    # API É A CAMADA QUE FAZ A LIGAÇÃO ENTRE O BANCO DE DADOS E O FRONT-END.
    # RES= RESPONSE =(RESPOSTA),(VARIÁVEL), REQUEST.GET =(REQUISIÇÃO GET = os parâmetros são passados no cabeçalho(sessão paara parametros) da requisição.Por isso, podem ser vistos pela URI.
    res = request.get("https://www.goodreads.com/book/review_counts.json",
                      params={"key": "vco3gX9ZLjJWyORdIO2Q", "isbns": "9781632168146"})
    return str(res.json())


# FAZ A REQUISIÇÃO E ARMAZENA A RESPOSTA PRA MOSTRAR NA TELA
# STR= CONVERTENDO PRA STRING P/ MOSTRAR NA TELA

@app.route("/teste")
def teste():
    # essa variável armazena o resultado do sql
    teste = db.execute("select * from client;").fetchone()
    # fetchone função que puxa quais resultados tu quer dessa consulta no banco, "one" puxa um resultado, "all" todos
    return str(teste.login)


# transformando em string o login, retorna "Ana" que é o login do db


# Registrando a rota, e aplicando os métodos get e post
@app.route("/registration", methods=["GET", "POST"])
def registration():
    # função da rota
    if request.method == "GET":  # entrar no /registration
        # se for feita uma requisição do método get
        return render_template("registration.html")
    # retorna a página de registro
    if request.method == "POST":  # preencher as informações e clicar no botão de envio
        # se for feita uma requisição do método post (envia informações ao servidor)
        try:
            # usa o try quando sabe que pode ocorrer um erro, por exemplo, puxar dados de um campo que ta vazio
            login_form = request.form.get(
                "login")  # uma requisição post para login e password é disparada assim que o botão é apertado para armazenar os dados no db
            password_form = request.form.get("password")  # extraindo esses dados de dentro do formulário
        except ValueError:
            # se der erro, "flash" mostra uma mensagem na tela e depois retorna para a página de registro
            flash("Erro ao cadastrar")
            return render_template("registration.html")
        # db.execute (armazenando comandos na fila)
        db.execute("INSERT INTO client (login, password) VALUES (:login, :password)",
                   {"login": login_form, "password": password_form})
        # o segundo parametro da função db.execute(é o que está entre {}) é um dicionário (diferente do da requisição) que faz a ligação entre as variáveis de dentro do comando sql(primeiro parâmetro) com as variáveis de fora(do formulário)
        #:login vai vira o "login" no dicionário, a função não reconhece a variável direto, tem que usar o dicionário
        #:login é uma variável, e "login" é uma chave.
        # estrutura do dicionário:
        # variavel "chave":valor ---> chave é identificador do valor
        flash("Registration sucessful!")

        db.commit()
        # vai fazer com que o db rode a lista de comandos dele
        return redirect(url_for("index"))


@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "GET":
        return render_template("login.html")
    if request.method == "POST":
        try:
            login = request.form.get("login")
            password = request.form.get("password")
        except ValueError:
            flash("Erro ao logar")
            return render_template("login.html")

        user = db.execute("SELECT *  FROM client where login = :login AND password = :password",
                          {"login": login, "password": password}).fetchone()

        if not user:
            flash("User or password incorrect.")
            return render_template("login.html")
        # sessão é uma variável global, usada pra guardar informação do login da pessoa (id e login) pra certificar que ela ta logada
        session["id"] = user.id
        session["login"] = user.login

        flash("You are logged in!")

        return redirect(url_for("index"))


@app.route("/logout")
def logout():
    if session.get("login"):
        flash("Logged out!")
        session.clear()
    else:
        flash("No user logged in!")
    return redirect(url_for("index"))


@app.route("/search", methods=["GET", "POST"])
def search():
    if not session.get("login"):
        return redirect(url_for("index"))
    if request.method == "GET":
        return render_template("search.html")

    if request.method == "POST":
        try:
            search = request.form.get("search")
        except ValueError:
            flash("Nothing Found")
            return render_template("search.html")

        books = db.execute("SELECT * from book where isbn ILIKE concat('%',:search,'%') or title ILIKE concat('%',:search,'%') or author ILIKE concat('%',:search,'%');",{"search": search}).fetchall()

        if not books:
            flash("No results")
            return redirect(url_for("search"))

        return render_template("search.html", books=books)
#VERIFICAÇÃO DOS LIVROS NO BANCO DE DADOS
#:search é o que vem do formulário
# ILIKE no lugar de = significa que se escrever algo parecido, a busca vai achar algo
# o primeiro books é o segundo parametro que uma função pode ter(opcional)sendo uma variável que tu vai enviar para o html
# o segundo é a variável que ta vindo do banco
