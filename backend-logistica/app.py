from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from flask_cors import CORS
from db_config import conectar
import uuid
import os

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Carrinhos em memória
carrinhos = {}

@app.route('/')
def home():
    return '🚀 Backend Logística está rodando!'

@app.route('/tudo', methods=['GET'])
def exibir_tudo():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)

    # 🔹 Movimentações
    cursor.execute("""
        SELECT m.*, mat.cod_material AS material, mat.ean, mat.texto_breve_material,
               f.descricao_fornecedor_principal AS descricao_fornecedor_principal
        FROM movimentacoes m
        LEFT JOIN materiais mat ON m.cod_material = mat.id
        LEFT JOIN fornecedores f ON m.cod_fornecedor = f.id
    """)
    movimentacoes = cursor.fetchall()

    # 🔹 Materiais
    cursor.execute("SELECT * FROM materiais")
    materiais = cursor.fetchall()

    # 🔹 Fornecedores
    cursor.execute("SELECT * FROM fornecedores")
    fornecedores = cursor.fetchall()

    cursor.close()
    conexao.close()

    return jsonify({
        "movimentacoes": movimentacoes,
        "carrinhos": carrinhos,
        "materiais": materiais,
        "fornecedores": fornecedores
    })

@app.route('/material', methods=['GET'])
def listar_materiais():
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM materiais")
    materiais = cursor.fetchall()
    cursor.close()
    conexao.close()
    return jsonify(materiais)

@app.route('/movimentacoes', methods=['GET'])
def consultar_movimentacoes():
    id = request.args.get('id')
    ean = request.args.get('ean')
    material = request.args.get('material')

    query = """
        SELECT mat.cod_material, mat.texto_breve_material, mat.ean,
           f.descricao_fornecedor_principal AS descricao_fornecedor_principal
    FROM materiais mat
    LEFT JOIN movimentacoes mov ON mov.cod_material = mat.id
    LEFT JOIN fornecedores f ON f.id = mov.cod_fornecedor
    WHERE 1=1
    """
    params = []

    if id:
        query += " AND mov.id = %s"
        params.append(id)
    if ean:
        query += " AND mat.ean = %s"
        params.append(ean)
    if material:
        query += " AND mat.cod_material = %s"
        params.append(material)

    query += " LIMIT 100"

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute(query, tuple(params))
    dados = cursor.fetchall()
    cursor.close()
    conexao.close()
    return jsonify(dados)

@app.route('/movimentacoes', methods=['POST'])
def criar_movimentacao():
    data = request.json
    cod_material = data.get('cod_material')
    cod_fornecedor = data.get('cod_fornecedor')
    quantidade = data.get('quantidade')
    tipo_movimento = data.get('tipo_movimento')
    data_entrada = data.get('data_entrada')

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        INSERT INTO movimentacoes (cod_material, cod_fornecedor, quantidade, tipo_movimento, data_entrada)
        VALUES (%s, %s, %s, %s, %s)
    """, (cod_material, cod_fornecedor, quantidade, tipo_movimento, data_entrada))
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'mensagem': 'Movimentação criada com sucesso'})

@app.route('/movimentacoes/<int:id>', methods=['PUT'])
def atualizar_movimentacao(id):
    data = request.json
    cod_material = data.get('cod_material')
    cod_fornecedor = data.get('cod_fornecedor')
    quantidade = data.get('quantidade')
    tipo_movimento = data.get('tipo_movimento')

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("""
        UPDATE movimentacoes
        SET cod_material = %s, cod_fornecedor = %s, quantidade = %s, tipo_movimento = %s
        WHERE id = %s
    """, (cod_material, cod_fornecedor, quantidade, tipo_movimento, id))
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'mensagem': 'Movimentação atualizada com sucesso'})

@app.route('/movimentacoes/<int:id>', methods=['DELETE'])
def deletar_movimentacao(id):
    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute("DELETE FROM movimentacoes WHERE id = %s", (id,))
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'mensagem': 'Movimentação deletada com sucesso'})

@app.route('/atualizar_fornecedor', methods=['POST'])
def atualizar_fornecedor():
    data = request.json
    fornecedor_id = data.get('fornecedor_id')
    ean = data.get('ean')
    material = data.get('material')

    if not fornecedor_id or (not ean and not material):
        return jsonify({'erro': 'fornecedor_id e (ean ou material) são obrigatórios'}), 400

    query = "UPDATE movimentacoes SET cod_fornecedor = %s WHERE "
    params = [fornecedor_id]

    if ean:
        query += "ean = %s"
        params.append(ean)
    elif material:
        query += "material = %s"
        params.append(material)

    conexao = conectar()
    cursor = conexao.cursor()
    cursor.execute(query, tuple(params))
    conexao.commit()
    cursor.close()
    conexao.close()
    return jsonify({'mensagem': 'Fornecedor atualizado com sucesso'})

@app.route('/carrinho/<string:chave>', methods=['GET'])
def get_carrinho(chave):
    return jsonify(carrinhos.get(chave, []))

@socketio.on('adicionar_produto')
def adicionar_produto(data):
    id = data['id']
    chave = data.get('chave') or str(uuid.uuid4())[:8]

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("""
        SELECT m.quantidade, m.tipo_movimento, m.data_entrada,
               mat.cod_material AS material, mat.texto_breve_material,
               f.descricao_fornecedor_principal AS descricao_fornecedor_principal
        FROM movimentacoes m
        LEFT JOIN materiais mat ON m.cod_material = mat.id
        LEFT JOIN fornecedores f ON m.cod_fornecedor = f.id
        WHERE m.id = %s
    """, (id,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()

    if produto:
        carrinhos.setdefault(chave, []).append(produto)
        emit('carrinho_atualizado', {'chave': chave, 'produtos': carrinhos[chave]}, broadcast=True)
    else:
        emit('erro', {'mensagem': 'Produto não encontrado'})

@app.route('/buscar_produto', methods=['POST'])
def buscar_produto():
    try:
        data = request.json
        cod_material = data.get('valor')

        if not cod_material:
            return jsonify({'erro': 'O código do material é obrigatório'}), 400

        query = """
                        SELECT mat.cod_material, mat.texto_breve_material, mat.ean,
                mov.descricao_fornecedor_principal as descricao
        FROM materiais mat
        LEFT JOIN movimentacoes mov ON mov.cod_material = mat.id
        LEFT JOIN fornecedores f ON f.id = mov.cod_fornecedor
        WHERE mat.cod_material = %s 
        LIMIT 1

        """

        conexao = conectar()
        cursor = conexao.cursor(dictionary=True)
        cursor.execute(query, (cod_material,))
        produto = cursor.fetchone()
        cursor.close()
        conexao.close()

        # 👇 Aqui você vai ver no terminal
        print("Resultado da query:", produto)

        if produto:
            return jsonify(produto)
        else:
            return jsonify({'erro': 'Produto não encontrado'}), 404

    except Exception as e:
        print("Erro no buscar_produto:", str(e))  # também mostra no terminal
        return jsonify({'erro': f'Erro interno: {str(e)}'}), 500



import os

if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5050))
    app.run(host="0.0.0.0", port=port)

