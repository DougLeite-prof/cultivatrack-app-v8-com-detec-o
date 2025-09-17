# Script PowerShell para gerenciar tráfego entre revisões no Google Cloud Run

$ErrorActionPreference = "Stop"

# Variáveis de configuração
$PROJECT_ID = "cultivatrack-app"
$REGION = "southamerica-east1"
$FRONTEND_SERVICE = "cultivatrack-frontend"
$BACKEND_SERVICE = "cultivatrack-api"

function Show-Menu {
    Write-Host ""
    Write-Host "🚦 GERENCIAMENTO DE TRÁFEGO - CULTIVATRACK" -ForegroundColor Magenta
    Write-Host "=========================================" -ForegroundColor Magenta
    Write-Host ""
    Write-Host "1. Ver revisões atuais" -ForegroundColor Cyan
    Write-Host "2. Ver distribuição de tráfego atual" -ForegroundColor Cyan
    Write-Host "3. Migrar 100% tráfego para nova revisão" -ForegroundColor Yellow
    Write-Host "4. Dividir tráfego 50/50" -ForegroundColor Yellow
    Write-Host "5. Teste gradual (10% nova / 90% atual)" -ForegroundColor Yellow
    Write-Host "6. Rollback (100% para versão anterior)" -ForegroundColor Red
    Write-Host "7. Sair" -ForegroundColor White
    Write-Host ""
}

function Show-Revisions {
    Write-Host "📋 REVISÕES DO FRONTEND:" -ForegroundColor Cyan
    gcloud run revisions list --service $FRONTEND_SERVICE --region $REGION --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"
    Write-Host ""
    Write-Host "📋 REVISÕES DO BACKEND:" -ForegroundColor Cyan
    gcloud run revisions list --service $BACKEND_SERVICE --region $REGION --format="table(metadata.name,status.conditions[0].status,metadata.creationTimestamp)"
}

function Show-Traffic {
    Write-Host "🚦 DISTRIBUIÇÃO DE TRÁFEGO ATUAL:" -ForegroundColor Cyan
    Write-Host ""
    Write-Host "Frontend:" -ForegroundColor Yellow
    gcloud run services describe $FRONTEND_SERVICE --region $REGION --format="table(status.traffic[].percent,status.traffic[].tag,status.traffic[].revisionName)"
    Write-Host ""
    Write-Host "Backend:" -ForegroundColor Yellow
    gcloud run services describe $BACKEND_SERVICE --region $REGION --format="table(status.traffic[].percent,status.traffic[].tag,status.traffic[].revisionName)"
}

function Migrate-To-New-Revision {
    Write-Host "🔄 Migrando 100% do tráfego para a nova revisão..." -ForegroundColor Yellow
    
    # Pegar a tag mais recente
    $LATEST_TAG = gcloud run revisions list --service $FRONTEND_SERVICE --region $REGION --format="value(metadata.labels.serving-knative-dev-serviceTag)" --limit=1 --sort-by="~metadata.creationTimestamp"
    
    if ($LATEST_TAG) {
        Write-Host "Migrando para tag: $LATEST_TAG" -ForegroundColor Cyan
        gcloud run services update-traffic $FRONTEND_SERVICE --to-tags "$LATEST_TAG=100" --region $REGION
        Write-Host "✅ Tráfego migrado com sucesso!" -ForegroundColor Green
    } else {
        Write-Host "❌ Nenhuma tag encontrada. Migrando para última revisão..." -ForegroundColor Red
        gcloud run services update-traffic $FRONTEND_SERVICE --to-latest=100 --region $REGION
    }
}

function Split-Traffic-50-50 {
    Write-Host "🔄 Dividindo tráfego 50/50..." -ForegroundColor Yellow
    
    $LATEST_TAG = gcloud run revisions list --service $FRONTEND_SERVICE --region $REGION --format="value(metadata.labels.serving-knative-dev-serviceTag)" --limit=1 --sort-by="~metadata.creationTimestamp"
    
    if ($LATEST_TAG) {
        gcloud run services update-traffic $FRONTEND_SERVICE --to-tags "$LATEST_TAG=50" --to-latest=50 --region $REGION
        Write-Host "✅ Tráfego dividido 50/50!" -ForegroundColor Green
    } else {
        Write-Host "❌ Não foi possível encontrar uma tag para dividir o tráfego." -ForegroundColor Red
    }
}

function Test-Gradual {
    Write-Host "🔄 Configurando teste gradual (10% nova / 90% atual)..." -ForegroundColor Yellow
    
    $LATEST_TAG = gcloud run revisions list --service $FRONTEND_SERVICE --region $REGION --format="value(metadata.labels.serving-knative-dev-serviceTag)" --limit=1 --sort-by="~metadata.creationTimestamp"
    
    if ($LATEST_TAG) {
        gcloud run services update-traffic $FRONTEND_SERVICE --to-tags "$LATEST_TAG=10" --to-latest=90 --region $REGION
        Write-Host "✅ Teste gradual configurado: 10% nova revisão, 90% atual!" -ForegroundColor Green
    } else {
        Write-Host "❌ Não foi possível encontrar uma tag para o teste gradual." -ForegroundColor Red
    }

}

function Rollback {
    Write-Host "🔄 Fazendo rollback para versão anterior..." -ForegroundColor Red
    gcloud run services update-traffic $FRONTEND_SERVICE --to-latest=100 --region $REGION
    Write-Host "✅ Rollback concluído!" -ForegroundColor Green
}

# Menu principal
try {
    gcloud config set project $PROJECT_ID
    
    do {
        Show-Menu
        $choice = Read-Host "Escolha uma opção (1-7)"
        
        switch ($choice) {
            "1" { Show-Revisions }
            "2" { Show-Traffic }
            "3" { Migrate-To-New-Revision }
            "4" { Split-Traffic-50-50 }
            "5" { Test-Gradual }
            "6" { Rollback }
            "7" { 
                Write-Host "👋 Saindo..." -ForegroundColor Green
                break
            }
            default { 
                Write-Host "❌ Opção inválida! Escolha de 1 a 7." -ForegroundColor Red 
            }
        }
        
        if ($choice -ne "7") {
            Write-Host ""
            Read-Host "Pressione Enter para continuar"
        }
    } while ($choice -ne "7")

} catch {
    Write-Host ""
    Write-Host "❌ ERRO:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    exit 1
}

