# 🌱 CultivaTrack v8 - Sistema de Monitoramento Agrícola com IA

**Sistema avançado de monitoramento e análise de cultivos com detecção automática de doenças usando YOLOv8**

[![Deploy Status](https://img.shields.io/badge/Deploy-Cloud%20Run-blue)](https://cloud.google.com/run)
[![Python](https://img.shields.io/badge/Python-3.10%2B-blue)](https://python.org)
[![Flet](https://img.shields.io/badge/Frontend-Flet-green)](https://flet.dev)
[![YOLOv8](https://img.shields.io/badge/AI-YOLOv8-orange)](https://ultralytics.com)

## 🆕 **Novidades da Versão v8**

### 🧠 **Detecção Automática com IA**
- **YOLOv8**: Modelo treinado para detecção de doenças em pimenteiras
- **3 Doenças Detectadas**: Cercosporiose, Mosaico e Mancha-bacteriana
- **Visualização Avançada**: Bounding boxes coloridos com confidence values
- **Múltiplas Detecções**: Suporte para identificar várias doenças na mesma imagem

### 🎯 **Funcionalidades Principais**
- **📸 Captura de Imagem**: Interface integrada para fotografia de folhas
- **🔍 Análise Instantânea**: Processamento em tempo real com confidence scores
- **📊 Visualização**: Plotagem de resultados com bounding boxes coloridas
- **🔄 Redirecionamento Inteligente**: Fluxo específico baseado na doença detectada

## 🏗️ **Arquitetura do Sistema**

```
CultivaTrack v8
├── 🖥️ Frontend (Flet)
│   ├── Interface principal
│   ├── Captura de imagem
│   ├── Visualização de resultados
│   └── Dashboard de monitoramento
├── ⚙️ Backend (FastAPI)
│   ├── API REST
│   ├── Processamento YOLOv8
│   ├── Análise de severidade
│   └── Dados meteorológicos
└── 🧠 Modelos IA
    ├── YOLOv8 Detecção (modelo-deteccao.pt)
    └── YOLOv8 Segmentação (yolov8n-seg.pt)
```

## 🚀 **Deploy em Produção**

### 📍 **URLs de Teste (Zero Traffic)**
- **Frontend**: https://revisao-deteccao-v6---cultivatrack-frontend-5f6w6oqomq-rj.a.run.app
- **Backend**: https://revisao-deteccao-v6---cultivatrack-api-5f6w6oqomq-rj.a.run.app

### ☁️ **Google Cloud Run**
- **Deployment**: Automatizado via Cloud Build
- **Scaling**: Automático baseado em demanda
- **Zero Downtime**: Deployments sem interrupção

## 🛠️ **Tecnologias Utilizadas**

### **Frontend**
- **Flet 0.25.2**: Framework Python para UI multiplataforma
- **Python 3.12**: Linguagem principal
- **Matplotlib**: Visualização de gráficos e dados
- **Requests**: Comunicação com APIs

### **Backend**
- **FastAPI**: Framework web moderno e rápido
- **YOLOv8 (Ultralytics)**: Modelos de detecção e segmentação
- **OpenCV**: Processamento de imagens
- **rembg**: Remoção de background
- **Gunicorn**: Servidor WSGI para produção

### **IA e ML**
- **PyTorch**: Framework de deep learning
- **Ultralytics YOLOv8**: Estado da arte em detecção de objetos
- **OpenCV**: Processamento de imagens
- **NumPy**: Computação numérica

## 📊 **Funcionalidades de IA**

### 🔍 **Detecção de Doenças**
```python
# Doenças Suportadas
DISEASES = {
    'cercosporiose': 'Cercospora capsici',
    'mosaico': 'Pepper mosaic virus', 
    'mancha-bacteriana': 'Xanthomonas campestris'
}

# Configuração do Modelo
CONFIDENCE_THRESHOLD = 0.3
INPUT_SIZE = 256x256
COLORS = {
    'cercosporiose': Green,
    'mosaico': Blue, 
    'mancha-bacteriana': Red
}
```

### 📈 **Análise de Severidade**
- **Segmentação Pixel-level**: Cálculo preciso da área afetada
- **Percentual de Severidade**: Quantificação objetiva do dano
- **Histórico de Progressão**: Acompanhamento temporal

## 🔧 **Configuração Local**

### **Pré-requisitos**
```bash
Python 3.10+
Git
Docker (opcional)
```

### **Instalação**
```bash
# Clone o repositório
git clone https://github.com/DougLeite-prof/cultivatrack-app-v8-com-deteccao.git
cd cultivatrack-app-v8-com-deteccao

# Backend
cd backend_api
pip install -r requirements.txt
python app.py

# Frontend  
cd ../frontend_flet
pip install -r requirements.txt
python main.py
```

### **Teste Local da Detecção**
```bash
cd backend_api
python test_detection_local.py
```

## 📁 **Estrutura do Projeto**

```
cultivatrack-app-v8-com-deteccao/
├── 📂 backend_api/
│   ├── app.py                 # API principal
│   ├── Dockerfile            # Container backend
│   ├── requirements.txt      # Dependências Python
│   ├── modelo-deteccao.pt    # Modelo YOLOv8 detecção
│   ├── yolov8n-seg.pt       # Modelo YOLOv8 segmentação
│   └── test_detection_local.py # Teste local
├── 📂 frontend_flet/
│   ├── main.py              # Aplicação Flet
│   ├── Dockerfile           # Container frontend
│   ├── requirements.txt     # Dependências
│   └── 📂 assets/
│       ├── mosaico.jpg      # Imagem doença mosaico
│       ├── mancha bacteriana.png
│       └── *.pt             # Modelos IA
├── 📂 scripts/
│   └── deploy.ps1           # Scripts de deploy
└── README.md               # Documentação
```

## 🧪 **Como Testar a Detecção**

### **1. Acesse o Frontend**
```
https://revisao-deteccao-v6---cultivatrack-frontend-5f6w6oqomq-rj.a.run.app
```

### **2. Fluxo de Teste**
1. **Selecione**: "Pimenta" como cultura
2. **Clique**: "Detectar Doença com IA" (primeira opção)
3. **Capture**: Foto de folha com sintomas
4. **Analise**: Resultados com confidence e bounding boxes

### **3. Resultados Esperados**
- ✅ **Detecção Precisa**: Identificação correta da doença
- ✅ **Confidence Score**: Percentual de confiança (>30%)
- ✅ **Visualização**: Bounding boxes coloridos
- ✅ **Múltiplas Detecções**: Lista completa se houver

## 🎯 **Roadmap**

### **Versão Atual (v8.0)**
- ✅ Detecção YOLOv8 implementada
- ✅ Interface de captura integrada
- ✅ Visualização com bounding boxes
- ✅ Deploy em produção

### **Próximas Versões**
- 🔄 **v8.1**: Mais doenças suportadas
- 🔄 **v8.2**: Culturas adicionais (tomate, milho)
- 🔄 **v8.3**: Recomendações de tratamento
- 🔄 **v8.4**: Análise temporal automatizada

## 🤝 **Contribuição**

1. **Fork** o projeto
2. **Crie** uma branch para sua feature (`git checkout -b feature/nova-doenca`)
3. **Commit** suas mudanças (`git commit -m 'feat: adiciona detecção de nova doença'`)
4. **Push** para a branch (`git push origin feature/nova-doenca`)
5. **Abra** um Pull Request

## 📄 **Licença**

Este projeto está licenciado sob a MIT License - veja o arquivo [LICENSE](LICENSE) para detalhes.

## 👨‍💻 **Autor**

**Prof. Douglas Leite**
- GitHub: [@DougLeite-prof](https://github.com/DougLeite-prof)
- Email: contato@cultivatrack.com

## 🙏 **Agradecimentos**

- **Ultralytics** pela excelente biblioteca YOLOv8
- **Flet Team** pelo framework multiplataforma
- **Google Cloud** pela infraestrutura robusta
- **Comunidade Open Source** pelas contribuições

---

⭐ **Se este projeto foi útil, considere dar uma estrela no repositório!**