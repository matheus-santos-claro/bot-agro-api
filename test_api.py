import requests
import json
import time

# URL base da API
BASE_URL = "http://localhost:8000"

def testar_api():
    """Testa todos os endpoints da API"""
    
    print("🧪 TESTANDO API DO BOT AGRÍCOLA")
    print("=" * 50)
    
    # Aguardar um pouco para garantir que o servidor iniciou
    print("⏳ Aguardando servidor iniciar...")
    time.sleep(3)
    
    # Teste 1: Endpoint raiz
    print("\n1️⃣ Testando endpoint raiz (GET /)...")
    try:
        response = requests.get(f"{BASE_URL}/", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            print("✅ Endpoint raiz funcionando!")
            print(f"Resposta: {json.dumps(response.json(), indent=2, ensure_ascii=False)}")
        else:
            print(f"❌ Erro no endpoint raiz: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro de conexão: {e}")
        print("💡 Certifique-se de que o servidor está rodando!")
        return
    
    # Teste 2: Status do sistema
    print("\n2️⃣ Testando status do sistema (GET /status)...")
    try:
        response = requests.get(f"{BASE_URL}/status", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Status funcionando!")
            print(f"Total de manuais: {result.get('total_manuais', 0)}")
            print(f"Status: {result.get('status', 'UNKNOWN')}")
            if result.get('total_manuais', 0) > 0:
                print("✅ Manuais carregados com sucesso!")
            else:
                print("⚠️ Nenhum manual foi carregado!")
        else:
            print(f"❌ Erro no status: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 3: Listar manuais
    print("\n3️⃣ Testando lista de manuais (GET /manuais)...")
    try:
        response = requests.get(f"{BASE_URL}/manuais", timeout=10)
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Lista de manuais funcionando!")
            print(f"Total: {result.get('total', 0)}")
            if result.get('manuais'):
                print("📚 Manuais disponíveis:")
                for manual in result['manuais'][:5]:  # Mostrar apenas os primeiros 5
                    print(f"  - {manual}")
                if len(result['manuais']) > 5:
                    print(f"  ... e mais {len(result['manuais']) - 5} manuais")
        else:
            print(f"❌ Erro na lista: {response.status_code}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    # Teste 4: Fazer pergunta
    print("\n4️⃣ Testando pergunta (POST /perguntar)...")
    try:
        pergunta_data = {
            "pergunta": "Me fale sobre tratores"
        }
        response = requests.post(
            f"{BASE_URL}/perguntar",
            json=pergunta_data,
            headers={"Content-Type": "application/json"},
            timeout=30  # Timeout maior para perguntas
        )
        print(f"Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print("✅ Pergunta funcionando!")
            print(f"Sucesso: {result.get('sucesso')}")
            print(f"Manuais usados: {result.get('manuais_usados')}")
            resposta = result.get('resposta', '')
            print(f"Resposta (primeiros 200 chars): {resposta[:200]}...")
        else:
            print(f"❌ Erro na pergunta: {response.status_code}")
            print(f"Detalhes: {response.text}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    
    print("\n" + "=" * 50)
    print("✅ Testes concluídos!")
    print("💡 Se todos os testes passaram, sua API está funcionando!")

if __name__ == "__main__":
    testar_api()