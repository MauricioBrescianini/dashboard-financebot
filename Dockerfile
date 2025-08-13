FROM python:3.12.6

ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Copiar e instalar requirements
COPY requirements.txt .
RUN pip install --upgrade pip && pip install -r requirements.txt

# Criar diretórios
RUN mkdir -p /app/src /app/data

# Copiar arquivos
COPY src/ ./src/

# Expor porta
EXPOSE 8501

# Comando padrão
CMD ["streamlit", "run", "src/dashboard.py", "--server.port=8501", "--server.address=0.0.0.0"]
