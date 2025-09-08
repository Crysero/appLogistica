import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="switchyard.proxy.rlwy.net",
        port=58196,  # Porta padrão do MySQL, número inteiro
        user="root",
        password="PxuHWEPWgGeTVamTiTBasShoPmKMpTNw",  # coloque a senha correta
        database="railway"  # evite espaços no nome do banco
    )
