# Script PowerShell principal para deploy completo do CultivaTrack no Google Cloud

$ErrorActionPreference = "Stop"

Write-Host "🌟 ===================================" -ForegroundColor Magenta
Write-Host "🌟 CULTIVATRACK - DEPLOY COMPLETO" -ForegroundColor Magenta
Write-Host "🌟 ===================================" -ForegroundColor Magenta

try {
    # Verificar se os scripts existem
    if (-not (Test-Path "deploy_backend.ps1") -or -not (Test-Path "deploy_frontend.ps1")) {
        Write-Host "❌ Scripts de deploy não encontrados!" -ForegroundColor Red
        exit 1
    }

    # 1. Deploy do Backend API (YOLO + Flask)
    Write-Host ""
    Write-Host "🔥 FASE 1: DEPLOY DO BACKEND API" -ForegroundColor Cyan
    Write-Host "================================" -ForegroundColor Cyan
    .\deploy_backend.ps1

    # Aguardar um pouco para garantir que o backend está estável
    Write-Host ""
    Write-Host "⏱️ Aguardando 30 segundos para estabilizar o backend..." -ForegroundColor Yellow
    Start-Sleep -Seconds 30

    # 2. Deploy do Frontend (Flet)
    Write-Host ""
    Write-Host "🎨 FASE 2: DEPLOY DO FRONTEND" -ForegroundColor Cyan
    Write-Host "============================" -ForegroundColor Cyan
    .\deploy_frontend.ps1

    # 3. Resumo final
    Write-Host ""
    Write-Host "🎉 ==================================" -ForegroundColor Green
    Write-Host "🎉 DEPLOY COMPLETO FINALIZADO!" -ForegroundColor Green
    Write-Host "🎉 ==================================" -ForegroundColor Green

    # Obter URLs dos serviços
    $PROJECT_ID = "cultivatrack-app"
    $REGION = "southamerica-east1"

    Write-Host ""
    Write-Host "📋 RESUMO DOS SERVIÇOS:" -ForegroundColor Cyan
    Write-Host "=======================" -ForegroundColor Cyan

    # Backend URL
    try {
        $BACKEND_URL = gcloud run services describe cultivatrack-api --platform managed --region $REGION --format="value(status.url)"
    } catch {
        $BACKEND_URL = "Não disponível"
    }
    Write-Host "🔗 Backend API: $BACKEND_URL" -ForegroundColor White

    # Frontend URL
    try {
        $FRONTEND_URL = gcloud run services describe cultivatrack-frontend --platform managed --region $REGION --format="value(status.url)"
    } catch {
        $FRONTEND_URL = "Não disponível"
    }
    Write-Host "🔗 Frontend App: $FRONTEND_URL" -ForegroundColor White

    Write-Host ""
    Write-Host "✅ PRÓXIMOS PASSOS:" -ForegroundColor Yellow
    Write-Host "==================" -ForegroundColor Yellow
    Write-Host "1. Acesse o frontend em: $FRONTEND_URL" -ForegroundColor White
    Write-Host "2. Teste a funcionalidade 'Calcular Severidade com IA'" -ForegroundColor White
    Write-Host "3. Verifique se as imagens são processadas corretamente" -ForegroundColor White

    Write-Host ""
    Write-Host "🚨 IMPORTANTE:" -ForegroundColor Red
    Write-Host "=============" -ForegroundColor Red
    Write-Host "- Certifique-se que a URL do backend no frontend está atualizada" -ForegroundColor White
    Write-Host "- Teste com algumas imagens antes do teste em campo" -ForegroundColor White
    Write-Host "- Monitore os logs em caso de problemas" -ForegroundColor White

    Write-Host ""
    Write-Host "📱 Para teste em campo:" -ForegroundColor Magenta
    Write-Host "======================" -ForegroundColor Magenta
    Write-Host "- Use o link do frontend em dispositivos móveis" -ForegroundColor White
    Write-Host "- Teste a captura de imagens via câmera" -ForegroundColor White
    Write-Host "- Verifique a conectividade de internet no local" -ForegroundColor White

    Write-Host ""
    Write-Host "🌟 Deploy concluído com sucesso! 🌟" -ForegroundColor Green

} catch {
    Write-Host ""
    Write-Host "❌ ERRO DURANTE O DEPLOY:" -ForegroundColor Red
    Write-Host $_.Exception.Message -ForegroundColor Red
    Write-Host ""
    Write-Host "Para diagnosticar problemas:" -ForegroundColor Yellow
    Write-Host "1. Verifique se está logado: gcloud auth list" -ForegroundColor White
    Write-Host "2. Verifique o projeto: gcloud config get-value project" -ForegroundColor White
    Write-Host "3. Verifique os logs: gcloud logging read" -ForegroundColor White
    exit 1
}
