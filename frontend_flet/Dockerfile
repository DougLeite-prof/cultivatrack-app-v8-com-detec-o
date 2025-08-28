# Dockerfile para o FRONTEND Flet

# 1. Usar uma imagem base oficial e leve do Python
FROM python:3.12-slim

# 2. Definir o diretório de trabalho dentro do container
WORKDIR /app

# 3. Copiar o arquivo de dependências LEVES e instalá-las
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# 4. Copiar o resto da aplicação do frontend para o container
# IMPORTANTE: Isso inclui seu main.py e a pasta 'assets' com as imagens e PDFs
COPY . .

# 4.1. Verificar se a pasta assets foi copiada corretamente
RUN ls -la assets/ || echo "AVISO: Pasta assets não encontrada!"

# 5. Expor a porta que o App Engine Flexible espera
EXPOSE 8080

# 6. Comando para iniciar o servidor Flet com Gunicorn
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8080"]