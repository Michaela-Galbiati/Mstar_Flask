from flask import Flask, render_template, jsonify, request, send_file
from flask_cors import CORS
from flask_mysqldb import MySQL
from werkzeug.security import generate_password_hash, check_password_hash
import logging
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle
import io
from datetime import datetime
from flask_cors import CORS
import time

app = Flask(__name__)
CORS(app)  # Permitindo solicitações de origens cruzadas

# Configurações do banco de dados MySQL
app.config['MYSQL_HOST'] = 'sistemaro.mysql.dbaas.com.br'
app.config['MYSQL_USER'] = 'sistemaro'
app.config['MYSQL_PASSWORD'] = 'TW5brJ8Z!39X51'
app.config['MYSQL_DB'] = 'sistemaro'

# Inicialização da extensão MySQL
mysql = MySQL(app)

@app.route('/api/time')
def get_current_time():
    return {'time': time.time()}

@app.route('/add_mercadoria', methods=['POST'])
def add_mercadoria():



    data = request.get_json()
    nome = data.get('nome')
    fabricante = data.get('fabricante')
    numero_registro = data.get('numero_registro')
    tipo = data.get('tipo')
    descricao = data.get('descricao')

    # Verificar se todos os campos foram fornecidos
    if not nome or not fabricante or not numero_registro or not tipo or not descricao:
        return jsonify({'error': 'Missing nome, fabricante, numero_registro, tipo, or descricao'}), 400

    # Inserir a mercadoria no banco de dados
    cur = mysql.connection.cursor()
    cur.execute("INSERT INTO Mercadorias (nome, fabricante, numero_registro, tipo, descricao) VALUES (%s, %s, %s, %s, %s)", (nome, fabricante, numero_registro, tipo, descricao))
    mysql.connection.commit()
    cur.close()

    return jsonify({'message': 'Mercadoria added successfully'}), 201


@app.route('/add_entrada', methods=['POST'])
def add_entrada():

    data = request.get_json()
    nome_mercadoria = data.get('nome_mercadoria')
    quantidade = data.get('quantidade')
    data_hora = data.get('data_hora')
    local = data.get('local')

    # Verificar se todos os campos foram fornecidos
    if not nome_mercadoria or not quantidade or not data_hora or not local:
        return jsonify({'error': 'Missing nome_mercadoria, quantidade, data_hora, or local'}), 400

    try:
        # Iniciar uma transação para garantir atomicidade das operações
        cur = mysql.connection.cursor()

        # Inserir a entrada no banco de dados
        cur.execute("INSERT INTO Entrada (nome_mercadoria, quantidade, data_hora, local) VALUES (%s, %s, %s, %s)", (nome_mercadoria, quantidade, data_hora, local))

        # Atualizar a quantidade total de entrada da mercadoria na tabela de Mercadorias
        cur.execute("UPDATE Mercadorias SET quantidade_total_entrada = quantidade_total_entrada + %s WHERE nome = %s", (quantidade, nome_mercadoria))

        # Atualizar a disponibilidade da mercadoria
        cur.execute("UPDATE Mercadorias SET disponibilidade = quantidade_total_entrada - quantidade_total_saida WHERE nome = %s", (nome_mercadoria,))

        # Obtendo a data e hora atual
        data_hora_atual = datetime.now()

        # Obtendo o mês e o ano a partir da data e hora atual
        mes_ano_atual = data_hora_atual.strftime('%b/%Y')

       # Inserir na tabela QuantidadeTotal para entradas
        cur.execute("""
            INSERT INTO QuantidadeTotal (nome_mercadoria, mes_ano, quantidade_total_entradas)
            SELECT nome_mercadoria, CONCAT(YEAR(data_hora), '-', LPAD(MONTH(data_hora), 2, '0')) AS mes_ano, SUM(quantidade) AS quantidade_total_entradas
            FROM Entrada
            GROUP BY nome_mercadoria, YEAR(data_hora), MONTH(data_hora)
            ON DUPLICATE KEY UPDATE quantidade_total_entradas = VALUES(quantidade_total_entradas)
        """)
        cur.execute("""
            UPDATE QuantidadeTotal
            SET disponibilidade = IFNULL(quantidade_total_entradas, 0) - IFNULL(quantidade_total_saidas, 0)
        """)


        # Confirmar as alterações na transação
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Entrada added successfully'}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/add_saida', methods=['POST'])
def add_saida():
    # Obter os dados do corpo da requisição
    data = request.get_json()
    nome_mercadoria = data.get('nome_mercadoria')
    quantidade = data.get('quantidade')
    data_hora = data.get('data_hora')
    local = data.get('local')

    # Verificar se todos os campos foram fornecidos
    if not nome_mercadoria or not quantidade or not data_hora or not local:
        return jsonify({'error': 'Missing nome_mercadoria, quantidade, data_hora, or local'}), 400

    try:
        # Iniciar uma transação para garantir atomicidade das operações
        cur = mysql.connection.cursor()

        # Inserir a saída no banco de dados
        cur.execute("INSERT INTO Saida (nome_mercadoria, quantidade, data_hora, local) VALUES (%s, %s, %s, %s)", (nome_mercadoria, quantidade, data_hora, local))

        # Atualizar a quantidade total de saída da mercadoria na tabela de Mercadorias
        cur.execute("UPDATE Mercadorias SET quantidade_total_saida = quantidade_total_saida + %s WHERE nome = %s", (quantidade, nome_mercadoria))

        # Atualizar a disponibilidade da mercadoria
        cur.execute("UPDATE Mercadorias SET disponibilidade = quantidade_total_entrada - quantidade_total_saida WHERE nome = %s", (nome_mercadoria,))

        # Obtendo a data e hora atual
        data_hora_atual = datetime.now()

        # Obtendo o mês e o ano a partir da data e hora atual
        mes_ano_atual = data_hora_atual.strftime('%b/%Y')

        # Inserir na tabela QuantidadeTotal para saídas
        cur.execute("""
            INSERT INTO QuantidadeTotal (nome_mercadoria, mes_ano, quantidade_total_saidas)
            SELECT nome_mercadoria, CONCAT(YEAR(data_hora), '-', LPAD(MONTH(data_hora), 2, '0')) AS mes_ano, SUM(quantidade) AS quantidade_total_saidas
            FROM Saida
            GROUP BY nome_mercadoria, YEAR(data_hora), MONTH(data_hora)
            ON DUPLICATE KEY UPDATE quantidade_total_saidas = VALUES(quantidade_total_saidas)
        """)
        cur.execute("""
            UPDATE QuantidadeTotal
            SET disponibilidade = IFNULL(quantidade_total_entradas, 0) - IFNULL(quantidade_total_saidas, 0)
        """)

        # Confirmar as alterações na transação
        mysql.connection.commit()
        cur.close()

        return jsonify({'message': 'Saida added successfully'}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/mercadorias', methods=['GET'])
def get_mercadorias():
    cur = mysql.connection.cursor()
    cur.execute("SELECT nome FROM Mercadorias")
    mercadorias = cur.fetchall()
    cur.close()
    return jsonify(mercadorias)




@app.route('/entradan', methods=['GET'])
def get_entradan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT nome_mercadoria FROM Entrada ORDER BY id DESC LIMIT 5")
    entradan = cur.fetchall()
    cur.close()
    return jsonify(entradan)



@app.route('/entradaq', methods=['GET'])
def get_entradaq():
    cur = mysql.connection.cursor()
    cur.execute("SELECT quantidade FROM Entrada ORDER BY id DESC LIMIT 5")
    entradaq = cur.fetchall()
    cur.close()
    return jsonify(entradaq)

@app.route('/entradadh', methods=['GET'])
def get_entradadh():
    cur = mysql.connection.cursor()
    cur.execute("SELECT data_hora FROM Entrada ORDER BY id DESC LIMIT 5")
    entradadh = cur.fetchall()
    cur.close()
    return jsonify(entradadh)


@app.route('/entradal', methods=['GET'])
def get_entradal():
    cur = mysql.connection.cursor()
    cur.execute("SELECT local FROM Entrada ORDER BY id DESC LIMIT 5")
    entradal = cur.fetchall()
    cur.close()
    return jsonify(entradal)


@app.route('/saidan', methods=['GET'])
def get_saidan():
    cur = mysql.connection.cursor()
    cur.execute("SELECT nome_mercadoria FROM Saida ORDER BY id DESC LIMIT 5")
    saidan = cur.fetchall()
    cur.close()
    return jsonify(saidan)



@app.route('/saidaq', methods=['GET'])
def get_saidaq():
    cur = mysql.connection.cursor()
    cur.execute("SELECT quantidade FROM Saida ORDER BY id DESC LIMIT 5")
    saidaq = cur.fetchall()
    cur.close()
    return jsonify(saidaq)

@app.route('/saidadh', methods=['GET'])
def get_saidadh():
    cur = mysql.connection.cursor()
    cur.execute("SELECT data_hora FROM Saida ORDER BY id DESC LIMIT 5")
    saidadh = cur.fetchall()
    cur.close()
    return jsonify(saidadh)


@app.route('/saidal', methods=['GET'])
def get_saidal():
    cur = mysql.connection.cursor()
    cur.execute("SELECT local FROM Saida ORDER BY id DESC LIMIT 5")
    saidal = cur.fetchall()
    cur.close()
    return jsonify(saidal)


@app.route('/soma_quantidade_entradas', methods=['GET'])
def soma_quantidade_entradas():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT SUM(quantidade) AS soma_quantidade FROM Entrada")
        soma_quantidade = cursor.fetchone()[0]  # Obtém o resultado da consulta
        return jsonify({"soma_quantidade": soma_quantidade})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/soma_quantidade_entradasaida', methods=['GET'])
def soma_quantidade_entradasaida():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT SUM(quantidade) AS soma_quantidade FROM Saida")
        soma_quantidade = cursor.fetchone()[0]  # Obtém o resultado da consulta
        return jsonify({"soma_quantidade": soma_quantidade})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/diferenca_entradas_saidas', methods=['GET'])
def diferenca_entradas_saidas():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT SUM(quantidade) AS soma_entradas FROM Entrada")
        soma_entradas = cursor.fetchone()[0] or 0

        cursor.execute("SELECT SUM(quantidade) AS soma_saidas FROM Saida")
        soma_saidas = cursor.fetchone()[0] or 0

        diferenca = soma_entradas - soma_saidas

        return jsonify({"diferenca": diferenca})
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/quantidade_total', methods=['GET'])
def get_quantidade_total():
    nome_mercadoria = request.args.get('nome_mercadoria')
    try:
        cursor = mysql.connection.cursor()
        if nome_mercadoria:
            cursor.execute("""
                SELECT nome_mercadoria, mes_ano, quantidade_total_entradas, quantidade_total_saidas
                FROM QuantidadeTotal
                WHERE nome_mercadoria = %s
            """, (nome_mercadoria,))
        else:
            cursor.execute("""
                SELECT nome_mercadoria, mes_ano, quantidade_total_entradas, quantidade_total_saidas
                FROM QuantidadeTotal
            """)
        quantidades = cursor.fetchall()
        # Organizando os dados em uma lista de dicionários
        quantidades_data = []
        for row in quantidades:
            nome_mercadoria, mes_ano, quantidade_total_entradas, quantidade_total_saidas = row
            quantidades_data.append({
                'nome_mercadoria': nome_mercadoria,
                'mes_ano': mes_ano,
                'quantidade_total_entradas': quantidade_total_entradas,
                'quantidade_total_saidas': quantidade_total_saidas

            })
        return jsonify(quantidades_data)
    except Exception as e:
        return jsonify({"error": str(e)}), 500


@app.route('/quantidade_disponivel', methods=['GET'])
def quantidade_disponivel():
    nome_mercadoria = request.args.get('nome_mercadoria')
    if not nome_mercadoria:
        return jsonify({'error': 'Nome da mercadoria não fornecido'}), 400

    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT disponibilidade FROM Mercadorias WHERE nome = %s", (nome_mercadoria,))
        quantidade_disponivel = cursor.fetchone()[0]
        return jsonify({'quantidade_disponivel': quantidade_disponivel})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/quantidade_variedade_itens', methods=['GET'])
def quantidade_variedade_itens():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("SELECT COUNT(DISTINCT nome) AS quantidade_variedade_itens FROM Mercadorias")
        quantidade_variedade_itens = cursor.fetchone()[0]
        return jsonify({"quantidade_variedade_itens": quantidade_variedade_itens})
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/create_mensal', methods=['POST'])
def create_mensal():
    try:
        cursor = mysql.connection.cursor()

        # Calcular quantidade total de entradas por mês/ano
        cursor.execute("""
            SELECT mes_ano, SUM(quantidade_total_entradas) AS total_entradas
            FROM QuantidadeTotal
            GROUP BY mes_ano
        """)
        entradas_data = cursor.fetchall()

        # Calcular quantidade total de saídas por mês/ano
        cursor.execute("""
            SELECT mes_ano, SUM(quantidade_total_saidas) AS total_saidas
            FROM QuantidadeTotal
            GROUP BY mes_ano
        """)
        saidas_data = cursor.fetchall()

        # Inserir os dados na tabela Mensal
        for entry in entradas_data:
            mes_ano, total_entradas = entry
            cursor.execute("""
                INSERT INTO Mensal (mes_ano, quantidade_total_entradas, quantidade_total_saidas)
                VALUES (%s, %s, 0)
                ON DUPLICATE KEY UPDATE quantidade_total_entradas = VALUES(quantidade_total_entradas)
            """, (mes_ano, total_entradas))

        for entry in saidas_data:
            mes_ano, total_saidas = entry
            cursor.execute("""
                UPDATE Mensal
                SET quantidade_total_saidas = %s
                WHERE mes_ano = %s
            """, (total_saidas, mes_ano))

        mysql.connection.commit()
        cursor.close()

        return jsonify({'message': 'Mensal table created successfully'}), 201

    except Exception as e:
        return jsonify({"error": str(e)}), 500



@app.route('/mensal_data', methods=['GET'])
def get_mensal_data():
    try:
        cursor = mysql.connection.cursor()
        cursor.execute("""
            SELECT mes_ano, SUM(quantidade_total_entradas) AS quantidade_total_entradas, SUM(quantidade_total_saidas) AS quantidade_total_saidas
            FROM QuantidadeTotal
            GROUP BY mes_ano
        """)
        mensal_data = cursor.fetchall()
        # Organizando os dados em uma lista de dicionários
        mensal_data_list = []
        for row in mensal_data:
            mes_ano, quantidade_total_entradas, quantidade_total_saidas = row
            mensal_data_list.append({
                'mes_ano': mes_ano,
                'quantidade_total_entradas': quantidade_total_entradas,
                'quantidade_total_saidas': quantidade_total_saidas
            })
        return jsonify(mensal_data_list)
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route('/check_numero_registro', methods=['POST'])
def check_numero_registro():
    # Obter o número de registro da requisição
    numero_registro = request.json.get('numero_registro')

    # Verificar se o número de registro já existe no banco
    cur = mysql.connection.cursor()
    cur.execute("SELECT COUNT(*) FROM Mercadorias WHERE numero_registro = %s", (numero_registro,))
    count = cur.fetchone()[0]
    cur.close()

    if count > 0:
        return jsonify({'message': 'Número de registro já existe no banco'}), 400
    else:
        return jsonify({'message': 'Número de registro disponível'}), 200



if __name__ == '__main__':
    app.run(debug=True)
