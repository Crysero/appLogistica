from db_config import conectar

try:
    conexao = conectar()
    if conexao.is_connected():
        print("✅ Conexão com o banco de dados bem-sucedida!")
    else:
        print("❌ Falha na conexão com o banco.")
    conexao.close()
except Exception as e:
    print("⚠️ Erro ao conectar:", e)
