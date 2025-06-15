import os
import json
import requests
from flask import Flask, request, jsonify, render_template
from datetime import datetime, timezone, timedelta
import math

app = Flask(__name__)

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "0153a042112f9529edbc2bad5372a198")

# --- Portos com localização geográfica (para cálculo de distância)
PORTOS_DISPONIVEIS = [
    ("Porto do Recife", "recife", -8.03, -34.52),
    ("Porto de São Luís", "sao_luis", -2.4, -44.17),
    ("Porto de Santos", "santos", -23.96, -46.33),
    ("Porto de Paranaguá", "paranagua", -25.31, -48.32),
    ("Porto de Salvador", "salvador", -12.97, -38.52),

    # Adicionando os demais portos (exemplos, pode ajustar slugs e valores)
    
    # Alagoas
    ("Porto de Maceió", "maceio", -9.68, -35.73),

    # Amapá
    ("Igarapé Grande do Curuá", "igarape_grande_curua", -0.76, -50.12),
    ("Barra Norte - Arco Lamoso", "barra_norte_arco_lamoso", -1.44, -49.21),
    ("Porto de Santana", "porto_santana", -0.06, -51.17),

    # Bahia
    ("Porto de Madre de Deus", "madre_de_deus", -12.75, -38.62),
    ("Porto de Ilhéus - Malhado", "ilheus_malhado", -14.78, -39.03),
    ("Porto de Salvador", "salvador_ba", -12.97, -38.52),
    ("Porto de Aratu", "aratu", -12.8, -38.5),

    # Ceará
    ("Terminal Portuário do Pecém", "pecem", -3.54, -38.8),
    ("Porto de Mucuripe", "mucuripe", -3.72, -38.48),

    # Espírito Santo
    ("Terminal da Ponta do Ubu", "ponta_ubu", -20.79, -40.57),
    ("Ilha da Trindade", "ilha_trindade", -20.51, -29.31),
    ("Porto de Vitória", "vitoria", -20.32, -40.34),
    ("Terminal de Barra do Riacho", "barra_riacho", -19.84, -40.06),
    ("Porto de Tubarão", "tubarao", -20.29, -40.24),

    # Maranhão
    ("Porto de Tutóia", "tutoia", -2.18, -42.14),
    ("Terminal da Alumar", "alumar", -2.5, -44.35),
    ("Terminal da Ponta da Madeira", "ponta_madeira", -2.57, -44.38),
    ("Porto de Itaqui", "itaqui", -2.58, -44.37),
    ("São Luís", "sao_luis_ma", -2.4, -44.17),

    # Pará
    ("Porto de Vila do Conde", "vila_conde", -1.54, -48.75),
    ("Ilha dos Guarás", "ilha_guaras", -0.08, -47.58),
    ("Fundeadouro de Salinópolis", "salinopolis", -0.62, -47.35),
    ("Ilha do Mosqueiro", "mosqueiro", -1.17, -48.47),
    ("Porto de Belém", "belem", -1.4, -48.49),
    ("Atracadouro de Breves", "breves", -1.69, -50.48),

    # Paraíba
    ("Porto de Cabedelo", "cabedelo", -6.97, -34.84),

    # Paraná
    ("Terminal da Ponta do Felix", "ponta_felix", -25.1, -48.41),
    ("Porto de Paranaguá", "paranagua_pr", -25.31, -48.32),
    ("Barra de Paranaguá - Canal Galheta", "canal_galheta", -25.57, -48.32),
    ("Barra de Paranaguá - Canal Sueste", "canal_sueste", -25.46, -48.16),

    # Pernambuco
    ("Porto do Recife", "recife_pe", -34.52, -8.03),
    ("Porto de Suape", "suape", -34.57, -8.23),
    ("Arquipélago de Fernando de Noronha", "fernando_noronha", -32.4, -3.83),
  

    # Piauí
    ("Porto de Luís Correia", "luis_correia", -2.85, -41.64),

    # Rio de Janeiro
    ("Porto do Rio de Janeiro - Ilha Fiscal", "ilha_fiscal", -22.9, -43.17),
    ("Porto de Itaguaí", "itaguai", -22.93, -43.84),
    ("Porto do Forno", "forno", -22.37, -42.01),
    ("Terminal da Ilha Guaíba", "ilha_guaiba", -22.1, -44.03),
    ("Porto de Angra dos Reis", "angra_reis", -23.01, -44.32),
    ("Terminal Marítimo de Imbetiba", "imbetiba", -22.42, -41.44),
    ("Porto do Açu", "acu", -21.81, -40.98),

    # Rio Grande do Norte
    ("Porto de Macau", "macau", -5.1, -36.67),
    ("Porto de Guamaré", "guamare", -5.11, -36.32),
    ("Porto de Natal - Capitania dos Portos do RN", "natal", -5.78, -35.21),
    ("Porto de Areia Branca - Termisa", "areia_branca", -4.45, -37.04),

    # Rio Grande do Sul
    ("Porto do Rio Grande", "rio_grande_rs", -32.14, -52.1),

    # Santa Catarina
    ("Porto de Imbituba", "imbituba", -28.23, -48.65),
    ("Porto de São Francisco do Sul", "sao_francisco_sul", -26.25, -48.64),
]

# --- Utilitários
def haversine(lon1, lat1, lon2, lat2):
    R = 6371
    lon1, lat1, lon2, lat2 = map(math.radians, [lon1, lat1, lon2, lat2])
    dlon = lon2 - lon1
    dlat = lat2 - lat1
    a = math.sin(dlat/2)**2 + math.cos(lat1)*math.cos(lat2)*math.sin(dlon/2)**2
    c = 2 * math.asin(math.sqrt(a))
    return R * c

def porto_mais_proximo(lat, lon):
    distancias = []
    for nome, identificador, plat, plon in PORTOS_DISPONIVEIS:
        dist = haversine(lon, lat, plon, plat)
        distancias.append((dist, identificador, nome))
    return min(distancias, key=lambda x: x[0])

def converter_timestamp(timestamp, offset_segundos):
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc) + timedelta(seconds=offset_segundos)
    return dt.strftime('%H:%M')

def carregar_dados_mare(caminho_json='banco_mareas.json'):
    try:
        with open(caminho_json, 'r', encoding='utf-8') as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return None

def obter_dados_mare_do_banco(porto_id_simplificado):
    termo_busca_json = porto_id_simplificado.replace("_", " ")
    dados_mare = carregar_dados_mare()
    if not dados_mare:
        return None

    data_hoje = datetime.now().strftime('%Y-%m-%d')
    for item in dados_mare:
        if termo_busca_json in item.get('local', '').lower() and item.get('data') == data_hoje:
            return item

    datas_disponiveis = [item for item in dados_mare if termo_busca_json in item.get('local', '').lower()]
    if datas_disponiveis:
        datas_disponiveis.sort(key=lambda x: x['data'], reverse=True)
        return datas_disponiveis[0]

    return None

def formatar_dados_mare_para_clima(dados_mare):
    if not dados_mare or not dados_mare.get('mares'):
        return None

    mares = dados_mare['mares']
    altas = [m for m in mares if m['tipo'] == 'alta']
    baixas = [m for m in mares if m['tipo'] == 'baixa']

    local_completo = dados_mare.get('local', '')
    nome_porto = f"Porto de {local_completo.title()}"

    resultado = {
        'local': nome_porto,
        'data': dados_mare.get('data', ''),
        'mare_alta': altas,
        'mare_baixa': baixas,
        'proxima_mare': None
    }

    agora = datetime.now().time()
    proximas_mares = []

    for mare in mares:
        try:
            hora_mare = datetime.strptime(mare['hora'], '%H:%M').time()
            if hora_mare > agora:
                proximas_mares.append(mare)
        except ValueError:
            continue

    if proximas_mares:
        resultado['proxima_mare'] = min(proximas_mares, key=lambda x: datetime.strptime(x['hora'], '%H:%M').time())
    elif mares:
        resultado['proxima_mare'] = mares[0]

    return resultado

# --- Rota principal ---
@app.route("/")
def index():
    return render_template("index.html")

# --- Rota da API de Clima (com maré) ---
@app.route("/clima")
def obter_clima():
    if not API_KEY:
        return jsonify({"erro": "Chave da API de clima não configurada"}), 500

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

        lat = dados['coord']['lat']
        lon = dados['coord']['lon']
        dist, porto_id, nome_porto = porto_mais_proximo(lat, lon)

        if dist <= 50:
            dados_mare = obter_dados_mare_do_banco(porto_id)
            if dados_mare:
                resultado["mare"] = formatar_dados_mare_para_clima(dados_mare)
                resultado["eh_litoranea"] = True
            else:
                resultado["mare"] = None
                resultado["eh_litoranea"] = True  # ainda litorânea, só que sem dados disponíveis
        else:
            resultado["mare"] = None
            resultado["eh_litoranea"] = False

        resultado["eh_litoranea"] = True

        return jsonify(resultado)

    except KeyError as e:
        return jsonify({"erro": f"Erro ao processar os dados do clima: {e}"}), 500

# --- Rota da API de Marés (pergunta direta) ---
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

def processar_pergunta_mare(dados_mare, porto_usuario, data_usuario, pergunta):
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

# --- Execução local ---
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
  