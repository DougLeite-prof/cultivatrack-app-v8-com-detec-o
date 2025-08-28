# 🌟 CultivaTrack - Deploy no Google Cloud

Este projeto implementa um sistema completo de monitoramento agrícola com IA para detecção de cercosporiose em pimentas.

## 📋 Pré-requisitos

### 1. Conta Google Cloud
- Crie uma conta em [Google Cloud Console](https://console.cloud.google.com/)
- Ative billing (cobrança) na sua conta
- Crie um projeto chamado `cultivatrack-app` (ou use outro nome e ajuste os scripts)

### 2. Google Cloud CLI
- Instale o [Google Cloud CLI](https://cloud.google.com/sdk/docs/install)
- Faça login: `gcloud auth login`
- Configure o projeto: `gcloud config set project cultivatrack-app`

### 3. Docker (Opcional)
- Para builds locais, instale o [Docker](https://www.docker.com/get-started)

## 🚀 Deploy Automático

### Windows (PowerShell)
```powershell
# Execute o script principal
.\deploy_all.ps1
```

### Linux/Mac (Bash)
```bash
# Torne os scripts executáveis
chmod +x *.sh

# Execute o script principal
./deploy_all.sh
```

## 📦 Deploy Manual

Se preferir fazer o deploy passo a passo:

### 1. Backend API (YOLO + Flask)
```bash
# Windows
.\deploy_backend.ps1

# Linux/Mac
./deploy_backend.sh
```

### 2. Frontend (Flet)
```bash
# Windows
.\deploy_frontend.ps1

# Linux/Mac
./deploy_frontend.sh
```

## 🏗️ Arquitetura do Sistema

```
📱 Frontend (Flet)          🔄 API REST          🧠 Backend (Flask + YOLO)
├── Interface do usuário    ├── /predict         ├── Processamento de imagens
├── Upload de imagens       └── JSON response    ├── Modelo YOLOv8
├── Visualização de dados                        ├── Cálculo de severidade
└── Clima & ETP                                  └── Inferência IA
```

## 🔧 Configuração

### URLs dos Serviços
Após o deploy, você terá:
- **Backend API**: `https://cultivatrack-api-{hash}.southamerica-east1.run.app`
- **Frontend**: `https://cultivatrack-frontend-{hash}.southamerica-east1.run.app`

### Atualizar URL da API
Se a URL do backend mudou, atualize no arquivo `frontend_flet/main.py`:
```python
API_URL = "https://sua-nova-url-do-backend"
```

## 🧪 Testando o Sistema

### 1. Teste Local (Desenvolvimento)
```bash
# Backend
cd backend_api
pip install -r requirements.txt
python app.py

# Frontend (em outro terminal)
cd frontend_flet
pip install -r requirements.txt
python main.py
```

### 2. Teste em Produção
1. Acesse a URL do frontend
2. Selecione cidade, cultura e doença
3. Calcule amostragem de folhas
4. Carregue imagens (câmera ou galeria)
5. Clique em "Calcular Severidade com IA"
6. Verifique os resultados

## 📱 Uso em Campo

### Para Agricultores
1. **Acesse pelo celular**: Use a URL do frontend
2. **Capture fotos**: Use o botão "Câmera" para fotos diretas
3. **Processe as imagens**: Clique em "Calcular Severidade com IA"
4. **Veja os resultados**: Severidade % e recomendações

### Requisitos de Campo
- 📶 Conexão com internet (3G/4G/WiFi)
- 📱 Navegador moderno (Chrome, Safari, Edge)
- 📷 Câmera funcional no dispositivo

## 🔍 Monitoramento

### Logs do Sistema
```bash
# Logs do backend
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cultivatrack-api"

# Logs do frontend
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=cultivatrack-frontend"
```

### Métricas
Acesse o [Cloud Console](https://console.cloud.google.com/) → Cloud Run → Suas aplicações

## ❌ Solução de Problemas

### Erro: "Service Unavailable"
- ✅ Verifique se o deploy foi bem-sucedido
- ✅ Aguarde alguns minutos (cold start)
- ✅ Verifique os logs do serviço

### Erro: "Authentication failed"
```bash
gcloud auth login
gcloud config set project cultivatrack-app
```

### Erro de build Docker
- ✅ Verifique se o arquivo `requirements.txt` existe
- ✅ Verifique se o modelo YOLO (`yolov8n-seg.pt`) está presente
- ✅ Verifique a conexão com internet

### Problema de upload de imagens
- ✅ Verifique se o navegador suporta FileAPI
- ✅ Teste com imagens menores (<5MB)
- ✅ Verifique a conectividade

## 💰 Custos Estimados

Para teste com poucos agricultores:
- **Cloud Run**: ~$5-20/mês (depende do uso)
- **Cloud Build**: ~$1-5/mês
- **Storage**: ~$1/mês
- **Network**: ~$1-3/mês

**Total estimado**: $8-30/mês para uso moderado

## 🔄 Atualizações

Para atualizar o sistema:
1. Faça suas modificações no código
2. Execute novamente: `.\deploy_all.ps1` ou `./deploy_all.sh`
3. O sistema fará build e deploy das novas versões

## 📞 Suporte

Em caso de problemas:
1. Verifique os logs do Cloud Run
2. Teste localmente primeiro
3. Verifique conectividade e permissões
4. Monitore o uso de recursos

---

## 🌟 Resumo dos Comandos

```bash
# Deploy completo
.\deploy_all.ps1  # Windows
./deploy_all.sh   # Linux/Mac

# Logs
gcloud logging read "resource.type=cloud_run_revision"

# Status dos serviços
gcloud run services list

# Deletar serviços (se necessário)
gcloud run services delete cultivatrack-api --region=southamerica-east1
gcloud run services delete cultivatrack-frontend --region=southamerica-east1
```

**🎉 Boa sorte com seu teste em campo!** 🌾


