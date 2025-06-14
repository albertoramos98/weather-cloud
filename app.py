# app.py
import os # <--- ADICIONADO
import json
import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone, timedelta
import re

# --- Configuração Inicial ---
app = Flask(__name__)
# !!! API KEY AGORA VEM DAS VARIÁVEIS DE AMBIENTE !!!
API_KEY = os.environ.get("OPENWEATHER_API_KEY") # <--- MODIFICADO

# --- Funções Auxiliares (do seu app de clima e marés) ---
def converter_timestamp(timestamp, offset_segundos):
    """Converte timestamp UNIX para H:M, ajustado pelo fuso horário."""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) + timedelta(seconds=offset_segundos)
    return dt.strftime('%H:%M')

def carregar_dados_mare(caminho_json='banco_mareas.json'):
    """Carrega os dados das marés a partir de um arquivo JSON."""
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def processar_pergunta_mare(dados_mare, porto_usuario, data_usuario, pergunta):
    """Processa a pergunta do usuário sobre marés e retorna a resposta."""
    porto_encontrado = None
    for item in dados_mare:
        if porto_usuario.strip().lower() in item.get('local', '').lower():
            if item.get('data') == data_usuario:
                porto_encontrado = item
                break
    
    if not porto_encontrado:
        return f"Não foram encontrados dados para o porto '{porto_usuario}' na data '{data_usuario}'."

    mares_data = porto_encontrado.get("mares", [])
    if not mares_data:
        return "Dados de maré para esta data estão indisponíveis ou incompletos."

    altas = [(m['hora'], m['altura_m']) for m in mares_data if m['tipo'] == 'alta']
    baixas = [(m['hora'], m['altura_m']) for m in mares_data if m['tipo'] == 'baixa']
    pergunta = pergunta.lower()
    
    if "horário" in pergunta and "maré alta" in pergunta:
        return f"Horários de maré alta em {data_usuario}:\n" + "\n".join([f"- {h} com {a}m" for h, a in altas])
    if "horário" in pergunta and "maré baixa" in pergunta:
        return f"Horários de maré baixa em {data_usuario}:\n" + "\n".join([f"- {h} com {a}m" for h, a in baixas])
    if "maré mais alta" in pergunta:
        mais_alta = max(altas, key=lambda item: item[1])
        return f"A maré mais alta em {data_usuario} será às {mais_alta[0]} com {mais_alta[1]}m."
    if "maré mais baixa" in pergunta:
        mais_baixa = min(baixas, key=lambda item: item[1])
        return f"A maré mais baixa em {data_usuario} será às {mais_baixa[0]} com {mais_baixa[1]}m."
    
    return "Não entendi sua pergunta. Tente: 'horário da maré alta/baixa' ou 'maré mais alta/baixa'."

# --- Rota Principal para o Frontend ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Rota da API de Clima ---
@app.route("/clima")
def obter_clima():
    if not API_KEY:
        return jsonify({"erro": "Chave da API de clima não configurada no servidor"}), 500
        
    cidade = request.args.get("cidade")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    
    if lat and lon:
        link = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&lang=pt_br&units=metric"
    elif cidade:
        link = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={API_KEY}&lang=pt_br&units=metric"
    else:
        return jsonify({"erro": "Informe o nome da cidade ou coordenadas"}), 400

    try:
        resposta = requests.get(link)
        resposta.raise_for_status()
        dados = resposta.json()
    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Erro na requisição: {str(e)}"}), 500
    
    if dados.get("cod") != 200:
        return jsonify({"erro": "Cidade não encontrada"}), 404
        
    timezone_offset = dados.get('timezone', 0)
    try:
        resultado = {
            "cidade": dados["name"], "pais": dados['sys']['country'],
            "descricao": dados['weather'][0]['description'], "icone": dados['weather'][0]['icon'],
            "temperatura": dados['main']['temp'], "sensacao": dados['main']['feels_like'],
            "temp_min": dados['main']['temp_min'], "temp_max": dados['main']['temp_max'],
            "pressao": dados['main']['pressure'], "umidade": dados['main']['humidity'],
            "nivel_mar": dados['main'].get('sea_level', 'N/A'), "visibilidade": dados.get('visibility', 'N/A'),
            "vento": dados['wind']['speed'], "nuvens": dados['clouds']['all'],
            "nascer_do_sol": converter_timestamp(dados['sys']['sunrise'], timezone_offset),
            "por_do_sol": converter_timestamp(dados['sys']['sunset'], timezone_offset),
            "latitude": dados['coord']['lat'], "longitude": dados['coord']['lon'],
        }
        return jsonify(resultado)
    except KeyError as e:
        return jsonify({"erro": f"Erro ao processar os dados do clima: {e}"}), 500

# --- Rota da API de Marés ---
@app.route('/mare', methods=['POST'])
def get_mare():
    dados_requisicao = request.json
    porto = dados_requisicao.get('porto')
    data_str_iso = dados_requisicao.get('data')
    pergunta = dados_requisicao.get('pergunta')

    if not all([porto, data_str_iso, pergunta]):
        return jsonify({"erro": "Campos 'porto', 'data' e 'pergunta' são obrigatórios."}), 400
    
    dados_mare = carregar_dados_mare()
    if dados_mare is None:
        return jsonify({"erro": "Falha ao carregar o banco de dados das marés no servidor."}), 500

    resposta = processar_pergunta_mare(dados_mare, porto, data_str_iso, pergunta)
    return jsonify({"resposta": resposta})

# O bloco abaixo não é usado pelo Render, mas é bom para testes locais.
if __name__ == "__main__":
    app.run(debug=False)
