
import os
import json
import requests
from flask import Flask, request, jsonify, render_template, redirect, url_for, session, flash
from datetime import datetime, timezone, timedelta
import math
from werkzeug.security import generate_password_hash, check_password_hash

app = Flask(__name__)
app.secret_key = os.urandom(24)  # Para sessões e flash

ADMIN_PASSWORD_RAW = os.getenv("ADMIN_PASSWORD", "admin")
ADMIN_HASH = generate_password_hash(ADMIN_PASSWORD_RAW)

API_KEY = os.environ.get("OPENWEATHER_API_KEY", "0153a042112f9529edbc2bad5372a198")




@app.route("/")
def index():
    if not session.get("logado"):
        return redirect(url_for("login"))
    return render_template("index.html")

@app.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        senha_digitada = request.form.get("senha")
        if check_password_hash(ADMIN_HASH, senha_digitada):
            session["logado"] = True
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("index"))
        else:
            flash("Senha incorreta", "danger")
    return render_template("login.html")

@app.route("/logout")
def logout():
    session.pop("logado", None)
    flash("Você saiu da sessão.", "info")
    return redirect(url_for("login"))

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

    altas = [(m['hora'], m['altura_m']) for m in mares_data if m['tipo'] == 'baixa']
    baixas =  [(m['hora'], m['altura_m']) for m in mares_data if m['tipo'] == 'alta']
    pergunta = pergunta.lower()

    # Maré mais alta (variações)
    if any(p in pergunta for p in [
        "maré mais alta", "maior maré", "pico da maré alta", 
        "qual a maré mais alta", "a que horas a maré estará mais alta",
        "horário da maré mais alta"
    ]):
        mais_alta = max(altas, key=lambda item: item[1]) if altas else None
        if mais_alta:
            return f"A maré mais alta em {data_usuario} será às {mais_alta[0]} com {mais_alta[1]}m."
        return "Não há registros de maré alta para este dia."

    # Maré mais baixa (variações)
    if any(p in pergunta for p in [
        "maré mais baixa", "menor maré", "pico da maré baixa", 
        "qual a maré mais baixa", "a que horas a maré estará mais baixa",
        "horário da maré mais baixa", "qual o horário que a maré está mais baixa", "qual o horário que a maré está mais baixa hoje", "qual horário que a maré está mais baixa"
    ]):
        mais_baixa = min(baixas, key=lambda item: item[1]) if baixas else None
        if mais_baixa:
            return f"A maré mais baixa em {data_usuario} no {porto_usuario} será às {mais_baixa[0]} com {mais_baixa[1]}m."
        return "Não há registros de maré baixa para este dia."

    # Horários de maré alta
    if any(p in pergunta for p in [
        "horário da maré alta", "que horas a maré vai estar alta", 
        "quando maré alta", "quais os horários da maré alta"
    ]):
        return f"Horários de maré alta em {data_usuario}:\n" + "\n".join([f"- {h} com {a}m" for h, a in altas])

    # Horários de maré baixa
    if any(p in pergunta for p in [
        "horário da maré baixa", "que horas a maré vai estar baixa", 
        "quando maré baixa", "quais os horários da maré baixa"
    ]):
        return f"Horários de maré baixaem {data_usuario}:\n" + "\n".join([f"- {h} com {a}m" for h, a in baixas])

    # Quantidade de marés
    if any(p in pergunta for p in ["quantas marés", "quantas vezes", "quantas altas", "quantas baixas"]):
        resposta = []
        if "alta" in pergunta:
            resposta.append(f"Quantidade de marés altas: {len(altas)}")
        elif "baixa" in pergunta:
            resposta.append(f"Quantidade de marés baixas: {len(baixas)}")
        else:
            resposta.append(f"Quantidade total de marés: {len(mares_data)} (Altas: {len(altas)}, Baixas: {len(baixas)})")
        return "\n".join(resposta)

    return ("Não entendi sua pergunta. Tente algo como:\n"
            "- 'Horário da maré alta'\n"
            "- 'Horário da maré baixa'\n"
            "- 'Qual será a maré mais alta?'\n"
            "- 'Quantas marés altas teremos?'")


# --- Rota da API de Tábua Mensal ---
@app.route("/tabua-mensal")
def obter_tabua_mensal():
    cidade = request.args.get("cidade")
    mes = request.args.get("mes")  # formato: YYYY-MM
    
    if not cidade or not mes:
        return jsonify({"erro": "Informe a cidade e o mês"}), 400
    
    try:
        # Obter coordenadas da cidade
        link_geo = f"https://api.openweathermap.org/geo/1.0/direct?q={cidade}&limit=1&appid={API_KEY}"
        resposta_geo = requests.get(link_geo)
        resposta_geo.raise_for_status()
        dados_geo = resposta_geo.json()
        
        if not dados_geo:
            return jsonify({"erro": "Cidade não encontrada"}), 404
            
        lat = dados_geo[0]['lat']
        lon = dados_geo[0]['lon']
        nome_cidade = dados_geo[0]['name']
        
        # Encontrar porto mais próximo
        dist, porto_id, nome_porto = porto_mais_proximo(lat, lon)
        
        if dist > 50:  # Se muito longe do mar
            return jsonify({"erro": "Esta localização está muito distante do mar para dados de maré"}), 400
        
        # Obter dados de marés para o mês
        dados_mensais = obter_dados_mare_mensal(porto_id, mes)
        
        if not dados_mensais:
            return jsonify({"erro": f"Não há dados de maré disponíveis para {nome_cidade} no mês {mes}"}), 404
        
        # Obter dados climáticos para alerta
        link_clima = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&lang=pt_br&units=metric"
        resposta_clima = requests.get(link_clima)
        dados_clima = resposta_clima.json() if resposta_clima.status_code == 200 else None
        
        # Calcular alerta de alagamento
        alerta = calcular_alerta_alagamento(dados_mensais, dados_clima)
        
        # Preparar resposta
        resultado = {
            "cidade": nome_cidade,
            "porto": nome_porto,
            "mes_nome": obter_nome_mes(mes),
            "ano": mes.split('-')[0],
            "dados_grafico": preparar_dados_grafico(dados_mensais),
            "estatisticas": calcular_estatisticas_mensais(dados_mensais),
            "alerta": alerta
        }
        
        return jsonify(resultado)
        
    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Erro na requisição: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

def obter_dados_mare_mensal(porto_id, mes):
    """Obter dados de maré para um mês específico"""
    dados_mare = carregar_dados_mare()
    if not dados_mare:
        return None
    
    termo_busca = porto_id.replace("_", " ")
    dados_do_mes = []
    
    for item in dados_mare:
        if termo_busca in item.get('local', '').lower():
            data_item = item.get('data', '')
            if data_item.startswith(mes):  # YYYY-MM
                dados_do_mes.append(item)
    
    return dados_do_mes

def obter_nome_mes(mes_str):
    """Converter YYYY-MM para nome do mês em português"""
    meses = {
        '01': 'Janeiro', '02': 'Fevereiro', '03': 'Março', '04': 'Abril',
        '05': 'Maio', '06': 'Junho', '07': 'Julho', '08': 'Agosto',
        '09': 'Setembro', '10': 'Outubro', '11': 'Novembro', '12': 'Dezembro'
    }
    mes_num = mes_str.split('-')[1]
    return meses.get(mes_num, 'Mês')

def preparar_dados_grafico(dados_mensais):
    """Preparar dados para o gráfico Chart.js"""
    labels = []
    alturas = []
    cores = []
    
    for dia_dados in sorted(dados_mensais, key=lambda x: x.get('data', '')):
        data = dia_dados.get('data', '')
        mares = dia_dados.get('mares', [])
        
        for mare in mares:
            # Formato: DD/MM
            dia = data.split('-')[2]
            mes = data.split('-')[1]
            label = f"{dia}/{mes}"
            
            labels.append(f"{label} {mare['hora']}")
            alturas.append(float(mare['altura_m']))
            
            # Cor baseada no tipo de maré
            if mare['tipo'] == 'alta':
                cores.append('#10b981')  # Verde para maré alta
            else:
                cores.append('#f59e0b')  # Amarelo para maré baixa
    
    return {
        "labels": labels,
        "alturas": alturas,
        "cores": cores
    }

def calcular_estatisticas_mensais(dados_mensais):
    """Calcular estatísticas do mês"""
    todas_mares = []
    mares_altas = []
    mares_baixas = []
    
    for dia_dados in dados_mensais:
        mares = dia_dados.get('mares', [])
        for mare in mares:
            altura = float(mare['altura_m'])
            todas_mares.append(altura)
            
            if mare['tipo'] == 'alta':
                mares_altas.append(altura)
            else:
                mares_baixas.append(altura)
    
    if not todas_mares:
        return {
            "maior_alta": "N/A",
            "menor_baixa": "N/A", 
            "amplitude_media": "N/A",
            "total_mares": 0
        }
    
    maior_alta = max(mares_altas) if mares_altas else 0
    menor_baixa = min(mares_baixas) if mares_baixas else 0
    amplitude_media = round((maior_alta - menor_baixa), 2) if mares_altas and mares_baixas else 0
    
    return {
        "maior_alta": f"{maior_alta:.2f}",
        "menor_baixa": f"{menor_baixa:.2f}",
        "amplitude_media": f"{amplitude_media:.2f}",
        "total_mares": len(todas_mares)
    }

def calcular_alerta_alagamento(dados_mensais, dados_clima):
    """Calcular nível de alerta de alagamento baseado em marés e clima"""
    if not dados_mensais:
        return {
            "nivel": "BAIXO",
            "descricao": "Dados insuficientes para análise"
        }
    
    # Calcular altura média das marés altas
    mares_altas = []
    for dia_dados in dados_mensais:
        mares = dia_dados.get('mares', [])
        for mare in mares:
            if mare['tipo'] == 'alta':
                mares_altas.append(float(mare['altura_m']))
    
    if not mares_altas:
        return {
            "nivel": "BAIXO",
            "descricao": "Sem dados de marés altas disponíveis"
        }
    
    altura_media_alta = sum(mares_altas) / len(mares_altas)
    altura_maxima = max(mares_altas)
    
    # Fatores climáticos (se disponíveis)
    fator_clima = 1.0
    if dados_clima:
        # Pressão baixa e umidade alta aumentam risco
        pressao = dados_clima.get('main', {}).get('pressure', 1013)
        umidade = dados_clima.get('main', {}).get('humidity', 50)
        vento = dados_clima.get('wind', {}).get('speed', 0)
        
        if pressao < 1000:  # Pressão muito baixa
            fator_clima += 0.3
        elif pressao < 1010:  # Pressão baixa
            fator_clima += 0.1
            
        if umidade > 80:  # Umidade muito alta
            fator_clima += 0.2
        elif umidade > 70:  # Umidade alta
            fator_clima += 0.1
            
        if vento > 10:  # Vento forte
            fator_clima += 0.2
    
    # Calcular risco baseado na altura das marés e fatores climáticos
    risco_base = altura_maxima * fator_clima
    
    if risco_base >= 2.5 or altura_media_alta >= 2.0:
        return {
            "nivel": "ALTO",
            "descricao": "Marés excepcionalmente altas combinadas com condições climáticas adversas. Alto risco de alagamentos costeiros."
        }
    elif risco_base >= 1.8 or altura_media_alta >= 1.5:
        return {
            "nivel": "MÉDIO", 
            "descricao": "Marés elevadas com possível influência de condições meteorológicas. Risco moderado de alagamentos em áreas baixas."
        }
    else:
        return {
            "nivel": "BAIXO",
            "descricao": "Condições normais de maré. Baixo risco de alagamentos, mas mantenha-se atento às condições locais."
        }

# --- Execução local ---
if __name__ == "__main__":
    app.run(debug=True, host='0.0.0.0', port=5000)
  

# --- NOVAS FUNCIONALIDADES PARA TÁBUA DE MARÉS ---

def criar_mapeamento_portos():
    """Cria mapeamento entre nomes dos portos no JSON e na lista PORTOS_DISPONIVEIS"""
    mapeamento = {}
    
    # Mapeamento manual baseado na análise dos dados
    mapeamentos_manuais = {
        "sao luis": ["11   sao luis  ma 41 43"],
        "alumar": ["12   terminal da alumar   ma 44 46"],
        "ponta_madeira": ["13   terminal da ponta da madeira   ma 47 49"],
        "itaqui": ["14   porto de itaqui   ma 50 52"],
        "luis_correia": ["15   PORTO DE LUÍS CORREIA  PI 53 55"],
        "pecem": ["16   terminal portuario do pecem   ce 56 58"],
        "mucuripe": ["17   porto de mucuripe   ce 59 61"],
        "fernando_noronha": ["18   arquipelago de fernando de noronha  bs 62 64"],
        "areia_branca": ["19   porto de areia branca   termisa   rn 65 67"],
        "macau": ["20   PORTO DE MACAU   RN   68 70"],
        "guamare": ["21   PORTO DE GUAMARÉ   RN   71 73"],
        "natal": ["22   porto de natal   capitania dos portos do rn   74 76"],
        "cabedelo": ["23   porto de cabedelo   pb   77 79"],
        "recife": ["24   PORTO DO RECIFE  PE   80 82"],
        "suape": ["25   PORTO DE SUAPE  PE   83 85"],
        "maceio": ["26   porto de maceio   al   86 88"],
        "madre_de_deus": ["29   porto de madre de deus   ba   95 97"],
        "aratu": ["30   porto de aratu   base naval   ba   98 100"],
        "salvador": ["31   PORTO DE SALVADOR   BA   101 103"],
        "ilheus_malhado": ["32   PORTO DE ILHÉUS   MALHADO   BA   104 106"],
        "barra_riacho": ["33   TERMINAL DE BARRA DO RIACHO   ES   107 109"],
        "tubarao": ["34   PORTO DE TUBARÃO   ES   110 112"],
        "vitoria": ["35   PORTO DE VITÓRIA 113   115"],
        "ilha_trindade": ["36   ILHA DA TRINDADE   116 118"],
        "ponta_ubu": ["37   TERMINAL DA PONTA DO UBU   ES   119 121"],
        "imbetiba": ["39   TERMINAL MARÍTIMO DE IMBETIBA   RJ   125 127"],
        "ilha_fiscal": ["40   PORTO DO RIO DE JANEIRO   ILHA FISCAL   RJ   128 130"],
        "itaguai": ["41   PORTO DE ITAGUAÍ   RJ   131 133"],
        "forno": ["42   PORTO DO FORNO   RJ   134 136"],
        "ilha_guaiba": ["43   TERMINAL DA ILHA GUAÍBA   RJ   137 139"],
        "angra_reis": ["44   PORTO DE ANGRA DOS REIS   RJ   140 142"],
        "santos": ["46   PORTO DE SANTOS    146 148"],
        "ponta_felix": ["47   TERMINAL DA PONTA DO FELIX    149 151"],
        "paranagua": ["48   PORTO DE PARANAGUÁ    152 154"],
        "canal_sueste": ["49   BARRA DE PARANAGUÁ   CANAL SUESTE   155 157"],
        "canal_galheta": ["50   BARRA DE PARANAGUÁ   CANAL GALHETA   158 160"],
        "sao_francisco_sul": ["51   PORTO DE SÃO FRANCISCO DO SUL   161 163", "51   PORTO DE SÃO FRANCISCO DO SUL   161 163 0"],
        "imbituba": ["54   PORTO DE IMBITUBA    170 172"],
        "rio_grande_rs": ["55   PORTO DO RIO GRANDE    173 175"],
        "igarape_grande_curua": ["2   igarape grande do curua 14 16"],
        "barra_norte_arco_lamoso": ["1   barra norte   arco lamoso 11 13", "1   barra norte   arco lamoso 11 13 (1)"],
        "porto_santana": ["3   porto de santana   cia docas de santana  ap 17 19"],
        "ilha_guaras": ["4   ILHA DOS GUARÁS   PA 20 22"],
        "salinopolis": ["5   FUNDEADOURO DE SALINÓPOLIS   PA 23  25"],
        "mosqueiro": ["6   ILHA DO MOSQUEIRO 26   28"],
        "belem": ["7   PORTO DE BELÉM   PA 29 31"],
        "vila_conde": ["8   PORTO DE VILA DO CONDE   PA 32 34"],
        "breves": ["9   ATRACADOURO DE BREVES   PA 35 37"]
    }
    
    return mapeamentos_manuais

def obter_portos_disponiveis():
    """Retorna lista de portos disponíveis para seleção"""
    portos = []
    for nome, slug, lat, lon in PORTOS_DISPONIVEIS:
        portos.append({
            "nome": nome,
            "slug": slug,
            "latitude": lat,
            "longitude": lon
        })
    return portos

def obter_dados_mare_mensal(porto_slug, mes, ano=2025):
    """Obtém dados de marés para um porto específico em um mês"""
    dados_mare = carregar_dados_mare()
    if not dados_mare:
        return None
    
    mapeamento = criar_mapeamento_portos()
    locais_json = mapeamento.get(porto_slug, [])
    
    if not locais_json:
        return None
    
    # Filtrar dados do mês especificado
    dados_mes = []
    for item in dados_mare:
        local_item = item.get('local', '').lower()
        data_item = item.get('data', '')
        
        # Verificar se é o local correto
        local_encontrado = False
        for local_json in locais_json:
            if local_json.lower() in local_item:
                local_encontrado = True
                break
        
        if local_encontrado and data_item:
            try:
                data_obj = datetime.strptime(data_item, '%Y-%m-%d')
                if data_obj.year == ano and data_obj.month == mes:
                    dados_mes.append(item)
            except ValueError:
                continue
    
    return dados_mes

def processar_dados_tabua_mares(dados_mes):
    """Processa dados mensais para criar tábua de marés"""
    if not dados_mes:
        return None
    
    tabua = []
    
    for item in dados_mes:
        data = item.get('data', '')
        mares = item.get('mares', [])
        
        if not mares:
            continue
            
        # Separar marés altas e baixas
        mares_altas = [m for m in mares if m.get('tipo') == 'baixa']
        mares_baixas =  [m for m in mares if m.get('tipo') == 'alta']
       
        
        # Encontrar a maré mais alta e mais baixa do dia
        mare_mais_alta = min(mares_baixas, key=lambda x: x.get('altura_m', float('inf'))) if mares_baixas else None
        mare_mais_baixa = max(mares_altas, key=lambda x: x.get('altura_m', 0)) if mares_altas else None
        
        dia_data = {
            'data': data,
            'dia': datetime.strptime(data, '%Y-%m-%d').day,
            'mare_mais_alta': mare_mais_alta,
            'mare_mais_baixa': mare_mais_baixa,
            'todas_mares': mares
        }
        
        tabua.append(dia_data)
    
    # Ordenar por data
    tabua.sort(key=lambda x: x['data'])
    
    return tabua

@app.route('/tabua_mares', methods=['GET'])
def obter_tabua_mares():
    """API para obter tábua de marés mensal"""
    porto_slug = request.args.get('porto')
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', default=2025, type=int)
    
    if not porto_slug or not mes:
        return jsonify({"erro": "Parâmetros 'porto' e 'mes' são obrigatórios"}), 400
    
    if mes < 1 or mes > 12:
        return jsonify({"erro": "Mês deve estar entre 1 e 12"}), 400
    
    # Obter dados do mês
    dados_mes = obter_dados_mare_mensal(porto_slug, mes, ano)
    if not dados_mes:
        return jsonify({"erro": "Dados não encontrados para o porto e mês especificados"}), 404
    
    # Processar dados para tábua
    tabua = processar_dados_tabua_mares(dados_mes)
    if not tabua:
        return jsonify({"erro": "Não foi possível processar os dados de marés"}), 500
    
    # Encontrar porto na lista
    porto_info = None
    for nome, slug, lat, lon in PORTOS_DISPONIVEIS:
        if slug == porto_slug:
            porto_info = {"nome": nome, "slug": slug, "latitude": lat, "longitude": lon}
            break
    
    resultado = {
        "porto": porto_info,
        "mes": mes,
        "ano": ano,
        "total_dias": len(tabua),
        "tabua": tabua
    }
    
    return jsonify(resultado)

@app.route('/PORTOS_DISPONIVEIS', methods=['GET'])
def listar_portos():
    """API para listar todos os portos disponíveis"""
    portos = obter_portos_disponiveis()
    return jsonify({"portos": portos})



# --- SISTEMA DE ALERTAS DE ALAGAMENTO ---

def analisar_risco_alagamento(dados_clima, dados_mare):
    """Analisa risco de alagamento baseado em clima e marés"""
    alertas = []
    nivel_risco = "baixo"
    
    if not dados_clima or not dados_mare:
        return {"nivel": "indeterminado", "alertas": ["Dados insuficientes para análise"]}
    
    # Critérios de análise
    umidade = dados_clima.get('umidade', 0)
    nuvens = dados_clima.get('nuvens', 0)
    pressao = dados_clima.get('pressao', 1013)
    vento = dados_clima.get('vento', 0)
    
    # Verificar se há marés altas significativas
    mares_altas = dados_mare.get('mare_alta', [])
    mare_mais_alta = max(mares_altas, key=lambda x: x.get('altura_m', 0)) if mares_altas else None
    
    # Análise de condições meteorológicas
    condicoes_chuva = False
    if umidade > 80 and nuvens > 70:
        condicoes_chuva = True
        alertas.append("Alta umidade e cobertura de nuvens indicam possibilidade de chuva")
    
    if pressao < 1000:
        condicoes_chuva = True
        alertas.append("Baixa pressão atmosférica pode indicar sistema de tempestade")
    
    if vento > 10:
        alertas.append("Ventos fortes podem intensificar ondas e marés")
    
    # Análise de marés
    mare_critica = False
    if mare_mais_alta and mare_mais_alta.get('altura_m', 0) > 4.0:
        mare_critica = True
        alertas.append(f"Maré alta significativa prevista: {mare_mais_alta.get('altura_m')}m às {mare_mais_alta.get('hora')}")
    
    # Determinar nível de risco
    if condicoes_chuva and mare_critica:
        nivel_risco = "alto"
        alertas.append("⚠️ RISCO ALTO: Combinação de condições meteorológicas adversas com maré alta")
    elif condicoes_chuva or mare_critica:
        nivel_risco = "moderado"
        if condicoes_chuva:
            alertas.append("⚠️ RISCO MODERADO: Condições meteorológicas podem causar alagamentos")
        if mare_critica:
            alertas.append("⚠️ RISCO MODERADO: Maré alta pode causar alagamentos costeiros")
    
    # Recomendações específicas
    recomendacoes = []
    if nivel_risco == "alto":
        recomendacoes.extend([
            "Evite áreas baixas e próximas ao mar",
            "Monitore boletins meteorológicos constantemente",
            "Tenha plano de evacuação preparado",
            "Evite atividades marítimas"
        ])
    elif nivel_risco == "moderado":
        recomendacoes.extend([
            "Mantenha-se atento às condições meteorológicas",
            "Evite áreas de risco conhecidas",
            "Tenha cuidado em atividades próximas ao mar"
        ])
    else:
        recomendacoes.append("Condições normais, mas mantenha sempre atenção às mudanças meteorológicas")
    
    return {
        "nivel": nivel_risco,
        "alertas": alertas,
        "recomendacoes": recomendacoes,
        "dados_analisados": {
            "umidade": umidade,
            "nuvens": nuvens,
            "pressao": pressao,
            "vento": vento,
            "mare_mais_alta": mare_mais_alta
        }
    }

def obter_previsao_estendida(lat, lon):
    """Obtém previsão estendida para análise de risco"""
    if not API_KEY:
        return None
    
    try:
        # Usar API de previsão de 5 dias
        link = f"https://api.openweathermap.org/data/2.5/forecast?lat={lat}&lon={lon}&appid={API_KEY}&lang=pt_br&units=metric"
        resposta = requests.get(link)
        resposta.raise_for_status()
        dados = resposta.json()
        
        previsoes = []
        for item in dados.get('list', [])[:8]:  # Próximas 24 horas (8 períodos de 3h)
            previsao = {
                'datetime': item.get('dt_txt'),
                'temperatura': item['main']['temp'],
                'umidade': item['main']['humidity'],
                'pressao': item['main']['pressure'],
                'nuvens': item['clouds']['all'],
                'vento': item['wind']['speed'],
                'descricao': item['weather'][0]['description'],
                'chuva': item.get('rain', {}).get('3h', 0)  # Chuva em 3h
            }
            previsoes.append(previsao)
        
        return previsoes
    except:
        return None

@app.route('/alertas_alagamento', methods=['GET'])
def obter_alertas_alagamento():
    """API para obter alertas de alagamento para uma localização"""
    cidade = request.args.get("cidade")
    lat = request.args.get("lat")
    lon = request.args.get("lon")
    
    if not ((lat and lon) or cidade):
        return jsonify({"erro": "Informe cidade ou coordenadas"}), 400
    
    try:
        # Obter dados climáticos atuais
        if lat and lon:
            link_clima = f"https://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&lang=pt_br&units=metric"
        else:
            link_clima = f"https://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={API_KEY}&lang=pt_br&units=metric"
        
        resposta_clima = requests.get(link_clima)
        resposta_clima.raise_for_status()
        dados_clima = resposta_clima.json()
        
        if dados_clima.get("cod") != 200:
            return jsonify({"erro": "Localização não encontrada"}), 404
        
        # Obter coordenadas
        lat_local = dados_clima['coord']['lat']
        lon_local = dados_clima['coord']['lon']
        
        # Encontrar porto mais próximo
        dist, porto_id, nome_porto = porto_mais_proximo(lat_local, lon_local)
        
        dados_mare = None
        if dist <= 50:  # Apenas se estiver próximo ao litoral
            dados_mare_raw = obter_dados_mare_do_banco(porto_id)
            if dados_mare_raw:
                dados_mare = formatar_dados_mare_para_clima(dados_mare_raw)
        
        # Obter previsão estendida
        previsao_estendida = obter_previsao_estendida(lat_local, lon_local)
        
        # Analisar risco
        analise_risco = analisar_risco_alagamento(dados_clima, dados_mare)
        
        # Análise adicional com previsão estendida
        if previsao_estendida:
            chuva_total_24h = sum(p.get('chuva', 0) for p in previsao_estendida)
            if chuva_total_24h > 20:  # Mais de 20mm em 24h
                analise_risco['alertas'].append(f"Previsão de chuva significativa: {chuva_total_24h:.1f}mm nas próximas 24h")
                if analise_risco['nivel'] == 'baixo':
                    analise_risco['nivel'] = 'moderado'
                elif analise_risco['nivel'] == 'moderado':
                    analise_risco['nivel'] = 'alto'
        
        resultado = {
            "localizacao": {
                "cidade": dados_clima["name"],
                "pais": dados_clima['sys']['country'],
                "latitude": lat_local,
                "longitude": lon_local
            },
            "eh_litoranea": dist <= 50,
            "porto_proximo": {
                "nome": nome_porto,
                "distancia_km": round(dist, 1)
            } if dist <= 50 else None,
            "analise_risco": analise_risco,
            "previsao_chuva_24h": sum(p.get('chuva', 0) for p in previsao_estendida) if previsao_estendida else None,
            "timestamp": datetime.now().isoformat()
        }
        
        return jsonify(resultado)
        
    except requests.exceptions.RequestException as e:
        return jsonify({"erro": f"Erro na requisição: {str(e)}"}), 500
    except Exception as e:
        return jsonify({"erro": f"Erro interno: {str(e)}"}), 500

