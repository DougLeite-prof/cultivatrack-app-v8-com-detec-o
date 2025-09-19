# backend_api/app.py
import os
import cv2
import numpy as np
import base64
import uuid
from typing import Dict, List
from flask import Flask, request, jsonify
from flask_cors import CORS
from PIL import Image
from rembg import remove
from ultralytics import YOLO

# --- Configuração do Flask ---
app = Flask(__name__)
CORS(app)  # Permite que o frontend acesse a API

# --- Constantes e Carregamento do Modelo ---
# Estas pastas serão usadas DENTRO do container na nuvem
INPUT_FOLDER = "/tmp/input"
OUTPUT_FOLDER = "/tmp/output"
PLOTS_FOLDER = "/tmp/plots"
os.makedirs(INPUT_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)
os.makedirs(PLOTS_FOLDER, exist_ok=True)

# O modelo será copiado para dentro do container pelo Dockerfile
MODEL_PATH = "yolov8n-seg.pt" 
model = YOLO(MODEL_PATH)
print("Modelo YOLO carregado com sucesso.")

# Modelo para detecção de doenças (YOLOv8 para classificação)
DETECTION_MODEL_PATH = "modelo-deteccao.pt"
detection_model = None
if os.path.exists(DETECTION_MODEL_PATH):
    try:
        detection_model = YOLO(DETECTION_MODEL_PATH)
        print("Modelo YOLOv8 de detecção carregado com sucesso.")
    except Exception as e:
        print(f"ERRO ao carregar modelo de detecção: {e}")
        detection_model = None
else:
    print(f"AVISO: Modelo de detecção não encontrado em {DETECTION_MODEL_PATH}")

# --- Lógica de Processamento de Imagem ---
TARGET_SIZE = (640, 640)
ZOOM_FACTOR = 1.0  # Sem zoom - usa 100% da imagem
ADD_PADDING = False  # Padding desativado
PADDING_FACTOR = 0.15

def preprocess_image(image_path: str, output_path: str) -> None:
    """Processa imagem com abordagem melhorada para centralização"""
    print("[DEBUG] preprocess_image:", image_path, "->", output_path)
    img = cv2.imread(image_path)
    if img is None:
        print(f"Erro ao carregar a imagem: {image_path}")
        return
    
    h, w = img.shape[:2]
    print(f"[DEBUG] Dimensões originais: {w}x{h}")
    
    # PASSO 1: Tornar a imagem quadrada (crop central EXPANDIDO)
    # Usar a menor dimensão como base e EXPANDIR para capturar mais área
    min_dim = min(h, w)
    
    # Fator de EXPANSÃO do crop (1.50 = pega 50% a mais se disponível)
    # Isso captura MUITO mais área ao redor da folha, garantindo margem generosa
    CROP_EXPANSION = 1.50
    desired_size = int(min_dim * CROP_EXPANSION)
    
    # Garantir que não exceda as dimensões da imagem
    crop_size = min(desired_size, h, w)
    
    # Calcular coordenadas para crop quadrado central expandido
    center_x = w // 2
    center_y = h // 2
    half_size = crop_size // 2
    
    # Calcular limites garantindo que não saiam da imagem
    left = max(0, center_x - half_size)
    right = min(w, center_x + half_size)
    top = max(0, center_y - half_size)
    bottom = min(h, center_y + half_size)
    
    # Ajustar para garantir que seja quadrado
    actual_width = right - left
    actual_height = bottom - top
    if actual_width != actual_height:
        # Ajustar para o menor lado
        size = min(actual_width, actual_height)
        left = center_x - size // 2
        right = left + size
        top = center_y - size // 2
        bottom = top + size
    
    # Fazer crop quadrado central expandido
    img_square = img[top:bottom, left:right]
    print(f"[DEBUG] Após crop quadrado: {img_square.shape[1]}x{img_square.shape[0]}")
    
    # PASSO 2: Aplicar zoom (se necessário)
    # ZOOM_FACTOR = 1.0 significa usar 100% da imagem (sem zoom)
    # ZOOM_FACTOR = 0.90 significa capturar 90% da imagem (zoom suave)
    # ZOOM_FACTOR = 0.50 significa capturar 50% da imagem (zoom médio)
    if ZOOM_FACTOR < 1.0:
        square_size = img_square.shape[0]
        zoom_size = int(square_size * ZOOM_FACTOR)
        margin = (square_size - zoom_size) // 2
        
        # Aplicar zoom (crop com margens iguais)
        img_zoomed = img_square[margin:margin+zoom_size, margin:margin+zoom_size]
        print(f"[DEBUG] Aplicando zoom - capturando {ZOOM_FACTOR*100:.0f}% da imagem: {img_zoomed.shape[1]}x{img_zoomed.shape[0]}")
    else:
        # Sem zoom - usa a imagem quadrada completa
        img_zoomed = img_square
        print(f"[DEBUG] Sem zoom - usando 100% da imagem quadrada: {img_zoomed.shape[1]}x{img_zoomed.shape[0]}")
    
    # PASSO 3: Redimensionar para um tamanho adequado para o rembg
    # Usar um tamanho maior para melhor qualidade no rembg
    intermediate_size = 1024
    img_resized = cv2.resize(img_zoomed, (intermediate_size, intermediate_size), interpolation=cv2.INTER_CUBIC)
    
    # Converter para RGB para o rembg
    img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)
    pil_img = Image.fromarray(img_rgb)
    
    try:
        output_img = remove(pil_img)
        try:
            orientation = pil_img.getexif().get(274, 1) if hasattr(pil_img, "getexif") and pil_img.getexif() else 1
        except Exception:
            orientation = 1
    except Exception as e:
        print(f"Erro ao remover o fundo: {e}")
        # Se a remoção do fundo falhar, não há como continuar o processamento
        orientation = 1
        return
    
    # Garantir que output_img seja PIL.Image
    if isinstance(output_img, bytes):
        from io import BytesIO
        output_img = Image.open(BytesIO(output_img))
    elif isinstance(output_img, np.ndarray):
        output_img = Image.fromarray(output_img)
    
    # PASSO 4: Garantir fundo branco
    output_img = output_img.convert("RGBA")
    background = Image.new("RGBA", output_img.size, (255, 255, 255, 255))
    composited = Image.alpha_composite(background, output_img)
    composited = composited.convert("RGB")
    
    # PASSO 5: Adicionar padding se configurado (para "afastar" a imagem)
    if ADD_PADDING:
        # Primeiro reduzir a imagem para deixar espaço para o padding
        reduction_factor = 1 - (PADDING_FACTOR * 2)  # Se padding é 15%, reduzir para 70%
        reduced_size = int(TARGET_SIZE[0] * reduction_factor)
        
        # Reduzir a imagem
        composited = composited.resize((reduced_size, reduced_size), Image.Resampling.LANCZOS)
        
        # Criar imagem final com tamanho alvo e fundo branco
        final_img = Image.new("RGB", TARGET_SIZE, (255, 255, 255))
        
        # Calcular posição para centralizar a imagem reduzida
        paste_position = (TARGET_SIZE[0] - reduced_size) // 2
        
        # Colar a imagem reduzida no centro
        final_img.paste(composited, (paste_position, paste_position))
        composited = final_img
        print(f"[DEBUG] Imagem reduzida para {reduction_factor*100:.0f}% e padding de {PADDING_FACTOR*100:.0f}% aplicado")
    else:
        # PASSO 6: Resize final para 640x640 (tamanho ideal para inferência YOLO)
        composited = composited.resize(TARGET_SIZE, Image.Resampling.LANCZOS)
    
    composited.save(output_path)
    print(f"[DEBUG] Imagem salva em: {output_path} com dimensões {TARGET_SIZE}")
    print("[DEBUG] Arquivo existe:", os.path.exists(output_path))
    
    # Limpeza explícita de memória
    del pil_img, output_img, background, composited, img, img_square, img_zoomed, img_resized

def preprocess_image_detection(image_path: str, output_path: str) -> None:
    """Redimensiona imagem para 256x256 para detecção de doenças com YOLOv8"""
    print(f"[DEBUG] Redimensionando imagem para detecção: {image_path} -> {output_path}")
    
    # Carregar imagem
    img = cv2.imread(image_path)
    if img is None:
        print(f"Erro ao carregar a imagem: {image_path}")
        return
    
    # Redimensionar para 256x256
    img_resized = cv2.resize(img, (256, 256), interpolation=cv2.INTER_CUBIC)
    
    # Salvar imagem redimensionada
    cv2.imwrite(output_path, img_resized)
    print(f"[DEBUG] Imagem redimensionada salva: {output_path} (256x256)")

def detect_disease(image_path: str) -> Dict:
    """Detecta doença na imagem usando modelo YOLOv8 e retorna resultados detalhados"""
    if detection_model is None:
        raise ValueError("Modelo de detecção não está carregado")
    
    # Fazer inferência
    results = detection_model.predict(image_path, conf=0.3, save=False)
    
    print(f"[DEBUG] Número de resultados: {len(results)}")
    
    # Verificar se há resultados
    if len(results) == 0:
        return {"disease": "indefinido", "detections": [], "confidence": 0.0}
    
    result = results[0]
    
    # Verificar se há detecções
    if result.boxes is None or len(result.boxes) == 0:
        print("[DEBUG] Nenhuma detecção encontrada")
        return {"disease": "indefinido", "detections": [], "confidence": 0.0}
    
    # Processar detecções baseado no código fornecido
    detections = []
    
    for box, conf, cls in zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls):
        detection = {
            'bbox': box.cpu().numpy().tolist(),  # [x_min, y_min, x_max, y_max]
            'confidence': float(conf.cpu().numpy()),  # Confidence score
            'class_id': int(cls.cpu().numpy()),  # Class ID
            'class_name': result.names[int(cls.cpu().numpy())]  # Class name
        }
        detections.append(detection)
        print(f"[DEBUG] Detecção: {detection}")
    
    # Ordenar por confiança (maior primeiro)
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Determinar doença principal (maior confiança)
    if detections:
        main_detection = detections[0]
        disease_name = main_detection['class_name'].lower()
        confidence = main_detection['confidence']
        
        print(f"[DEBUG] Doença principal detectada: {disease_name} (conf: {confidence:.3f})")
        
        return {
            "disease": disease_name,
            "detections": detections,
            "confidence": confidence
        }
    else:
        return {"disease": "indefinido", "detections": [], "confidence": 0.0}

def plot_detections(image_path: str, detections: List[Dict], output_path: str) -> None:
    """Plota bounding boxes com confidence na imagem"""
    import cv2
    
    # Carregar imagem original
    img = cv2.imread(image_path)
    if img is None:
        print(f"Erro ao carregar imagem para plotagem: {image_path}")
        return
    
    # Cores para diferentes classes (BGR format)
    colors = {
        'cercosporiose': (0, 255, 0),     # Verde
        'mosaico': (255, 0, 0),           # Azul  
        'mancha-bacteriana': (0, 0, 255)  # Vermelho
    }
    
    # Plotar cada detecção
    for detection in detections:
        bbox = detection['bbox']
        confidence = detection['confidence']
        class_name = detection['class_name']
        
        # Coordenadas do bounding box
        x1, y1, x2, y2 = map(int, bbox)
        
        # Cor baseada na classe
        color = colors.get(class_name.lower(), (255, 255, 255))  # Branco como padrão
        
        # Desenhar retângulo
        cv2.rectangle(img, (x1, y1), (x2, y2), color, 2)
        
        # Texto com classe e confidence
        label = f"{class_name}: {confidence:.2f}"
        label_size = cv2.getTextSize(label, cv2.FONT_HERSHEY_SIMPLEX, 0.6, 2)[0]
        
        # Fundo para o texto
        cv2.rectangle(img, (x1, y1 - label_size[1] - 10), (x1 + label_size[0], y1), color, -1)
        
        # Texto
        cv2.putText(img, label, (x1, y1 - 5), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)
    
    # Salvar imagem com detecções
    cv2.imwrite(output_path, img)
    print(f"[DEBUG] Imagem com detecções salva: {output_path}")

def calcular_severidade(image_path_processada: str, plot_path: str) -> float:
    """Calcula severidade seguindo exatamente o algoritmo de referência"""
    img = cv2.imread(image_path_processada)
    if img is None:
        print(f"Erro ao carregar a imagem: {image_path_processada}")
        return 0.0
    
    # Inferência YOLO
    results = model.predict(img, conf=0.6)
    combined_mask = np.zeros_like(img[:, :, 0], dtype=np.float32)
    
    for result in results:
        if result.masks is not None:
            for mask in result.masks.data:
                combined_mask += mask.cpu().numpy()
    
    combined_mask = (combined_mask > 0).astype(np.uint8) * 255

    # Encontrar contornos das lesões na máscara combinada
    lesion_contours, _ = cv2.findContours(combined_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # Criar máscara vermelha para o overlay
    red_mask = np.zeros_like(img)
    red_mask[:, :, 2] = combined_mask

    # Criar overlay com a máscara vermelha (lesões)
    overlay = cv2.addWeighted(img, 0.7, red_mask, 0.3, 0)

    # Desenhar contornos das lesões em azul para melhor visualização
    cv2.drawContours(overlay, lesion_contours, -1, (255, 255, 0), 1)  # Amarelo brilhante para os contornos

    # ALGORITMO MELHORADO PARA DETECTAR FOLHA
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    
    # Aplicar threshold invertido para folhas que são mais escuras que o fundo
    _, thresh = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    
    # Aplicar operações morfológicas para limpar a imagem
    kernel = np.ones((5, 5), np.uint8)
    # Usar erosão para remover ruído
    dilated = cv2.erode(thresh, kernel, iterations=1)
    
    # Encontrar contornos
    contours, _ = cv2.findContours(dilated, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    
    if not contours:
        print("Nenhum contorno encontrado")
        return 0.0
    
    # Ordenar contornos por área
    contours = sorted(contours, key=cv2.contourArea, reverse=True)
    
    print(f"[DEBUG] Total de contornos encontrados: {len(contours)}")
    for i, c in enumerate(contours[:3]):  # Debug dos 3 maiores contornos
        area = cv2.contourArea(c)
        print(f"[DEBUG] Contorno {i}: área = {area}")
    
    # Lógica melhorada: pegar o maior contorno que não seja o fundo
    # O fundo geralmente é o maior contorno, então pegamos o segundo
    if len(contours) >= 2:
        # Verificar se o primeiro contorno não é muito grande (provavelmente o fundo)
        area_primeiro = cv2.contourArea(contours[0])
        area_segundo = cv2.contourArea(contours[1])
        
        # Se o primeiro contorno for muito maior que o segundo, usar o segundo
        if area_primeiro > area_segundo * 3:
            leaf_contour = contours[1]
            print(f"[DEBUG] Usando segundo contorno (primeiro muito grande)")
        else:
            leaf_contour = contours[0]
            print(f"[DEBUG] Usando primeiro contorno")
    else:
        leaf_contour = contours[0] if contours else None
        print(f"[DEBUG] Usando único contorno disponível")
    
    if leaf_contour is None:
        print(f"Nenhum contorno válido encontrado na imagem")
        return 0.0
    
    area_folha = cv2.contourArea(leaf_contour)
    print(f"[DEBUG] Área da folha selecionada: {area_folha}")
    
    if area_folha == 0:
        print(f"Área da folha inválida")
        return 0.0
    
    lesion_area = np.sum(combined_mask == 255)
    severity = (lesion_area / area_folha * 100)
    
    # Desenhar contorno da folha
    cv2.drawContours(overlay, [leaf_contour], -1, (0, 255, 255), 2)
    cv2.putText(overlay, f"Severidade: {severity:.2f}%", (10, 30),
                cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 255, 255), 2, cv2.LINE_AA)
    
    cv2.imwrite(plot_path, overlay)
    print(f"Plot salvo em: {plot_path}")
    
    return severity

# --- Endpoint da API ---
@app.route("/predict", methods=["POST"])
def predict():
    if 'file' not in request.json:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    # Decodifica a imagem recebida em base64
    image_data_b64 = request.json['file']
    try:
        image_data = base64.b64decode(image_data_b64)
    except Exception as e:
        return jsonify({"error": f"Erro ao decodificar base64: {str(e)}"}), 400

    # Salva a imagem com um nome único para evitar conflitos
    filename = f"{uuid.uuid4()}.jpg"
    input_path = os.path.join(INPUT_FOLDER, filename)
    output_path = os.path.join(OUTPUT_FOLDER, filename)
    plot_path = os.path.join(PLOTS_FOLDER, filename)

    with open(input_path, "wb") as f:
        f.write(image_data)

    try:
        # Executa a lógica de IA
        print(f"Processando arquivo: {filename}")
        preprocess_image(input_path, output_path)
        severity = calcular_severidade(output_path, plot_path)

        # Codifica a imagem de resultado (plot) para enviar de volta
        with open(plot_path, "rb") as f:
            plot_image_b64 = base64.b64encode(f.read()).decode('utf-8')

        # Limpa os arquivos temporários
        os.remove(input_path)
        os.remove(output_path)
        os.remove(plot_path)

        # Gerar recomendações baseadas na severidade
        if severity < 5:
            recomendacao = {
                "tipo": "calda_bordalesa",
                "titulo": "Recomendação: Calda Bordalesa",
                "descricao": "Para severidades médias abaixo de 5% recomenda-se o uso de tratamentos alternativos, como a utilização de calda bordalesa.",
                "instrucoes": [
                    "1. Diluição do sulfato de cobre: Pegue 200 g de sulfato de cobre e coloque-o dentro de um pano, formando um saquinho. Amarre o saquinho na ponta de uma vara e mergulhe em aproximadamente 5 litros de água fria ou morna por 4 a 24 horas.",
                    "2. Preparo do leite de cal: Coloque 200 g de cal virgem em 2 litros de água e misture bem.",
                    "3. Mistura dos ingredientes: Derrame vagarosamente o sulfato de cobre diluído sobre o leite de cal.",
                    "4. Verificação da acidez: Mergulhe um objeto de ferro na calda por 3 minutos. Se escurecer, acrescente cal.",
                    "5. Filtragem e aplicação: Coe a calda e aplique com pulverizador."
                ],
                "fonte": "BRASIL. Ministério da Agricultura, Pecuária e Abastecimento. Calda bordalesa. Coordenação de Agroecologia, [s.d.]. Disponível em: <www.agricultura.gov.br/desenvolvimento-sustentavel/organicos>."
            }
        else:
            recomendacao = {
                "tipo": "fungicida",
                "titulo": "Recomendação: Uso de Fungicida",
                "descricao": "Devido à severidade média superior a 5%, recomenda-se o uso de fungicida.",
                "instrucoes": [
                    "Procure orientação técnica para escolha e aplicação adequada do fungicida.",
                    "Siga rigorosamente as instruções do fabricante.",
                    "Respeite o período de carência antes da colheita."
                ],
                "fonte": "Orientação técnica recomendada para casos de alta severidade."
            }

        # Retorna o resultado
        return jsonify({
            "severity": round(severity, 2),
            "plot_image_b64": plot_image_b64,
            "recomendacao": recomendacao
        })

    except Exception as e:
        print(f"Erro durante o processamento: {e}")
        return jsonify({"error": f"Erro interno no servidor: {str(e)}"}), 500

@app.route("/detect_disease", methods=["POST"])
def detect_disease_endpoint():
    """Endpoint para detectar doença usando YOLOv8"""
    if 'file' not in request.json:
        return jsonify({"error": "Nenhum arquivo enviado"}), 400
    
    # Verificar se o modelo está carregado
    if detection_model is None:
        return jsonify({"error": "Modelo de detecção não está disponível"}), 503
    
    # Decodificar imagem base64
    image_data_b64 = request.json['file']
    try:
        image_data = base64.b64decode(image_data_b64)
    except Exception as e:
        return jsonify({"error": f"Erro ao decodificar base64: {str(e)}"}), 400

    # Salvar imagem temporária
    filename = f"detect_{uuid.uuid4()}.jpg"
    input_path = os.path.join(INPUT_FOLDER, filename)
    processed_path = os.path.join(OUTPUT_FOLDER, f"processed_{filename}")
    plot_path = os.path.join(PLOTS_FOLDER, f"plot_{filename}")

    with open(input_path, "wb") as f:
        f.write(image_data)

    try:
        # Preprocessar imagem para 256x256
        print(f"Processando detecção para arquivo: {filename}")
        preprocess_image_detection(input_path, processed_path)
        
        # Detectar doença
        detection_result = detect_disease(processed_path)
        detected_disease = detection_result["disease"]
        detections = detection_result["detections"]
        confidence = detection_result["confidence"]
        
        # Plotar detecções na imagem original (redimensionada)
        plot_detections(processed_path, detections, plot_path)
        
        # Codificar imagem com detecções para envio
        plot_image_b64 = ""
        if os.path.exists(plot_path):
            with open(plot_path, "rb") as f:
                plot_image_b64 = base64.b64encode(f.read()).decode('utf-8')

        # Limpar arquivos temporários
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(processed_path):
            os.remove(processed_path)
        if os.path.exists(plot_path):
            os.remove(plot_path)

        # Retornar resultado detalhado
        return jsonify({
            "detected_disease": detected_disease,
            "detections": detections,
            "confidence": confidence,
            "plot_image_b64": plot_image_b64,
            "success": True
        })

    except Exception as e:
        print(f"Erro durante a detecção: {e}")
        # Limpar arquivos em caso de erro
        if os.path.exists(input_path):
            os.remove(input_path)
        if os.path.exists(processed_path):
            os.remove(processed_path)
        return jsonify({"error": f"Erro interno no servidor: {str(e)}"}), 500

if __name__ == "__main__":
    # A porta é gerenciada pelo Cloud Run, não precisamos definir aqui.
    app.run(host="0.0.0.0", port=int(os.environ.get("PORT", 8080)))