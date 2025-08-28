#!/bin/bash

# Script para deploy do backend API no Google Cloud Run
# Execute com: ./deploy_backend.sh

set -e  # Para em caso de erro

echo "🚀 Iniciando deploy do Backend API..."

# Variáveis de configuração
PROJECT_ID="cultivatrack-app"
SERVICE_NAME="cultivatrack-api"
REGION="southamerica-east1"
IMAGE_NAME="gcr.io/$PROJECT_ID/$SERVICE_NAME"

# 1. Verificar se o usuário está logado no gcloud
echo "🔐 Verificando autenticação..."
if ! gcloud auth list --filter=status:ACTIVE --format="value(account)" | grep -q .; then
    echo "❌ Você não está logado no gcloud. Execute: gcloud auth login"
    exit 1
fi

# 2. Configurar projeto
echo "🔧 Configurando projeto..."
gcloud config set project $PROJECT_ID

# 3. Habilitar APIs necessárias
echo "🔌 Habilitando APIs..."
gcloud services enable cloudbuild.googleapis.com
gcloud services enable run.googleapis.com

# 4. Navegar para diretório do backend
cd backend_api

# 5. Build da imagem
echo "🏗️ Fazendo build da imagem Docker..."
gcloud builds submit --tag $IMAGE_NAME .

# 6. Deploy no Cloud Run
echo "🚀 Fazendo deploy no Cloud Run..."
gcloud run deploy $SERVICE_NAME \
    --image $IMAGE_NAME \
    --platform managed \
    --region $REGION \
    --allow-unauthenticated \
    --memory 2Gi \
    --cpu 1 \
    --timeout 300 \
    --max-instances 10 \
    --port 8080

# 7. Obter URL do serviço
echo "🌐 Obtendo URL do serviço..."
SERVICE_URL=$(gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)")
echo "✅ Backend deployado com sucesso!"
echo "🌍 URL: $SERVICE_URL"

# 8. Testar o serviço
echo "🧪 Testando o serviço..."
if curl -f "$SERVICE_URL/" > /dev/null 2>&1; then
    echo "✅ Serviço está respondendo!"
else
    echo "⚠️ Serviço pode estar iniciando. Teste manualmente: $SERVICE_URL"
fi

cd ..
echo "🎉 Deploy do backend concluído!"


