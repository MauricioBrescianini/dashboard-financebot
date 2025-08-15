import os
from dotenv import load_dotenv

print("=== TESTE GROQ CLIENTE DIRETO - VERSÃO DEFINITIVA ===")

# Carregar variáveis
load_dotenv()

try:
    print("1. 🔑 Verificando API Key...")
    api_key = os.getenv('GROQ_API_KEY')
    
    if not api_key:
        print("❌ GROQ_API_KEY não encontrada")
        exit(1)
    
    print(f"✅ API Key: {api_key[:20]}...")
    
    print("2. 📦 Importando cliente Groq...")
    from groq import Groq
    print("✅ Import realizado!")
    
    print("3. 🤖 Criando cliente Groq...")
    client = Groq(api_key=api_key)
    print("✅ Cliente criado com sucesso!")
    
    print("4. 💬 Testando chamada à API...")
    completion = client.chat.completions.create(
        messages=[
            {
                "role": "user",
                "content": "Responda apenas: 'Groq funcionando perfeitamente!'"
            }
        ],
        model="mixtral-8x7b-32768",
        temperature=0.3,
        max_tokens=50
    )
    
    response_text = completion.choices[0].message.content
    print("✅ Chamada à API funcionou!")
    print(f"📝 Resposta: {response_text}")
    
    print("\n🎉 GROQ DIRETO FUNCIONANDO PERFEITAMENTE!")
    print("💡 Sistema pronto para uso!")
    
except Exception as e:
    print(f"❌ ERRO: {e}")
    import traceback
    traceback.print_exc()
