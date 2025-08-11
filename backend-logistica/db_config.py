import mysql.connector

def conectar():
    return mysql.connector.connect(
        host="localhost",
        user="root",
        password="",  # ou sua senha do MySQL
        database="app logistica"
    )
