# app.py
import os
import json
import requests
import re
from flask import Flask, request, jsonify, render_template, abort
from datetime import datetime, timezone, timedelta

# Bibliotecas de Segurança
from flask_talisman import Talisman
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address

# --- Configuração Inicial e de Segurança ---
app = Flask(__name__)

# Configura Content Security Policy (CSP) e outros cabeçalhos de segurança.
# A CSP ajuda a prevenir ataques de XSS, restringindo de onde os scripts/estilos podem ser carregados.
csp = {
    'default-src': '\'self\'',
    'script-src': [
        '\'self\'',
        'https://unpkg.com'  # Permite scripts do LeafletJS
    ],
    'style-src': [
        '\'self\'',
        'https://unpkg.com', # Permite estilos do LeafletJS
        'https://fonts.googleapis.com'
    ],
    'font-src': 'https://fonts.gstatic.com',
    'img-src': [
        '\'self\'',
        'data:',
        'https://*.tile.openstreetmap.org', # Permite imagens do mapa
        'https://openweathermap.org'      # Permite ícones do clima
    ]
}
Talisman(app, content_security_policy=csp)

# Configura o limitador de taxa (Rate Limiter)
limiter = Limiter(
    get_remote_address,
    app=app,
    default_limits=["200 per day", "50 per hour", "5 per minute"] # Limites padrão para todas as rotas
)

# --- Variáveis de Ambiente ---
OPENWEATHER_API_KEY = os.environ.get("OPENWEATHER_API_KEY")

# --- Funções Auxiliares ---
def converter_timestamp(timestamp, offset_segundos):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) + timedelta(seconds=offset_segundos)
    return dt.strftime('%H:%M')

def carregar_dados_mare(caminho_json='banco_mareas.json'):
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def processar_pergunta_mare_com_regras(dados_mare, porto_usuario, data_usuario, pergunta):
    porto_encontrado_dados = None
    for item in dados_mare:
        if porto_usuario.strip().lower() in item.get('local', '').lower() and item.get('data') == data_usuario:
            porto_encontrado_dados = item
            break
    if not porto_encontrado_dados:
        return f"Não foram encontrados dados para o porto '{porto_usuario}' na data '{data_usuario}'."
    mares_data = porto_encontrado_dados.get("mares", [])
    if not mares_data:
        return "Dados de maré para esta data estão indisponíveis ou incompletos."
    altas = sorted([(m['hora'], m['altura_m']) for m in mares_data if m['tipo'] == 'alta'], key=lambda x: x[1], reverse=True)
    baixas = sorted([(m['hora'], m['altura_m']) for m in mares_data if m['tipo'] == 'baixa'], key=lambda x: x[1])
    pergunta_lower = pergunta.lower()
    if "horário" in pergunta_lower and "alta" in pergunta_lower:
        if not altas: return "Não há dados de maré alta para esta data."
        return f"Horários de maré alta em {data_usuario}:\n" + "\n".join([f"- {h} com {a}m" for h, a in altas])
    if "horário" in pergunta_lower and "baixa" in pergunta_lower:
        if not baixas: return "Não há dados de maré baixa para esta data."
        return f"Horários de maré baixa em {data_usuario}:\n" + "\n".join([f"- {h} com {a}m" for h, a in baixas])
    if "mais alta" in pergunta_lower:
        if not altas: return "Não há dados de maré alta para esta data."
        return f"A maré mais alta em {data_usuario} será às {altas[0][0]} com {altas[0][1]}m."
    if "mais baixa" in pergunta_lower:
        if not baixas: return "Não há dados de maré baixa para esta data."
        return f"A maré mais baixa em {data_usuario} será às {baixas[0][0]} com {baixas[0][1]}m."
    return "Não entendi sua pergunta. Tente: 'horário da maré alta/baixa' ou 'maré mais alta/baixa'."

# --- Rotas da Aplicação ---
@app.route("/")
def index():
    return render_template("index.html")

@app.route("/clima")
@limiter.limit("10 per minute") # Limite mais específico para esta rota
def obter_clima():
    if not OPENWEATHER_API_KEY:
        abort(500, "Configuração do servidor incompleta: chave da API de clima ausente.")
    
    # Validação de entradas
    cidade = request.args.get("cidade", "")
    lat = request.args.get("lat", "")
    lon = request.args.get("lon", "")

    if len(cidade) > 100 or len(lat) > 20 or len(lon) > 20:
        abort(400, "Parâmetro de entrada demasiado longo.")

    if lat and lon:
        link = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={OPENWEATHER_API_KEY}&lang=pt_br&units=metric"
    elif cidade:
        link = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={OPENWEATHER_API_KEY}&lang=pt_br&units=metric"
    else:
        abort(400, "Informe cidade ou coordenadas.")

    try:
        resposta = requests.get(link, timeout=5) # Adiciona timeout
        resposta.raise_for_status()
        dados = resposta.json()
        if dados.get("cod") != 200:
            abort(404, "Cidade não encontrada.")
        
        timezone_offset = dados.get('timezone', 0)
        resultado = {
            "cidade": dados["name"], "pais": dados['sys']['country'], "descricao": dados['weather'][0]['description'],
            "icone": dados['weather'][0]['icon'], "temperatura": dados['main']['temp'], "sensacao": dados['main']['feels_like'],
            "temp_min": dados['main']['temp_min'], "temp_max": dados['main']['temp_max'], "pressao": dados['main']['pressure'],
            "umidade": dados['main']['humidity'], "nivel_mar": dados['main'].get('sea_level', 'N/A'),
            "visibilidade": dados.get('visibility', 'N/A'), "vento": dados['wind']['speed'], "nuvens": dados['clouds']['all'],
            "nascer_do_sol": converter_timestamp(dados['sys']['sunrise'], timezone_offset),
            "por_do_sol": converter_timestamp(dados['sys']['sunset'], timezone_offset),
            "latitude": dados['coord']['lat'], "longitude": dados['coord']['lon'],
        }
        return jsonify(resultado)
    except requests.exceptions.Timeout:
        abort(504, "O serviço de clima demorou muito para responder.")
    except requests.exceptions.RequestException:
        abort(502, "Erro ao comunicar com o serviço de clima.")
    except KeyError:
        abort(500, "Resposta inválida do serviço de clima.")

@app.route('/mare', methods=['POST'])
def get_mare():
    if not request.is_json:
        abort(415, "O tipo de conteúdo deve ser application/json")
    
    dados_requisicao = request.get_json()
    
    # Validação de entradas
    porto = dados_requisicao.get('porto', '')
    data_str_iso = dados_requisicao.get('data', '')
    pergunta = dados_requisicao.get('pergunta', '')

    if len(porto) > 100 or len(data_str_iso) > 10 or len(pergunta) > 200:
        abort(400, "Parâmetro de entrada demasiado longo.")

    if not all([porto, data_str_iso, pergunta]):
        abort(400, "Campos 'porto', 'data' e 'pergunta' são obrigatórios.")
    
    dados_mare = carregar_dados_mare()
    if dados_mare is None:
        abort(500, "Falha ao carregar o banco de dados das marés.")
    
    resposta = processar_pergunta_mare_com_regras(dados_mare, porto, data_str_iso, pergunta)
    return jsonify({"resposta": resposta})

# Manipulador de erros para retornar JSON
@app.errorhandler(400)
@app.errorhandler(404)
@app.errorhandler(415)
@app.errorhandler(429)
@app.errorhandler(500)
@app.errorhandler(502)
@app.errorhandler(504)
def json_error_handler(error):
    return jsonify(erro=error.description), error.code

if __name__ == "__main__":
    # Em produção, o Gunicorn será usado. O debug=False é fundamental.
    app.run(debug=False)

