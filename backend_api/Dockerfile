# Dockerfile mais robusto para resolver problemas de dependência
FROM ubuntu:22.04

# Evitar interações durante a instalação
ENV DEBIAN_FRONTEND=noninteractive

# Instalar Python 3.10 e dependências do sistema
RUN apt-get update && apt-get install -y \
    python3.10 \
    python3.10-venv \
    python3.10-dev \
    python3-pip \
    build-essential \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libgtk-3-0 \
    libavcodec58 \
    libavformat58 \
    libswscale5 \
    pkg-config \
    && rm -rf /var/lib/apt/lists/*

# Criar link simbólico para python
RUN ln -s /usr/bin/python3.10 /usr/bin/python

# Atualizar pip
RUN python -m pip install --upgrade pip==23.3.1

WORKDIR /app

# Copiar requirements
COPY requirements.txt .

# Instalar dependências em ordem específica para evitar conflitos
RUN pip install numpy==1.24.4
RUN pip install opencv-python-headless==4.8.1.78
RUN pip install torch==2.1.2 torchvision==0.16.2 --index-url https://download.pytorch.org/whl/cpu
RUN pip install ultralytics==8.0.232 --no-deps
RUN pip install Flask==3.0.0 Flask-Cors==4.0.0 gunicorn==21.2.0
RUN pip install Pillow==10.2.0 PyYAML==6.0.1 requests==2.31.0 matplotlib==3.8.2 tqdm==4.66.1 psutil==5.9.8 py-cpuinfo==9.0.0 onnxruntime==1.16.3 rembg==2.0.67 pandas==2.1.4 seaborn==0.13.0

# Copiar código da aplicação e modelos
COPY . .

# Expor porta
EXPOSE 8080

# Comando de inicialização
CMD ["gunicorn", "--bind", "0.0.0.0:8080", "--workers", "1", "--threads", "2", "--timeout", "300", "--max-requests", "10", "--preload", "app:app"]