#!/usr/bin/env python3
import importlib, sys

pkgs = [
    "streamlit", "pandas", "plotly",
    "psycopg2", "sqlalchemy", "dotenv",
    "langchain", "langchain_core",
    "langchain_community", "langsmith",
    "langchain_groq", "groq",
    "httpx", "pydantic", "tiktoken"
]

print("🧪  Compat-test – stack FinanceBot\n")
fail = []
for name in pkgs:
    try:
        m = importlib.import_module(name)
        print(f"✅ {name:<20} {getattr(m,'__version__','?')}")
    except Exception as e:
        fail.append((name, str(e)))
        print(f"❌ {name:<20} {e}")

if fail:
    print("\n🚨 Incompatibilidades:")
    for n, err in fail:
        print(f"   • {n}: {err}")
    sys.exit(1)

print("\n🎉 Ambiente limpo – todos os pacotes carregaram!")