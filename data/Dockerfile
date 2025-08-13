# 1️⃣ Imagem base com Python 3.11
FROM python:3.12.6

# 2️⃣ Variável de ambiente para evitar buffers no Python
ENV PYTHONUNBUFFERED=1

# 3️⃣ Diretório de trabalho dentro do container
WORKDIR /app

# 4️⃣ Copiar requirements.txt primeiro para cache do pip
COPY requirements.txt .

# 5️⃣ Instalar dependências
RUN pip install --upgrade pip && pip install -r requirements.txt

# 6️⃣ Copiar todo o código fonte para o container
COPY src/ ./src/
COPY data/ ./data/

# 7️⃣ Expor porta se usar Streamlit ou FastAPI
EXPOSE 8501

# 8️⃣ Comando padrão para rodar seu dashboard (exemplo Streamlit)
CMD ["streamlit", "run", "src/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]