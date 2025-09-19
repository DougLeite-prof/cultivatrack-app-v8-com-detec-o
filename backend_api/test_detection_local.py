#!/usr/bin/env python3
"""
Script para testar localmente a detecção de doenças
Uso: python test_detection_local.py caminho_da_imagem
"""

import sys
import os
import cv2
import numpy as np
from ultralytics import YOLO
import glob
from typing import Dict, List

def test_detection_local(image_path: str):
    """Testa a detecção localmente usando a mesma lógica do servidor"""
    
    # Carregar modelo
    model_path = "modelo-deteccao.pt"
    if not os.path.exists(model_path):
        print(f"❌ Modelo não encontrado: {model_path}")
        return
    
    print(f"📁 Carregando modelo: {model_path}")
    
    # Carregar modelo com configuração de compatibilidade
    try:
        model = YOLO(model_path)
    except Exception as e:
        print(f"⚠️  Problema de compatibilidade PyTorch: {e}")
        print("💡 Use o container Docker para testes ou atualize o PyTorch")
        return
    
    print("✅ Modelo carregado com sucesso!")
    
    # Verificar se a imagem existe
    if not os.path.exists(image_path):
        print(f"❌ Imagem não encontrada: {image_path}")
        return
    
    print(f"📷 Processando imagem: {image_path}")
    
    # Redimensionar para 256x256 (igual ao servidor)
    img = cv2.imread(image_path)
    if img is None:
        print(f"❌ Erro ao carregar imagem: {image_path}")
        return
    
    print(f"📐 Dimensões originais: {img.shape}")
    img_resized = cv2.resize(img, (256, 256), interpolation=cv2.INTER_CUBIC)
    
    # Salvar imagem redimensionada temporariamente
    temp_path = "temp_resized_256.jpg"
    cv2.imwrite(temp_path, img_resized)
    print(f"✅ Imagem redimensionada para 256x256")
    
    # Fazer inferência
    print("🔍 Executando inferência...")
    results = model.predict(temp_path, conf=0.3, save=False)
    
    print(f"📊 Número de resultados: {len(results)}")
    
    if len(results) == 0:
        print("❌ Nenhum resultado de inferência")
        return
    
    result = results[0]
    
    if result.boxes is None or len(result.boxes) == 0:
        print("❌ Nenhuma detecção encontrada")
        return
    
    print(f"🎯 Encontradas {len(result.boxes)} detecções:")
    
    # Processar detecções
    detections = []
    
    for i, (box, conf, cls) in enumerate(zip(result.boxes.xyxy, result.boxes.conf, result.boxes.cls)):
        detection = {
            'bbox': box.cpu().numpy().tolist(),
            'confidence': float(conf.cpu().numpy()),
            'class_id': int(cls.cpu().numpy()),
            'class_name': result.names[int(cls.cpu().numpy())]
        }
        detections.append(detection)
        
        print(f"  📌 Detecção {i+1}:")
        print(f"     🏷️  Classe: {detection['class_name']}")
        print(f"     💯 Confiança: {detection['confidence']:.3f} ({detection['confidence']:.1%})")
        print(f"     📦 BBox: {detection['bbox']}")
        print(f"     🆔 ID: {detection['class_id']}")
    
    # Ordenar por confiança
    detections.sort(key=lambda x: x['confidence'], reverse=True)
    
    # Resultado principal
    main_detection = detections[0]
    print(f"\n🏆 RESULTADO PRINCIPAL:")
    print(f"   🎯 Doença: {main_detection['class_name']}")
    print(f"   💯 Confiança: {main_detection['confidence']:.3f} ({main_detection['confidence']:.1%})")
    
    # Plotar detecções (igual ao servidor)
    plot_path = "test_detection_result.jpg"
    plot_detections_local(temp_path, detections, plot_path)
    
    # Limpar arquivo temporário
    if os.path.exists(temp_path):
        os.remove(temp_path)
    
    print(f"🖼️  Resultado salvo em: {plot_path}")
    print("✅ Teste concluído!")

def plot_detections_local(image_path: str, detections: List[Dict], output_path: str) -> None:
    """Plota bounding boxes com confidence na imagem"""
    
    # Carregar imagem
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("❌ Uso: python test_detection_local.py <caminho_da_imagem>")
        print("📝 Exemplo: python test_detection_local.py ../frontend_flet/assets/mosaico.jpg")
        sys.exit(1)
    
    image_path = sys.argv[1]
    test_detection_local(image_path)
