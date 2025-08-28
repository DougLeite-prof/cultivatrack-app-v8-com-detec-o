# Script PowerShell para deploy do backend API no Google Cloud Run

$ErrorActionPreference = "Stop"

Write-Host "🚀 Iniciando deploy do Backend API..." -ForegroundColor Green

# Variáveis de configuração
$PROJECT_ID = "cultivatrack-app"
$SERVICE_NAME = "cultivatrack-api"
$REGION = "southamerica-east1"
$IMAGE_NAME = "gcr.io/$PROJECT_ID/$SERVICE_NAME"

try {
    # 1. Verificar se o usuário está logado no gcloud
    Write-Host "🔐 Verificando autenticação..." -ForegroundColor Yellow
    $activeAccount = gcloud auth list --filter=status:ACTIVE --format="value(account)"
    if (-not $activeAccount) {
        Write-Host "❌ Você não está logado no gcloud. Execute: gcloud auth login" -ForegroundColor Red
        exit 1
    }

    # 2. Configurar projeto
    Write-Host "🔧 Configurando projeto..." -ForegroundColor Yellow
    gcloud config set project $PROJECT_ID

    # 3. Habilitar APIs necessárias
    Write-Host "🔌 Habilitando APIs..." -ForegroundColor Yellow
    gcloud services enable cloudbuild.googleapis.com
    gcloud services enable run.googleapis.com

    # 4. Navegar para diretório do backend
    Push-Location "backend_api"

    # 5. Build da imagem
    Write-Host "🏗️ Fazendo build da imagem Docker..." -ForegroundColor Yellow
    gcloud builds submit --tag $IMAGE_NAME .

    # 6. Deploy no Cloud Run
    Write-Host "🚀 Fazendo deploy no Cloud Run..." -ForegroundColor Yellow
    gcloud run deploy $SERVICE_NAME `
        --image $IMAGE_NAME `
        --platform managed `
        --region $REGION `
        --allow-unauthenticated `
        --memory 2Gi `
        --cpu 1 `
        --timeout 300 `
        --max-instances 10 `
        --port 8080

    # 7. Obter URL do serviço
    Write-Host "🌐 Obtendo URL do serviço..." -ForegroundColor Yellow
    $SERVICE_URL = gcloud run services describe $SERVICE_NAME --platform managed --region $REGION --format="value(status.url)"
    Write-Host "✅ Backend deployado com sucesso!" -ForegroundColor Green
    Write-Host "🌍 URL: $SERVICE_URL" -ForegroundColor Cyan

    # 8. Testar o serviço
    Write-Host "🧪 Testando o serviço..." -ForegroundColor Yellow
    try {
        Invoke-WebRequest -Uri $SERVICE_URL -Method GET -TimeoutSec 30 | Out-Null
        Write-Host "✅ Serviço está respondendo!" -ForegroundColor Green
    } catch {
        Write-Host "⚠️ Serviço pode estar iniciando. Teste manualmente: $SERVICE_URL" -ForegroundColor Yellow
    }

    Pop-Location
    Write-Host "🎉 Deploy do backend concluído!" -ForegroundColor Green

} catch {
    Write-Host "❌ Erro durante o deploy: $($_.Exception.Message)" -ForegroundColor Red
    if (Get-Location | Select-Object -ExpandProperty Path -ne $PWD) {
        Pop-Location
    }
    exit 1
}


