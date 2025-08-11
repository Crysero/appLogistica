from flask import Flask, request, jsonify
from flask_socketio import SocketIO, emit
from db_config import conectar
import uuid
from flask_cors import CORS

app = Flask(__name__)
CORS(app)
socketio = SocketIO(app, cors_allowed_origins="*")

# Carrinhos em memória (pode evoluir para banco)
carrinhos = {}

@app.route('/movimentacoes/id/<number:id>', methods=['GET'])
def get_produto_por_ean(id):
    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM movimentacoes WHERE id = %s", (id,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()
    return jsonify(produto)

@app.route('/carrinho/<string:chave>', methods=['GET'])
def get_carrinho(chave):
    return jsonify(carrinhos.get(chave, []))

@socketio.on('adicionar_produto')
def adicionar_produto(data):
    id = data['id']
    chave = data.get('chave') or str(uuid.uuid4())[:8]

    conexao = conectar()
    cursor = conexao.cursor(dictionary=True)
    cursor.execute("SELECT * FROM movimentacoes WHERE id = %s", (id,))
    produto = cursor.fetchone()
    cursor.close()
    conexao.close()

    if produto:
        carrinhos.setdefault(chave, []).append(produto)
        emit('carrinho_atualizado', {'chave': chave, 'produtos': carrinhos[chave]}, broadcast=True)
    else:
        emit('erro', {'mensagem': 'Produto não encontrado'})

if __name__ == '__main__':
    socketio.run(app, debug=True)
