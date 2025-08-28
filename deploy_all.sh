#!/bin/bash

# Script principal para deploy completo do CultivaTrack no Google Cloud
# Execute com: ./deploy_all.sh

set -e  # Para em caso de erro

echo "🌟 ==================================="
echo "🌟 CULTIVATRACK - DEPLOY COMPLETO"
echo "🌟 ==================================="

# Verificar se os scripts existem
if [ ! -f "deploy_backend.sh" ] || [ ! -f "deploy_frontend.sh" ]; then
    echo "❌ Scripts de deploy não encontrados!"
    exit 1
fi

# Tornar scripts executáveis
chmod +x deploy_backend.sh
chmod +x deploy_frontend.sh

# 1. Deploy do Backend API (YOLO + Flask)
echo ""
echo "🔥 FASE 1: DEPLOY DO BACKEND API"
echo "================================"
./deploy_backend.sh

# Aguardar um pouco para garantir que o backend está estável
echo ""
echo "⏱️ Aguardando 30 segundos para estabilizar o backend..."
sleep 30

# 2. Deploy do Frontend (Flet)
echo ""
echo "🎨 FASE 2: DEPLOY DO FRONTEND"
echo "============================"
./deploy_frontend.sh

# 3. Resumo final
echo ""
echo "🎉 =================================="
echo "🎉 DEPLOY COMPLETO FINALIZADO!"
echo "🎉 =================================="

# Obter URLs dos serviços
PROJECT_ID="cultivatrack-app"
REGION="southamerica-east1"

echo ""
echo "📋 RESUMO DOS SERVIÇOS:"
echo "======================="

# Backend URL
BACKEND_URL=$(gcloud run services describe cultivatrack-api --platform managed --region $REGION --format="value(status.url)" 2>/dev/null || echo "Não disponível")
echo "🔗 Backend API: $BACKEND_URL"

# Frontend URL
FRONTEND_URL=$(gcloud run services describe cultivatrack-frontend --platform managed --region $REGION --format="value(status.url)" 2>/dev/null || echo "Não disponível")
echo "🔗 Frontend App: $FRONTEND_URL"

echo ""
echo "✅ PRÓXIMOS PASSOS:"
echo "=================="
echo "1. Acesse o frontend em: $FRONTEND_URL"
echo "2. Teste a funcionalidade 'Calcular Severidade com IA'"
echo "3. Verifique se as imagens são processadas corretamente"
echo ""
echo "🚨 IMPORTANTE:"
echo "=============="
echo "- Certifique-se que a URL do backend no frontend está atualizada"
echo "- Teste com algumas imagens antes do teste em campo"
echo "- Monitore os logs em caso de problemas"
echo ""
echo "📱 Para teste em campo:"
echo "======================"
echo "- Use o link do frontend em dispositivos móveis"
echo "- Teste a captura de imagens via câmera"
echo "- Verifique a conectividade de internet no local"

echo ""
echo "🌟 Deploy concluído com sucesso! 🌟"


