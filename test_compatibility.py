#!/usr/bin/env python3
import importlib, sys

pkgs = [
    "streamlit","pandas","plotly",
    "psycopg2","sqlalchemy","dotenv",
    "tiktoken",
    "langchain","langchain_core","langchain_community",
    "langsmith","langchain_openai","langchain_groq",
    "groq","httpx","pydantic"
]

print("🧪 Teste de Compatibilidade")
fails = []
for name in pkgs:
    try:
        m = importlib.import_module(name)
        print(f"✅ {name:<20} {getattr(m,'__version__','?')}")
    except Exception as e:
        fails.append((name,str(e)))
        print(f"❌ {name:<20} {e}")
if fails:
    print("\n🚨 Incompatibilidades:")
    for n,e in fails:
        print(f" • {n}: {e}")
    sys.exit(1)
print("\n🎉 Todos pacotes carregaram!")
