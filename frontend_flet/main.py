# main.py (VERSÃO FINAL, COMPLETA E PRONTA PARA CLOUD)

# Imports leves necessários para a interface
import flet as ft
import flet.fastapi as flet_fastapi
import requests
import base64
import time
import threading
from datetime import datetime, timedelta, timezone
import json
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import io
import numpy as np
from astral import LocationInfo
from astral.sun import sun
from typing import Dict, Tuple, Optional, List
import requests_cache
import openmeteo_requests
from retry_requests import retry
import os


# --- URL DA SUA API (Preenchida com a URL do seu serviço Cloud Run) ---
# Substitua pela URL real da sua API quando implantada
API_URL = "https://cultivatrack-api-317628613130.southamerica-east1.run.app"

# --- Constantes e Funções Leves (Clima, Gráficos, etc.) ---
WEATHER_CODES = {
    0: "Céu limpo", 1: "Predominantemente claro", 2: "Parcialmente nublado", 3: "Nublado", 45: "Nevoeiro",
    48: "Nevoeiro com geada", 51: "Garoa leve", 53: "Garoa moderada", 55: "Garoa intensa",
    56: "Garoa congelante leve", 57: "Garoa congelante intensa", 61: "Chuva leve", 63: "Chuva moderada",
    65: "Chuva forte", 66: "Chuva congelante leve", 67: "Chuva congelante forte", 71: "Neve leve",
    73: "Neve moderada", 75: "Neve forte", 77: "Grãos de neve", 80: "Aguaceiros de chuva leves",
    81: "Aguaceiros de chuva moderados", 82: "Aguaceiros de chuva fortes", 85: "Aguaceiros de neve leves",
    86: "Aguaceiros de neve fortes", 95: "Trovoada leve ou moderada", 96: "Trovoada com granizo leve",
    99: "Trovoada com granizo forte"
}

OPENMETEO_TIMEZONE = "America/Sao_Paulo"
_cache_session = requests_cache.CachedSession('/tmp/http_cache', expire_after=3600)
_retry_session = retry(_cache_session, retries=5, backoff_factor=0.2)
_openmeteo_client = openmeteo_requests.Client(session=_retry_session)

CITY_COORDINATES = {
    "Aracaju/SE": {"lat": -10.9475, "lon": -37.0731},
    "Itabaiana/SE": {"lat": -10.2357, "lon": -37.4261},
    "Lagarto/SE": {"lat": -10.9145, "lon": -37.6639},
}

# Dicionário global para estado compartilhado
APP_STATE = {}

# === FUNÇÕES GLOBAIS DE UI ===

# Função para criar botão de download PDF que funciona DEFINITIVAMENTE na nuvem
def criar_botao_pdf_simple():
    """Cria um botão para download do PDF otimizado para nuvem"""
    def download_pdf(e):
        try:
            # Obter referência da página
            page = e.page if hasattr(e, 'page') else e.control.page
            
            # ESTRATÉGIA MÚLTIPLA: Tentar várias abordagens
            
            # ABORDAGEM 1: Nova rota API específica para PDF
            try:
                page.launch_url("/api/pdf/calda-bordalesa")
                return
            except Exception:
                pass
            
            # ABORDAGEM 2: Rota API para download forçado  
            try:
                page.launch_url("/api/download/calda-bordalesa.pdf")
                return
            except Exception:
                pass
            
            # ABORDAGEM 3: Rota API assets
            try:
                page.launch_url("/api/assets/calda-bordalesa.pdf")
                return
            except Exception:
                pass
            
            # ABORDAGEM 4: URL estática (fallback)
            try:
                page.launch_url("/static/calda-bordalesa.pdf")
                return
            except Exception:
                pass
            
            # ABORDAGEM 5: Data URI com base64 (mais confiável)
            try:
                pdf_path = os.path.join("assets", "calda-bordalesa.pdf")
                
                if os.path.exists(pdf_path):
                    with open(pdf_path, "rb") as f:
                        pdf_b64 = base64.b64encode(f.read()).decode('utf-8')
                    
                    data_uri = f"data:application/pdf;base64,{pdf_b64}"
                    page.launch_url(data_uri)
                    return
            except Exception:
                pass
            
            # ABORDAGEM 6: Forçar download via JavaScript (última tentativa)
            try:
                if hasattr(page, 'run_javascript'):
                    pdf_path = os.path.join("assets", "calda-bordalesa.pdf")
                    if os.path.exists(pdf_path):
                        with open(pdf_path, "rb") as f:
                            pdf_b64 = base64.b64encode(f.read()).decode('utf-8')
                        
                        js_code = f"""
                        try {{
                            var blob = new Blob([Uint8Array.from(atob('{pdf_b64}'), c => c.charCodeAt(0))], {{type: 'application/pdf'}});
                            var url = window.URL.createObjectURL(blob);
                            var a = document.createElement('a');
                            a.href = url;
                            a.download = 'calda-bordalesa.pdf';
                            a.target = '_blank';
                            document.body.appendChild(a);
                            a.click();
                            window.URL.revokeObjectURL(url);
                            document.body.removeChild(a);
                        }} catch(jsErr) {{
                            console.error('Erro no JavaScript:', jsErr);
                        }}
                        """
                        page.run_javascript(js_code)
                        return
            except Exception:
                pass
                
        except Exception as ex:
            print(f"Erro ao abrir PDF: {str(ex)}")
    
    return ft.Row([
        ft.IconButton(
            icon=ft.Icons.PICTURE_AS_PDF, 
            on_click=download_pdf,
            tooltip="Clique para baixar o PDF das instruções",
            icon_color="red"
        ),
        ft.Text("Baixar PDF com instruções")
    ], alignment=ft.MainAxisAlignment.CENTER)

# Função para carregar imagem como base64 (fallback)
def load_image_as_base64(image_path: str) -> Optional[str]:
    """Carrega uma imagem como base64 para uso em caso de falha dos assets estáticos"""
    try:
        full_path = os.path.join("assets", image_path)
        if os.path.exists(full_path):
            with open(full_path, "rb") as f:
                return base64.b64encode(f.read()).decode('utf-8')
    except Exception:
        pass
    return None

def create_image_with_fallback(src_path: str, **kwargs) -> ft.Image:
    """Cria uma imagem com fallback para base64 se assets estáticos falharem"""
    # Primeiro tenta carregar via asset estático
    img = ft.Image(src=f"/assets/{src_path}", **kwargs)
    
    # Se não conseguir, adiciona error_content
    if "error_content" not in kwargs:
        # Tenta carregar como base64 em caso de erro
        b64_data = load_image_as_base64(src_path)
        if b64_data:
            kwargs["error_content"] = ft.Image(src_base64=b64_data, **{k: v for k, v in kwargs.items() if k not in ["src", "error_content"]})
        else:
            kwargs["error_content"] = ft.Text("Imagem não encontrada", color="red")
        
        img = ft.Image(src=f"/assets/{src_path}", **kwargs)
    
    return img

def create_dropdown(label: str, options: List[str], style: Dict) -> ft.Dropdown:
    return ft.Dropdown(label=label, options=[ft.dropdown.Option(opt) for opt in options], **style)

def get_sun_times(lat: float, lon: float) -> Tuple[datetime, datetime]:
    cidade = LocationInfo(latitude=lat, longitude=lon)
    tz = datetime.now().astimezone().tzinfo or timezone.utc
    s = sun(cidade.observer, date=datetime.now().date(), tzinfo=tz)
    return s['sunrise'], s['sunset']

# --- Funções de Clima (mantidas do código original) ---

def _build_time_series(start_unix: int, end_unix: int, interval_seconds: int, tz_offset: int) -> List[str]:
    times = []
    for ts in range(int(start_unix), int(end_unix), int(interval_seconds)):
        dt = datetime.fromtimestamp(ts, timezone(timedelta(seconds=tz_offset)))
        times.append(dt.isoformat())
    return times

def _adjust_wind_speed_10m_to_2m(wind_speed_10m_ms: float, roughness_length_m: float = 0.03) -> float:
    try:
        if wind_speed_10m_ms is None: return None
        numerator = np.log(2.0 / roughness_length_m)
        denominator = np.log(10.0 / roughness_length_m)
        factor = numerator / denominator
        return float(wind_speed_10m_ms * factor)
    except Exception:
        return float(wind_speed_10m_ms)

def get_weather_data(lat: float, lon: float) -> Optional[Dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "weather_code"],
        "timezone": OPENMETEO_TIMEZONE, "windspeed_unit": "ms", "past_days": 0, "forecast_days": 1
    }
    responses = _openmeteo_client.weather_api(url, params=params)
    if not responses: return None
    response = responses[0]
    hourly = response.Hourly()
    tz_offset = response.UtcOffsetSeconds()
    start, end, interval = hourly.Time(), hourly.TimeEnd(), hourly.Interval()
    times = _build_time_series(start, end, interval, tz_offset)
    now_local = datetime.now(timezone(timedelta(seconds=tz_offset)))
    try:
        parsed_times = [datetime.fromisoformat(t) for t in times]
        idx_candidates = [i for i, t in enumerate(parsed_times) if t <= now_local]
        idx = idx_candidates[-1] if idx_candidates else 0
    except Exception:
        idx = max(0, min(len(times) - 1, int((now_local - datetime.fromtimestamp(start, timezone(timedelta(seconds=tz_offset)))).total_seconds() // interval)))
    
    temperature = round(float(hourly.Variables(0).ValuesAsNumpy()[idx]), 1)
    humidity = round(float(hourly.Variables(1).ValuesAsNumpy()[idx]), 1)
    precip_prob = round(float(hourly.Variables(2).ValuesAsNumpy()[idx]), 1) if hourly.VariablesLength() > 2 else 0.0
    wind10 = float(hourly.Variables(3).ValuesAsNumpy()[idx])
    weather_code = int(hourly.Variables(4).ValuesAsNumpy()[idx])
    wind2 = _adjust_wind_speed_10m_to_2m(wind10)
    
    return {
        "data": { "values": {
            "temperature": temperature, "humidity": humidity, "precipitationProbability": precip_prob,
            "windSpeed": wind2, "weatherCode": weather_code
        }}
    }

def get_weather_data_prev(lat: float, lon: float) -> Optional[Dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon,
        "hourly": ["temperature_2m", "relative_humidity_2m", "precipitation_probability", "wind_speed_10m", "weather_code"],
        "timezone": OPENMETEO_TIMEZONE, "windspeed_unit": "ms", "forecast_days": 3
    }
    responses = _openmeteo_client.weather_api(url, params=params)
    if not responses: return None
    response = responses[0]
    hourly = response.Hourly()
    tz_offset = response.UtcOffsetSeconds()
    start, end, interval = hourly.Time(), hourly.TimeEnd(), hourly.Interval()
    times = _build_time_series(start, end, interval, tz_offset)
    temp, rh, pp, wind10, wcode = (
        hourly.Variables(0).ValuesAsNumpy(), hourly.Variables(1).ValuesAsNumpy(),
        hourly.Variables(2).ValuesAsNumpy() if hourly.VariablesLength() > 2 else np.zeros_like(hourly.Variables(0).ValuesAsNumpy()),
        hourly.Variables(3).ValuesAsNumpy(), hourly.Variables(4).ValuesAsNumpy()
    )
    timeline = [{
        "time": times[i],
        "values": {
            "temperature": round(float(temp[i]), 1), "humidity": round(float(rh[i]), 1),
            "precipitationProbability": round(float(pp[i]), 1),
            "windSpeed": float(_adjust_wind_speed_10m_to_2m(float(wind10[i]))),
            "weatherCode": int(wcode[i])
        }
    } for i in range(len(times))]
    return {"timelines": {"hourly": timeline}}

def get_weather_history(lat: float, lon: float) -> Optional[Dict]:
    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat, "longitude": lon, "hourly": ["et0_fao_evapotranspiration"],
        "daily": ["et0_fao_evapotranspiration"], "timezone": OPENMETEO_TIMEZONE,
        "past_days": 1, "forecast_days": 1
    }
    responses = _openmeteo_client.weather_api(url, params=params)
    if not responses: return None
    response = responses[0]
    tz_offset = response.UtcOffsetSeconds()
    daily_values = response.Daily().Variables(0).ValuesAsNumpy()
    evap_daily = float(daily_values[0]) if len(daily_values) > 0 else None
    
    hourly = response.Hourly()
    start, end, interval = hourly.Time(), hourly.TimeEnd(), hourly.Interval()
    times = _build_time_series(start, end, interval, tz_offset)
    et0_hourly = hourly.Variables(0).ValuesAsNumpy()
    
    now_local = datetime.now(timezone(timedelta(seconds=tz_offset)))
    try:
        parsed_times = [datetime.fromisoformat(t) for t in times]
        idx_candidates = [i for i, t in enumerate(parsed_times) if t <= now_local]
        idx_now = idx_candidates[-1] if idx_candidates else 0
    except Exception:
        idx_now = len(et0_hourly) - 1 if len(et0_hourly) else 0

    return { "timelines": {
        "daily": [{"values": {"evapotranspirationSum": evap_daily}}],
        "hourly": [{"time": times[i], "values": {"evapotranspiration": float(et0_hourly[i])}} for i in range(len(times))],
        "current": {"time": times[idx_now] if times else None, "value": float(et0_hourly[idx_now]) if len(et0_hourly) else None}
    }}

def select_next_hours(hourly_list: List[Dict], hours: int = 48) -> List[Dict]:
    try:
        now_local = datetime.now().astimezone()
        future = []
        for entry in hourly_list:
            time_str = entry.get("time")
            if not time_str: continue
            try:
                entry_dt = datetime.fromisoformat(time_str)
                if entry_dt > now_local: future.append(entry)
            except Exception: continue
        return future[:hours]
    except Exception:
        return hourly_list[:hours]

def generate_risk_graph(classificacao_list: List[str]) -> str:
    risk_map = {"Risco Baixo": 1, "Risco Moderado": 2, "Risco Elevado": 3, "Risco Alto": 4}
    risk_values = [risk_map.get(r, 1) for r in classificacao_list]
    x_values = list(range(len(risk_values)))
    start_time = datetime.now(timezone(timedelta(hours=-3)))
    labels = [(start_time + timedelta(hours=i + 1)).strftime("%H") for i in range(len(risk_values))]
    tick_positions, tick_labels = x_values[::3], labels[::3]
    plt.figure(figsize=(8, 5))
    for low, high, color in [(0.5, 1.5, '#4CAF50'), (1.5, 2.5, '#FFCA28'), (2.5, 3.5, '#FF5722'), (3.5, 4.5, '#D32F2F')]:
        plt.axhspan(low, high, facecolor=color, alpha=0.4)
    bar_colors = ['#4CAF50' if v == 1 else '#FFCA28' if v == 2 else '#FF5722' if v == 3 else '#D32F2F' for v in risk_values]
    plt.bar(x_values, risk_values, color=bar_colors, width=0.7, alpha=0.8, edgecolor='#1976D2', linewidth=1)
    plt.xlabel("Hora Local", fontsize=14, fontweight='bold', color='#424242')
    plt.title("Gráfico de Risco Climático para Cercosporiose", fontsize=16, fontweight='bold', color='#2E7D32')
    plt.yticks([1, 2, 3, 4], ["Baixo", "Moderado", "Elevado", "Alto"], fontsize=12, color='#424242')
    plt.xticks(tick_positions, tick_labels, fontsize=12, color='#424242')
    plt.grid(True, linestyle='--', alpha=0.7)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format='png', dpi=150)
    plt.close()
    return base64.b64encode(buf.getvalue()).decode('utf-8')

# --- LÓGICA DA INTERFACE ---

def main(page: ft.Page):
    page.title = "CultivaTrack"
    page.scroll = ft.ScrollMode.ADAPTIVE
    page.window_width = 450
    page.window_height = 800

    # Limpa o estado da aplicação a cada recarregamento da página
    APP_STATE.clear()
    APP_STATE["uploaded_files_data"] = [] # Guarda {"name": str, "bytes": bytes}
    
    # Função helper para obter URL absoluta
    def get_absolute_url(path: str) -> str:
        """Retorna a URL absoluta para um recurso"""
        # Tenta obter a URL base da página
        if hasattr(page, 'url'):
            # Remove o path atual e mantém apenas o domínio
            base_url = page.url.split('?')[0]  # Remove query params
            if base_url.endswith('/'):
                base_url = base_url[:-1]
            # Se já tem um domínio completo
            if base_url.startswith('http'):
                # Remove qualquer path após o domínio:porta
                parts = base_url.split('/')
                base_url = '/'.join(parts[:3])  # http://domain:port
                return f"{base_url}{path}"
        # Fallback para localhost
        return f"http://localhost:8000{path}"
    

    
    # Função alternativa para criar download direto via base64
    def criar_botao_pdf_download():
        """Cria um botão de download que funciona via base64"""
        try:
            # Lê o arquivo PDF e converte para base64
            pdf_path = os.path.join("assets", "calda-bordalesa.pdf")
            if os.path.exists(pdf_path):
                with open(pdf_path, "rb") as f:
                    pdf_b64 = base64.b64encode(f.read()).decode('utf-8')
                
                # Cria um container com HTML customizado para download
                return ft.Container(
                    content=ft.Row([
                        ft.IconButton(
                            icon=ft.Icons.PICTURE_AS_PDF,
                            on_click=lambda e: page.run_javascript(f"""
                                var blob = new Blob([Uint8Array.from(atob('{pdf_b64}'), c => c.charCodeAt(0))], {{type: 'application/pdf'}});
                                var url = window.URL.createObjectURL(blob);
                                var a = document.createElement('a');
                                a.href = url;
                                a.download = 'calda-bordalesa.pdf';
                                a.target = '_blank';
                                document.body.appendChild(a);
                                a.click();
                                window.URL.revokeObjectURL(url);
                                document.body.removeChild(a);
                            """) if hasattr(page, 'run_javascript') else page.launch_url("/download/calda-bordalesa.pdf")
                        ),
                        ft.Text("Baixar instruções em PDF")
                    ], alignment=ft.MainAxisAlignment.CENTER)
                )
        except Exception as ex:
            # Fallback para o método padrão
            return ft.Row([
                ft.IconButton(icon=ft.Icons.PICTURE_AS_PDF, on_click=lambda _: page.launch_url("/download/calda-bordalesa.pdf")),
                ft.Text("Baixar instruções em PDF")
            ], alignment=ft.MainAxisAlignment.CENTER)

    # Estilos
    page.theme = ft.Theme(
        color_scheme=ft.ColorScheme(
            primary="#4CAF50", primary_container="#C8E6C9", on_primary=ft.Colors.WHITE,
            secondary="#FF9800", on_secondary=ft.Colors.WHITE, surface="#F5F5F5", background="#E8F5E9",
        ), font_family="Roboto"
    )
    page.bgcolor = "#E8F5E9"
    dropdown_style = {"border_radius": 15, "bgcolor": "#F1F8E9", "border_color": "#81C784", "text_size": 18, "content_padding": 20, "focused_border_color": "#4CAF50", "width": 380}
    button_style = ft.ButtonStyle(shape=ft.RoundedRectangleBorder(radius=15), padding=25, bgcolor="#4CAF50", color=ft.Colors.WHITE, elevation=8, animation_duration=300)

    # --- Navegação e Funções de Tela ---

    def mostrar_tela_avaliar_severidade(e):
        # Limpar estado de upload (baseado no main-referencia.py)
        APP_STATE["uploaded_files_data"] = []
            
        page.clean()
        
        # Header (igual ao código original)
        header_avalia = ft.Row([
            ft.Icon(ft.Icons.SEARCH, size=40, color="white"),
            ft.Text("Avaliar Severidade com IA", size=26, weight=ft.FontWeight.BOLD, color="#1976D2")
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

        # Cálculo de amostragem (igual ao código original)
        row_cult_unit = ft.Row([
            ft.TextField(label="Tamanho do cultivo", hint_text="Digite o valor", width=150, bgcolor="#F1F8E9", border_color="#81C784"),
            ft.Dropdown(label="Unidade", options=[ft.dropdown.Option("ha"), ft.dropdown.Option("tarefas")], value="ha", width=150, bgcolor="#F1F8E9", border_color="#81C784")
        ], alignment=ft.MainAxisAlignment.CENTER, spacing=15)

        def calcular_amostragem(e):
            try:
                value = float(row_cult_unit.controls[0].value)
                unit = row_cult_unit.controls[1].value
                ha = value if unit == "ha" else value / 3.3
                num_plantas = round((ha * 26) / 0.5)
                num_folhas = num_plantas * 3

                APP_STATE["num_folhas_recomendadas"] = num_folhas

                # Limpar controles existentes
                resultado_container.content = ft.Column(controls=[])

                # Adicionar texto com informações
                resultado_container.content.controls.append(
                    ft.Text(f"Para {value} {unit}:\n\n• Total de plantas a amostrar: {num_plantas}\n• Total de folhas a coletar: {num_folhas}",
                        size=16, color="#424242", weight=ft.FontWeight.BOLD)
                )

                # Adicionar instruções de coleta com imagens (igual ao código original)
                resultado_container.content.controls.append(
                    ft.Text("Como coletar:\n\n1. Caminhe em padrão diagonal pela plantação conforme a ilustração abaixo.",
                        size=16, color="#424242")
                )

                resultado_container.content.controls.append(
                    ft.Container(
                        content=create_image_with_fallback("ilustracao diagonal.jpg", width=350, height=220, fit=ft.ImageFit.CONTAIN, border_radius=10),
                        alignment=ft.alignment.center, margin=ft.margin.only(top=10, bottom=10)
                    )
                )

                resultado_container.content.controls.append(
                    ft.Text("2. Para cada planta, colete 3 folhas em alturas diferentes (baixo, médio e alto) conforme a ilustração abaixo.",
                        size=16, color="#424242")
                )

                resultado_container.content.controls.append(
                    ft.Container(
                        content=create_image_with_fallback("terços da planta.jpg", width=350, height=220, fit=ft.ImageFit.CONTAIN, border_radius=10),
                        alignment=ft.alignment.center, margin=ft.margin.only(top=10, bottom=10)
                    )
                )

                resultado_container.visible = True
                btn_upload.disabled = False

            except ValueError:
                resultado_container.content = ft.Column([
                    ft.Text("Valor inválido. Por favor, digite um número válido.", size=16, color="#D32F2F")
                ])
                resultado_container.visible = True
                btn_upload.disabled = True

            page.update()

        btn_calcular = ft.ElevatedButton("Calcular Amostragem", on_click=calcular_amostragem, width=280, bgcolor="#4CAF50", color=ft.Colors.WHITE, style=button_style,
            content=ft.Row([ft.Icon(ft.Icons.CALCULATE, size=20, color="white"), ft.Text("Calcular Amostragem", size=18)], alignment=ft.MainAxisAlignment.CENTER, spacing=10))

        # Container para resultado
        resultado_container = ft.Container(
            content=ft.Column([], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.START, spacing=15),
            padding=25, bgcolor="#F1F8E9", border_radius=20, width=400, visible=False
        )

        container_amostragem = ft.Container(
            content=ft.Column([row_cult_unit, btn_calcular], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=25, bgcolor="#F1F8E9", border_radius=20, width=380
        )

        # Sistema de upload baseado no código original
        upload_count_text = ft.Text("Imagens carregadas: 0", size=16, color="#424242")
        upload_progress = ft.ProgressBar(width=340, color="#4CAF50", bgcolor="#E0E0E0", visible=False)
        upload_images_column = ft.Column()
        
        refresh_button = ft.IconButton(
            icon=ft.Icons.REFRESH, icon_size=24, tooltip="Atualizar",
            on_click=lambda e: update_upload_display(), icon_color="#4CAF50"
        )

        def update_upload_display():
            """Atualiza display baseado no APP_STATE (igual ao main-referencia.py)"""
            print("=== UPDATE UPLOAD DISPLAY ===")
            num_imagens = len(APP_STATE.get("uploaded_files_data", []))
            print(f"Número de imagens no estado: {num_imagens}")
            
            # Verificar dados recomendados (igual ao main-referencia.py)
            num_folhas_recomendadas = APP_STATE.get("num_folhas_recomendadas")
            if num_folhas_recomendadas and isinstance(num_folhas_recomendadas, int) and num_folhas_recomendadas > 0:
                if num_imagens == num_folhas_recomendadas:
                    status_cor = "#4CAF50"
                elif num_imagens < num_folhas_recomendadas:
                    status_cor = "#FF9800"
                else:
                    status_cor = "#D32F2F"
                upload_count_text.value = f"Imagens: {num_imagens}/{num_folhas_recomendadas} recomendadas"
                upload_count_text.color = status_cor

                # Atualizar barra de progresso
                upload_progress.visible = True
                upload_progress.value = min(1.0, num_imagens / num_folhas_recomendadas)
                upload_progress.color = status_cor
            else:
                upload_count_text.value = f"Imagens carregadas: {num_imagens}"
                upload_count_text.color = "#424242"
                upload_progress.visible = False
            
            btn_calcular_severidade.disabled = num_imagens == 0
            btn_upload.disabled = False  # Sempre habilitado após cálculo de amostragem
            upload_images_column.controls.clear()
            
            for i, file_data in enumerate(APP_STATE.get("uploaded_files_data", [])):
                # Usar filename como identificador único (igual ao main-referencia.py)
                filename = file_data['name']
                
                def create_remove_handler(file_name):
                    def remove_item(e):
                        print(f"Removendo arquivo: {file_name}")
                        # Remover por nome ao invés de índice (igual ao main-referencia.py)
                        APP_STATE["uploaded_files_data"] = [
                            f for f in APP_STATE["uploaded_files_data"] 
                            if f["name"] != file_name
                        ]
                        print(f"Arquivos restantes: {len(APP_STATE['uploaded_files_data'])}")
                        update_upload_display()
                    return remove_item
                
                size_mb = file_data.get("size", 0) / (1024*1024)
                upload_images_column.controls.append(
                    ft.Container(
                        content=ft.Row([
                            ft.Icon(ft.Icons.IMAGE, size=24, color="#1976D2"),
                            ft.Text(f"{file_data['name']} ({size_mb:.1f}MB)", size=14, color="#424242", width=220, overflow=ft.TextOverflow.VISIBLE, no_wrap=False),
                            ft.IconButton(icon=ft.Icons.CLOSE, icon_size=18, icon_color="#D32F2F", tooltip="Remover", on_click=create_remove_handler(filename))
                        ], alignment=ft.MainAxisAlignment.SPACE_BETWEEN, spacing=5),
                        padding=ft.padding.only(left=5, right=5, top=5, bottom=5),
                        margin=ft.margin.only(bottom=5), bgcolor="#F5F5F5", border_radius=10, width=320
                    )
                )

            # Configurar container para visualização
            if num_imagens > 0:
                upload_images_column.height = min(200, num_imagens * 55)
                upload_images_column.scroll = ft.ScrollMode.AUTO
                upload_images_column.width = 340
            else:
                upload_images_column.height = None
                upload_images_column.scroll = None
            
            print("Interface atualizada")
            page.update()

        def poll_uploads():
            """Sistema de polling igual ao código original"""
            update_upload_display()
            threading.Timer(3, poll_uploads).start()

        # Função para abrir página de upload HTML (baseado no main-referencia.py)
        def abrir_upload_html(e):
            print("📷 Abrindo página de upload...")
            # Abrir página HTML dedicada para upload (igual ao main-referencia.py)
            upload_url = "/upload.html"
            page.launch_url(upload_url)
            # Iniciar polling para verificar uploads
            poll_uploads()

        # Botão de upload (igual ao main-referencia.py)
        btn_upload = ft.ElevatedButton(
            "📷 Carregar Imagens", 
            on_click=abrir_upload_html,
            width=280, 
            bgcolor="#4CAF50", 
            color=ft.Colors.WHITE, 
            style=button_style, 
            disabled=True,
            content=ft.Row([
                ft.Icon(ft.Icons.CAMERA_ALT_OUTLINED, size=20, color="white"), 
                ft.Text("Carregar Imagens", size=18)
            ], alignment=ft.MainAxisAlignment.CENTER, spacing=10)
        )

        container_upload = ft.Container(
            content=ft.Column([
                ft.Row([upload_count_text, refresh_button], alignment=ft.MainAxisAlignment.CENTER),
                upload_progress, upload_images_column, btn_upload
            ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20),
            padding=25, bgcolor="#F1F8E9", border_radius=20, width=380
        )

        # Processamento IA (simplificado)
        progress_ring = ft.ProgressRing(visible=False, width=60, height=60, color="#4CAF50")
        progress_text = ft.Text("", size=18, color="#2E7D32")
        results_container = ft.Column(alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)

        def calcular_severidade_callback(e):
            if not APP_STATE.get("uploaded_files_data"):
                progress_text.value = "Nenhuma imagem carregada!"
                page.update()
                return

            def processing():
                try:
                progress_text.value, progress_ring.visible = "Processando com IA...", True
                page.update()
                    
                    # Processar cada imagem
                    severidades = []
                    plot_images = []
                    
                    for file_data in APP_STATE.get("uploaded_files_data", []):
                        # Converter bytes para base64 antes de enviar
                        import base64
                        file_b64 = base64.b64encode(file_data["bytes"]).decode('utf-8')
                        
                        # Chamar API de IA
                        response = requests.post(
                            f"{API_URL}/predict",
                            json={"file": file_b64},
                            headers={"Content-Type": "application/json"},
                            timeout=120
                        )
                        
                        if response.status_code == 200:
                            result = response.json()
                            severidades.append(result.get("severity", 0))
                            plot_images.append(result.get("plot_image_b64", ""))
                            recomendacao = result.get("recomendacao", {})
                        else:
                            print(f"Erro na API: {response.status_code} - {response.text}")
                            progress_text.value = f"Erro na API: {response.status_code}"
                            progress_ring.visible = False
                            page.update()
                            return
                    
                    # Calcular severidade média
                    severidade_media = sum(severidades) / len(severidades) if severidades else 0.0
                    
                    progress_text.value = f"Severidade média: {severidade_media:.2f}%"
                    progress_ring.visible = False
                    
                    # Exibir resultados
                    results_container.controls.clear()
                    
                    # Container de recomendações
                    if recomendacao:
                        recom_controls = [
                            ft.Row([
                                ft.Icon(ft.Icons.DESCRIPTION, size=20, color="#2E7D32"),
                                ft.Text(recomendacao.get("titulo", "Recomendações"), size=20, weight=ft.FontWeight.BOLD, color="#2E7D32")
                            ], alignment=ft.MainAxisAlignment.CENTER),
                            ft.Text(recomendacao.get("descricao", ""), size=16, text_align=ft.TextAlign.JUSTIFY, color="#424242"),
                        ]
                        
                        # Adicionar instruções
                        for instrucao in recomendacao.get("instrucoes", []):
                            recom_controls.append(ft.Text(instrucao, size=14, text_align=ft.TextAlign.JUSTIFY, color="#424242"))
                        
                        # Se for calda bordalesa (severidade < 5%), adicionar botões extras
                        if recomendacao.get("tipo") == "calda_bordalesa":
                            recom_controls.extend([
                                ft.Container(
                                    content=ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.PICTURE_AS_PDF,
                                            icon_color="#D32F2F",
                                            icon_size=28,
                                            tooltip="Baixar PDF da Calda Bordalesa",
                                            on_click=lambda _: print("PDF não disponível no Cloud Run")
                                        ),
                                        ft.Text("Baixar instruções em PDF", size=14, color="#424242")
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                                    padding=15
                                ),
                                ft.Container(
                                    content=ft.Row([
                                        ft.IconButton(
                                            icon=ft.Icons.PLAY_CIRCLE_FILL_ROUNDED,
                                            icon_color="#D32F2F",
                                            icon_size=28,
                                            tooltip="Assistir vídeo tutorial",
                                            on_click=lambda _: page.launch_url("https://www.youtube.com/watch?v=If2wHR-XOIc")
                                        ),
                                        ft.Text("Assistir vídeo tutorial", size=14, color="#424242")
                                    ], alignment=ft.MainAxisAlignment.CENTER, spacing=10),
                                    padding=15
                                )
                            ])
                        
                        if recomendacao.get("fonte"):
                            recom_controls.append(ft.Text(f"Fonte: {recomendacao.get('fonte')}", size=12, color="#666666", italic=True))
                        
                        recom_container = ft.Container(
                            content=ft.Column(controls=recom_controls, spacing=10),
                            padding=25,
                            bgcolor="#FFF8E1",
                            border_radius=20,
                            width=380,
                            shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))
                        )
                        results_container.controls.append(recom_container)
                    
                    # Container de imagens processadas
                    if plot_images:
                        images_controls = [
                            ft.Text("Plotagens da severidade", size=20, weight=ft.FontWeight.BOLD, color="#2E7D32")
                        ]
                        
                        for i, plot_b64 in enumerate(plot_images):
                            if plot_b64:
                                images_controls.append(
                                    ft.Column([
                                        ft.Image(
                                            src_base64=plot_b64,
                                            width=320,
                                            height=320,
                                            fit=ft.ImageFit.CONTAIN,
                                            border_radius=15
                                        ),
                                        ft.Text(f"Imagem {i+1} - Severidade: {severidades[i]:.2f}%", size=14, color="#424242")
                                    ], alignment=ft.MainAxisAlignment.CENTER)
                                )
                        
                        images_container = ft.Container(
                            content=ft.Column(controls=images_controls, spacing=15),
                            padding=25,
                            bgcolor="#F1F8E9",
                            border_radius=20,
                            width=380,
                            shadow=ft.BoxShadow(blur_radius=15, spread_radius=1, color=ft.Colors.with_opacity(0.2, ft.Colors.BLACK))
                        )
                        results_container.controls.append(images_container)
                    
                    page.update()
                    
                except Exception as ex:
                    print(f"Erro no processamento: {ex}")
                    progress_text.value = f"Erro: {str(ex)}"
                    progress_ring.visible = False
                page.update()

            threading.Thread(target=processing, daemon=True).start()

        btn_calcular_severidade = ft.ElevatedButton("Calcular Severidade com IA", disabled=True, on_click=calcular_severidade_callback,
            width=300, bgcolor="#1976D2", color=ft.Colors.WHITE, style=button_style,
            content=ft.Row([ft.Icon(ft.Icons.AUTO_FIX_HIGH_OUTLINED, size=20, color="white"), ft.Text("Calcular Severidade com IA", size=18)], alignment=ft.MainAxisAlignment.CENTER, spacing=10))

        page.add(ft.Column([
            header_avalia, container_amostragem, resultado_container, container_upload,
            ft.Container(content=btn_calcular_severidade, width=300, alignment=ft.alignment.center),
            progress_ring, progress_text, results_container,
            ft.ElevatedButton("Voltar", on_click=lambda e: mostrar_nova_tela(APP_STATE.get("cidade_selecionada"), APP_STATE.get("cultura_selecionada")), bgcolor="#4CAF50", color=ft.Colors.WHITE, style=button_style)
        ], alignment=ft.MainAxisAlignment.CENTER, horizontal_alignment=ft.CrossAxisAlignment.CENTER, scroll=ft.ScrollMode.AUTO, expand=True, spacing=25))
        
        # Iniciar polling (igual ao código original)
        poll_uploads()

    def mostrar_nova_tela(cidade, cultura):
        page.clean()
        
        # --- Lógica de busca de dados (copiada do original) ---
        lat, lon = CITY_COORDINATES[cidade]["lat"], CITY_COORDINATES[cidade]["lon"]
        APP_STATE["lat"], APP_STATE["lon"] = lat, lon
        APP_STATE["local_sunrise"], APP_STATE["local_sunset"] = get_sun_times(lat, lon)
        APP_STATE["weather_data"] = get_weather_data(lat, lon)
        APP_STATE["clima_previsao"] = get_weather_data_prev(lat, lon)
        historico = get_weather_history(lat, lon)
        
        # --- Processamento dos dados para UI ---
        weather_data = APP_STATE.get("weather_data", {})
        values = weather_data.get("data", {}).get("values", {})
        temperature = float(values.get("temperature", "N/A")) if "temperature" in values else "N/A"
        humidity = float(values.get("humidity", "N/A")) if "humidity" in values else "N/A"
        precip_prob = float(values.get("precipitationProbability", "N/A")) if "precipitationProbability" in values else "N/A"
        weather_code = int(values.get("weatherCode", 0))
        wind_kmh = float(values.get("windSpeed", "N/A")) * 3.6 if values.get("windSpeed") is not None else "N/A"
        
        sunrise, sunset = APP_STATE.get("local_sunrise"), APP_STATE.get("local_sunset")
        agora = datetime.now().astimezone()
        periodo = "d" if sunrise and sunset and sunrise <= agora <= sunset else "n"
        icon_filename = f"{weather_code}_{periodo}.png"
        
        # --- Construção da UI (copiada do original) ---
        header = ft.Row([ft.Icon(ft.Icons.ECO_ROUNDED, size=40), ft.Text("CultivaTrack", size=32, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
        
        subbox_clima = ft.Container(
            content=ft.Column([
                ft.Text("Clima Atual", size=22, weight=ft.FontWeight.BOLD, color="#2E7D32"),
                ft.Row([ft.Icon(ft.Icons.PIN_DROP_ROUNDED), ft.Text(cidade, size=16)]),
                ft.Row([ft.Icon(ft.Icons.LOCAL_FLORIST_ROUNDED), ft.Text(cultura, size=16)]),
                create_image_with_fallback(f"icones_weathercode_openmeteo/{icon_filename}", width=100, height=100),
                ft.Text(WEATHER_CODES.get(weather_code, "Desconhecido"), size=16, text_align=ft.TextAlign.CENTER),
                ft.Text(f"Temperatura: {temperature}°C\nUmidade: {humidity}%\nChuva: {precip_prob}%\nVento: {wind_kmh:.1f} km/h", size=16, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
            padding=25, bgcolor=ft.Colors.WHITE, border_radius=20, width=380
        )
        
        # Evapotranspiração UI
        data_anterior = (datetime.now().astimezone() - timedelta(days=1)).strftime("%d/%m/%Y")
        evap_total = historico['timelines']['daily'][0]['values']['evapotranspirationSum'] if historico and historico.get("timelines", {}).get("daily") else 'N/A'
        evap_text = f"Evapotranspiração total em {data_anterior}:\n{evap_total:.3f} mm/dia" if isinstance(evap_total, float) else "Dados indisponíveis"
        subbox_evapotranspiracao = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.WATER_DROP, size=32, color="#1976D2"),
                ft.Text("Evapotranspiração de Referência", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color="#2E7D32"),
                ft.Text(evap_text, size=16, text_align=ft.TextAlign.CENTER)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=25, bgcolor="#F1F8E9", border_radius=20, width=380
        )

        # Alerta de Risco UI
        if APP_STATE.get("clima_previsao"):
            hourly_sel = select_next_hours(APP_STATE["clima_previsao"]["timelines"]["hourly"], 48)
            classificacao_list = [("Risco Baixo" if (t < 20 or u < 80) else "Risco Moderado" if (20 <= t < 25 and 80 <= u < 90) else "Risco Elevado" if ((20 <= t < 25 and u >= 90) or (t >= 25 and 80 <= u < 90)) else "Risco Alto" if (t >= 25 and u >= 90) else "Risco Baixo") for e in hourly_sel for t, u in [(e["values"]["temperature"], e["values"]["humidity"])] if t is not None and u is not None]
            APP_STATE["classificacao_list"] = classificacao_list
            risco_counts = {r: classificacao_list.count(r) for r in ["Risco Baixo", "Risco Moderado", "Risco Elevado", "Risco Alto"]}
            total_horas = len(classificacao_list) or 1
            alert_text = "\n".join(f"{k}: {v / total_horas * 100:.1f}%" for k, v in risco_counts.items())
            subbox_alerta = ft.Container(
                content=ft.Column([
                    ft.Text("Status de alerta para Cercosporiose (48h)", size=20, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color="#2E7D32"),
                    ft.Text(alert_text, size=16, text_align=ft.TextAlign.CENTER),
                    ft.ElevatedButton("Gráfico", icon=ft.Icons.SHOW_CHART, on_click=abrir_tela_grafico, style=button_style, bgcolor="#1976D2")
                ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=15),
                padding=25, bgcolor="#F1F8E9", border_radius=20, width=380
            )
        else:
            subbox_alerta = ft.Container(ft.Text("Dados de previsão indisponíveis."), padding=20)
        
        # Botões de Ação
        botao_avaliar = ft.Container(content=ft.ElevatedButton("Avaliar Severidade", on_click=mostrar_tela_avaliar_severidade, disabled=True, style=button_style, bgcolor="#1976D2"), opacity=0.5)
        botao_recomendacao = ft.Container(content=ft.ElevatedButton("Gerar Recomendação", on_click=abrir_tela_recomendacao, disabled=False, style=button_style, bgcolor="#FF9800"))
        
        def toggle_botoes(e):
            botao_avaliar.content.disabled = not e.control.value
            botao_avaliar.opacity = 1.0 if e.control.value else 0.5
            botao_recomendacao.content.disabled = e.control.value
            botao_recomendacao.opacity = 0.5 if e.control.value else 1.0
            page.update()
            
        botao_deslizante = ft.Container(
            content=ft.Column([
                ft.Text("Existem sinais de cercosporiose no cultivo?", size=18, weight=ft.FontWeight.BOLD, text_align=ft.TextAlign.CENTER, color="#2E7D32"),
                ft.Row([ft.Text("Não"), ft.Switch(value=False, on_change=toggle_botoes), ft.Text("Sim")], alignment=ft.MainAxisAlignment.CENTER)
            ], spacing=15),
            padding=25, bgcolor=ft.Colors.WHITE, border_radius=20, width=380
        )
        
        # NOVO: Botão "Sobre a Cercosporiose" adicionado
        botao_sobre = ft.ElevatedButton(
            "Sobre a Cercosporiose",
            on_click=abrir_tela_sobre,
            width=280,
            bgcolor="#4CAF50",
            color=ft.Colors.WHITE,
            style=button_style,
            content=ft.Row(
                controls=[ft.Icon(ft.Icons.INFO_OUTLINED, size=20, color="white"),
                          ft.Text("Sobre a Cercosporiose", size=18)],
                alignment=ft.MainAxisAlignment.CENTER,
                spacing=10
            )
        )

        # Montagem final da tela
        page.add(ft.Column([
            header, subbox_clima, subbox_evapotranspiracao, subbox_alerta,
            botao_sobre, # Botão adicionado aqui
            botao_deslizante, botao_avaliar, botao_recomendacao,
            ft.ElevatedButton("Voltar para Início", on_click=lambda e: mostrar_tela_inicial(), style=button_style)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, scroll=ft.ScrollMode.AUTO, expand=True))
        page.update()
    
    # --- Telas Adicionais ---
    def abrir_tela_grafico(e):
        page.clean()
        graph_image = ft.Image(src_base64=generate_risk_graph(APP_STATE.get("classificacao_list", [])), width=380, fit=ft.ImageFit.CONTAIN) if APP_STATE.get("classificacao_list") else ft.Text("Dados de risco não disponíveis.")
        page.add(ft.Column([
            ft.Container(content=graph_image, padding=20, bgcolor=ft.Colors.WHITE, border_radius=20),
            ft.ElevatedButton("Voltar", on_click=lambda _: mostrar_nova_tela(APP_STATE.get("cidade_selecionada"), APP_STATE.get("cultura_selecionada")), style=button_style)
        ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=25, expand=True))
        page.update()
        
    # NOVO: Tela "Sobre a Cercosporiose" completa
    def abrir_tela_sobre(e):
        page.clean()
        page.add(
            ft.Column(
                controls=[
                    create_image_with_fallback(
                        "chilli-cercospora-leaf-spot-pepper-1560239911.jpg",
                        width=320,
                        height=200,
                        fit=ft.ImageFit.CONTAIN,
                        border_radius=15
                    ),
                    ft.Container(
                        content=ft.Column(
                            controls=[
                                ft.Text("Sintomas", size=22, weight=ft.FontWeight.BOLD, color="#2E7D32"),
                                ft.Text(
                                    "Manchas circulares ou irregulares nas folhas.\nLesões com bordas escuras e centros claros.\nAmarelecimento e queda prematura das folhas.\nRedução da fotossíntese e da produtividade.\n\nÉ uma doença favorecida por temperatura acima de 25 °C e umidade do ar acima de 90%. Plantas com estresse nutricional são mais sensíveis.",
                                    size=16,
                                    text_align=ft.TextAlign.JUSTIFY,
                                    color="#424242"
                                ),
                                ft.Text("Controle", size=22, weight=ft.FontWeight.BOLD, color="#2E7D32"),
                                ft.Text(
                                    "- Plantar sementes de boa qualidade;\n- Evitar plantio próximo a culturas velhas;\n- Pulverizar preventivamente com fungicidas;\n- Adubar corretamente;\n- Manejo adequado da irrigação;\n- Evitar épocas de chuva intensa;\n- Eliminar restos de cultura;\n- Rotação de culturas por pelo menos um ano;",
                                    size=16,
                                    text_align=ft.TextAlign.JUSTIFY,
                                    color="#424242"
                                ),
                                ft.Text(
                                    "Fonte:",
                                    size=16,
                                    weight=ft.FontWeight.BOLD,
                                    color="#2E7D32"
                                ),
                                ft.Text(
                                    "HENZ, Gilmar Paulo; LOPES, Carlos Alberto; REIS, Ailton. Mancha-de-cercóspora. Embrapa - Secretaria de Inteligência e Relações Estratégicas; Embrapa Hortaliças, 2022. Disponível em: https://www.embrapa.br/agencia-de-informacao-tecnologica/cultivos/pimenta/producao/doencas-e-pragas/doencas/fungicas/mancha-de-cercospora.",
                                    size=14,
                                    text_align=ft.TextAlign.JUSTIFY,
                                    color="#424242"
                                )
                            ],
                            alignment=ft.MainAxisAlignment.START,
                            horizontal_alignment=ft.CrossAxisAlignment.START,
                            spacing=20
                        ),
                        padding=25,
                        bgcolor="#F1F8E9",
                        border_radius=20,
                        width=380,
                    ),
                    ft.ElevatedButton(
                        "Voltar",
                        on_click=lambda e: mostrar_nova_tela(APP_STATE.get("cidade_selecionada"), APP_STATE.get("cultura_selecionada")),
                        style=button_style
                    )
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                spacing=25,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
        page.update()

    # NOVO: Tela de "Gerar Recomendação" completa
    def abrir_tela_recomendacao(e):
        page.clean()
        graph_image = ft.Image(
            src_base64=generate_risk_graph(APP_STATE.get("classificacao_list", [])),
            width=600,
            height=350,
            fit=ft.ImageFit.CONTAIN,
            border_radius=15
        ) if APP_STATE.get("classificacao_list") else ft.Text("Dados de risco não disponíveis.", size=20)

        weather_data = APP_STATE.get("weather_data", {})
        values = weather_data.get("data", {}).get("values", {})
        temperature = float(values.get("temperature", "N/A")) if "temperature" in values else "N/A"
        humidity = float(values.get("humidity", "N/A")) if "humidity" in values else "N/A"
        precipitation_probability = float(values.get("precipitationProbability", "N/A")) if "precipitationProbability" in values else "N/A"
        wind_speed_kmh = float(values.get("windSpeed", "N/A")) * 3.6 if "windSpeed" in values else "N/A"

        condicoes_ideais = True
        condicoes_mensagem = []
        if temperature != "N/A" and not (18 <= temperature <= 30): condicoes_ideais = False; condicoes_mensagem.append(f"Temperatura: {temperature}°C (Ideal: 18-30°C)")
        if humidity != "N/A" and not (50 <= humidity <= 90): condicoes_ideais = False; condicoes_mensagem.append(f"Umidade: {humidity}% (Ideal: 50-90%)")
        if wind_speed_kmh != "N/A" and not (3 <= wind_speed_kmh <= 10): condicoes_ideais = False; condicoes_mensagem.append(f"Vento: {wind_speed_kmh:.1f} km/h (Ideal: 3-10 km/h)")
        if precipitation_probability != "N/A" and precipitation_probability > 50: condicoes_ideais = False; condicoes_mensagem.append(f"Chuva: {precipitation_probability}% (Ideal: < 50%)")

        pulverizacao_mensagem = "Condições ideais para pulverização." if condicoes_ideais else ("Não são condições ideais para pulverização.\n\n" + "\n".join(condicoes_mensagem))
        
        subbox_pulverizacao = ft.Container(
            content=ft.Column([
                ft.Icon(ft.Icons.AIR, size=32, color="#1976D2"),
                ft.Text("Condições de Pulverização", size=20, weight=ft.FontWeight.BOLD, color="#2E7D32", text_align=ft.TextAlign.CENTER),
                ft.Icon(ft.Icons.CHECK_CIRCLE if condicoes_ideais else ft.Icons.WARNING, size=28, color="#4CAF50" if condicoes_ideais else "#D32F2F"),
                ft.Text(pulverizacao_mensagem, size=16, text_align=ft.TextAlign.CENTER, color="#424242")
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=10),
            padding=25, bgcolor="#F1F8E9", border_radius=20, width=380
        )

        page.add(
            ft.Column(
                controls=[
                    ft.Container(content=graph_image, padding=20, bgcolor=ft.Colors.WHITE, border_radius=20, alignment=ft.alignment.center, width=380),
                    ft.Container(
                        padding=20, bgcolor=ft.Colors.WHITE, border_radius=20, width=380,
                        content=ft.Column(
                            controls=[
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Recomendações para Risco Baixo/Moderado", size=20, weight=ft.FontWeight.BOLD, color="#2E7D32", text_align=ft.TextAlign.CENTER),
                                        ft.Text("Se não existirem sinais da doença e o risco for baixo ou moderado, recomenda-se observação contínua, irrigação adequada e monitoramento regular.", size=16, text_align=ft.TextAlign.JUSTIFY)
                                    ], spacing=15),
                                    padding=25, bgcolor="#FFF8E1", border_radius=20, width=380
                                ),
                                ft.Container(
                                    content=ft.Column([
                                        ft.Text("Recomendações para Risco Elevado/Alto", size=20, weight=ft.FontWeight.BOLD, color="#2E7D32", text_align=ft.TextAlign.CENTER),
                                        ft.Text("Se não existirem sinais da doença e o risco for elevado ou alto, recomenda-se tratamento preventivo com calda bordalesa.", size=16, text_align=ft.TextAlign.JUSTIFY),
                                        criar_botao_pdf_simple(),  # Botão PDF na tela de recomendações
                                        ft.Row([ft.IconButton(icon=ft.Icons.PLAY_CIRCLE_FILL_ROUNDED, on_click=lambda _: page.launch_url("https://www.youtube.com/watch?v=If2wHR-XOIc")), ft.Text("Assistir vídeo tutorial")], alignment=ft.MainAxisAlignment.CENTER),
                                        ft.Text("Passo a passo para a elaboração da calda bordalesa:\n1. Diluição do sulfato de cobre: 200 g em 5L de água por 4-24h.\n2. Preparo do leite de cal: 200 g de cal virgem em 2L de água.\n3. Mistura: Adicione sulfato ao leite de cal lentamente.\n4. Verificação: Teste com ferro; ajuste acidez com cal se necessário.\n5. Aplique após filtrar.", size=14, text_align=ft.TextAlign.JUSTIFY),
                                        subbox_pulverizacao
                                    ], spacing=15),
                                    padding=25, bgcolor="#FFF8E1", border_radius=20, width=380
                                )
                            ],
                            alignment=ft.MainAxisAlignment.CENTER,
                            spacing=20
                        )
                    ),
                    ft.ElevatedButton("Voltar", on_click=lambda _: mostrar_nova_tela(APP_STATE.get("cidade_selecionada"), APP_STATE.get("cultura_selecionada")), style=button_style)
                ],
                alignment=ft.MainAxisAlignment.CENTER,
                horizontal_alignment=ft.CrossAxisAlignment.CENTER,
                scroll=ft.ScrollMode.AUTO,
                expand=True
            )
        )
        page.update()

    # --- Tela Inicial ---
    header_inicial = ft.Row([ft.Icon(ft.Icons.ECO_ROUNDED, size=40), ft.Text("CultivaTrack", size=32, weight=ft.FontWeight.BOLD)], alignment=ft.MainAxisAlignment.CENTER)
    dropdown_cultura = create_dropdown("Selecione a Cultura", ["Pimenta"], dropdown_style)
    dropdown_doenca = create_dropdown("Selecione a Doença", ["Cercosporiose"], dropdown_style)
    dropdown_cidade = create_dropdown("Selecione a Cidade", list(CITY_COORDINATES.keys()), dropdown_style)
    button_ok = ft.ElevatedButton("Começar", style=button_style, on_click=lambda _: on_ok_click(), disabled=True)
    alerta_texto = ft.Container(content=ft.Row([ft.Icon(ft.Icons.INFO_ROUNDED), ft.Text("As recomendações pressupõem cultivo em boas condições nutricionais.", width=280)], alignment=ft.MainAxisAlignment.CENTER), padding=20, bgcolor="#FFF8E1")

    def check_button_enable(e):
        button_ok.disabled = not all([dropdown_cultura.value, dropdown_doenca.value, dropdown_cidade.value])
        page.update()
    
    dropdown_cultura.on_change = dropdown_doenca.on_change = dropdown_cidade.on_change = check_button_enable
    
    def on_ok_click():
        cidade, cultura = dropdown_cidade.value, dropdown_cultura.value
        if not all([cidade, cultura]): return
        
        page.clean()
        page.add(ft.Column([ft.ProgressRing(), ft.Text("Carregando dados...")], horizontal_alignment=ft.CrossAxisAlignment.CENTER, alignment=ft.MainAxisAlignment.CENTER, expand=True))
        page.update()
        
        APP_STATE["cidade_selecionada"] = cidade
        APP_STATE["cultura_selecionada"] = cultura
        
        # Usar um thread para não bloquear a UI enquanto os dados são carregados
        threading.Thread(target=lambda: mostrar_nova_tela(cidade, cultura), daemon=True).start()

    def mostrar_tela_inicial(e=None):
        page.clean()
        page.add(
            ft.Column([
                header_inicial, dropdown_cultura, dropdown_doenca, dropdown_cidade,
                ft.Column([button_ok, alerta_texto], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20)
            ], horizontal_alignment=ft.CrossAxisAlignment.CENTER, spacing=20, scroll=ft.ScrollMode.AUTO, expand=True)
        )
        page.update()
        
    mostrar_tela_inicial()

# --- Expõe a aplicação para o Gunicorn/FastAPI ---
# O 'assets_dir' deve apontar para a pasta com suas imagens (ícones, ilustrações, PDFs).
# CORRIGIDO: de "Assets" para "assets" (minúsculo)

# === CONFIGURAÇÃO FASTAPI COM ROTAS ESPECÍFICAS ===
from fastapi import FastAPI, HTTPException, UploadFile, File
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse, HTMLResponse
import os
import mimetypes
from typing import List

# IMPORTANTE: Criar a instância FastAPI PRIMEIRO, depois adicionar o Flet
app = FastAPI(title="CultivaTrack", description="Sistema de Monitoramento Agrícola")

# === ROTAS API ESPECÍFICAS (ANTES DO FLET) ===
if os.path.exists("assets"):
    # Rota ESPECÍFICA para o PDF (com prefixo API para evitar conflitos)
    @app.get("/api/pdf/calda-bordalesa")
    async def download_calda_bordalesa_api():
        """Serve o PDF da calda bordalesa via rota API dedicada"""
        pdf_path = os.path.join("assets", "calda-bordalesa.pdf")
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF não encontrado")
        
        return FileResponse(
            pdf_path, 
            media_type="application/pdf",
            headers={
                "Content-Disposition": "inline; filename=calda-bordalesa.pdf",
                "Cache-Control": "public, max-age=3600",
                "X-Content-Type-Options": "nosniff"
            }
        )
    
    # Rota alternativa para DOWNLOAD forçado
    @app.get("/api/download/calda-bordalesa.pdf")
    async def force_download_calda_bordalesa_api():
        """Força o download do PDF ao invés de abrir no navegador"""
        pdf_path = os.path.join("assets", "calda-bordalesa.pdf")
        
        if not os.path.exists(pdf_path):
            raise HTTPException(status_code=404, detail="PDF não encontrado")
        
        return FileResponse(
            pdf_path, 
            media_type="application/pdf",
            filename="calda-bordalesa.pdf",
            headers={
                "Content-Disposition": "attachment; filename=calda-bordalesa.pdf"
            }
        )
    
    # Rota para servir assets estáticos
    @app.get("/api/assets/{file_path:path}")
    async def serve_assets_api(file_path: str):
        """Serve arquivos de assets via API"""
        full_path = os.path.join("assets", file_path)
        
        if not os.path.exists(full_path):
            raise HTTPException(status_code=404, detail="Arquivo não encontrado")
        
        # Detecta o tipo MIME
        mime_type, _ = mimetypes.guess_type(full_path)
        if mime_type is None:
            mime_type = "application/octet-stream"
        
        return FileResponse(full_path, media_type=mime_type)

# === ROTAS DE UPLOAD DE IMAGENS (baseado no main-referencia.py) ===
@app.get("/upload.html", response_class=HTMLResponse)
async def get_upload_page():
    """Serve a página HTML de upload"""
    try:
        upload_html = """<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Upload - CultivaTrack</title>
    <style>
        body { margin: 0; padding: 0; background: rgba(0, 0, 0, 0.5); display: flex; align-items: center; justify-content: center; height: 100vh; font-family: Arial, sans-serif; }
        .modal { position: relative; background: #fff; width: 320px; padding: 20px; border-radius: 10px; box-shadow: 0 4px 8px rgba(0, 0, 0, 0.2); text-align: center; }
        .close-btn { position: absolute; top: 8px; right: 8px; background: transparent; border: none; font-size: 22px; cursor: pointer; color: #888; }
        .close-btn:hover { color: #555; }
        h2 { margin-top: 0; color: #388E3C; }
        button { background: #388E3C; border: none; color: #fff; padding: 8px 16px; font-size: 14px; border-radius: 5px; cursor: pointer; margin: 5px; }
        button:hover { background: #2E7D32; }
        .camera-buttons { display: flex; justify-content: center; gap: 10px; margin: 15px 0; }
        .camera-btn { background: #1976D2; border: none; color: #fff; padding: 10px 15px; font-size: 14px; border-radius: 8px; cursor: pointer; display: flex; align-items: center; gap: 5px; }
        .camera-btn:hover { background: #1565C0; }
        .gallery-btn { background: #FF9800; }
        .gallery-btn:hover { background: #F57C00; }
        #status { margin-top: 15px; color: #388E3C; font-size: 14px; white-space: pre-wrap; }
        #okButton { display: none; margin-top: 15px; }
        #fileInputCamera, #fileInputGallery { display: none; }
        .icon { font-size: 16px; }
    </style>
</head>
<body>
    <div class="modal">
        <button class="close-btn" onclick="closeModal()">×</button>
        <h2>Capturar Imagens</h2>
        
        <!-- Input para câmera (capture="environment" para câmera traseira) -->
        <input type="file" id="fileInputCamera" multiple accept="image/*" capture="environment">
        
        <!-- Input para galeria -->
        <input type="file" id="fileInputGallery" multiple accept="image/*">
        
        <div class="camera-buttons">
            <button class="camera-btn" onclick="document.getElementById('fileInputCamera').click()">
                <span class="icon">📷</span> Câmera
            </button>
            <button class="camera-btn gallery-btn" onclick="document.getElementById('fileInputGallery').click()">
                <span class="icon">🖼️</span> Galeria
            </button>
        </div>
        
        <button id="uploadButton">Enviar Imagens</button>
        <button id="okButton" onclick="okClick()">OK</button>
        <div id="status">Escolha câmera ou galeria para adicionar imagens.</div>
    </div>

    <script>
        function closeModal() { window.close(); }
        function okClick() {
            if (window.opener && typeof window.opener.postMessage === 'function') {
                window.opener.postMessage({ uploadStatus: "Upload de " + uploadedCount + " imagens com sucesso!" }, "*");
            }
            closeModal();
        }

        const fileInputCamera = document.getElementById("fileInputCamera");
        const fileInputGallery = document.getElementById("fileInputGallery");
        const uploadButton = document.getElementById("uploadButton");
        const okButton = document.getElementById("okButton");
        const statusDiv = document.getElementById("status");
        let uploadedCount = 0;
        let selectedFiles = [];

        // Função para processar arquivos selecionados
        function handleFileSelection(files, source) {
            if (files.length) {
                for (let file of files) {
                    selectedFiles.push(file);
                }
                const sourceText = source === 'camera' ? 'câmera' : 'galeria';
                statusDiv.innerText = `${selectedFiles.length} imagem(ns) selecionada(s) (última via ${sourceText})`;
            }
        }

        // Event listeners para ambos os inputs
        fileInputCamera.addEventListener("change", (e) => {
            handleFileSelection(e.target.files, 'camera');
            e.target.value = ""; // Limpar input para permitir nova seleção
        });

        fileInputGallery.addEventListener("change", (e) => {
            handleFileSelection(e.target.files, 'gallery');
            e.target.value = ""; // Limpar input para permitir nova seleção
        });

        async function uploadFile(file) {
            try {
                const formData = new FormData();
                formData.append('files', file);
                
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                return await response.json();
            } catch (err) {
                console.error("Erro no upload do arquivo", err);
                return { status: "erro", mensagem: err.toString() };
            }
        }

        uploadButton.addEventListener("click", async () => {
            if (selectedFiles.length === 0) {
                statusDiv.innerText = "Nenhuma imagem selecionada. Use câmera ou galeria primeiro.";
                return;
            }
            
            statusDiv.innerText = `Enviando ${selectedFiles.length} imagem(ns)...`;
            uploadedCount = 0;

            for (let i = 0; i < selectedFiles.length; i++) {
                const file = selectedFiles[i];
                statusDiv.innerText = `Enviando imagem ${i + 1}/${selectedFiles.length}...`;
                
                const result = await uploadFile(file);
                if (result.status !== "erro") {
                    uploadedCount++;
                }
            }

            statusDiv.innerText = `✅ Upload de ${uploadedCount} imagem(ns) concluído com sucesso!`;
            okButton.style.display = "inline-block";
            
            // Limpar lista para próximo uso
            selectedFiles = [];
        });

        // Detectar se é dispositivo móvel e mostrar dica
        const isMobile = /Android|webOS|iPhone|iPad|iPod|BlackBerry|IEMobile|Opera Mini/i.test(navigator.userAgent);
        if (isMobile) {
            statusDiv.innerHTML = "📱 <strong>Dica:</strong> Use 'Câmera' para fotos diretas ou 'Galeria' para imagens salvas.";
        }
    </script>
</body>
</html>"""
        return HTMLResponse(content=upload_html)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Erro ao servir página de upload: {str(e)}")

@app.post("/upload")
async def upload_files(files: List[UploadFile] = File(...)):
    """Recebe e processa uploads de imagens (baseado no main-referencia.py)"""
    print(f"=== UPLOAD RECEBIDO ===")
    print(f"Número de arquivos: {len(files)}")
    
    uploaded_files = []
    
    for file in files:
        if file.content_type and file.content_type.startswith('image/'):
            try:
                # Ler conteúdo do arquivo
                content = await file.read()
                file_data = {
                    "name": file.filename,
                    "bytes": content,
                    "size": len(content),
                    "content_type": file.content_type
                }
                uploaded_files.append(file_data)
                print(f"✅ Arquivo processado: {file.filename} ({len(content)} bytes)")
                
            except Exception as e:
                print(f"❌ Erro ao processar {file.filename}: {e}")
                raise HTTPException(status_code=500, detail=f"Erro ao processar {file.filename}")
        else:
            print(f"❌ Arquivo rejeitado (não é imagem): {file.filename}")
            raise HTTPException(status_code=400, detail=f"Arquivo {file.filename} não é uma imagem válida")
    
    # Armazenar no estado global (baseado no main-referencia.py)
    if "uploaded_files_data" not in APP_STATE:
        APP_STATE["uploaded_files_data"] = []
    
    APP_STATE["uploaded_files_data"].extend(uploaded_files)
    
    print(f"Total de arquivos no estado: {len(APP_STATE['uploaded_files_data'])}")
    
    return {
        "status": "success", 
        "message": f"{len(uploaded_files)} arquivo(s) enviado(s) com sucesso",
        "files": [{"name": f["name"], "size": f["size"]} for f in uploaded_files]
    }

# === MONTA ARQUIVOS ESTÁTICOS ===
if os.path.exists("assets"):
    app.mount("/static", StaticFiles(directory="assets"), name="static")

# === AGORA ADICIONA O FLET À APLICAÇÃO FASTAPI ===
flet_app = flet_fastapi.app(main, assets_dir="assets")

# Monta o Flet como sub-aplicação (isso resolve conflitos de rota)
app.mount("/", flet_app)

# === EXECUÇÃO STANDALONE PARA DESENVOLVIMENTO ===
if __name__ == "__main__":
    print("=== EXECUTANDO EM MODO DESENVOLVIMENTO ===")
    print("Para testar localmente sem FastAPI...")
    ft.app(target=main, assets_dir="assets", port=8080)
    print("=== APLICAÇÃO ENCERRADA ===")
