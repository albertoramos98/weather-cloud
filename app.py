import os
import json
import requests
from flask import Flask, request, jsonify, render_template, send_from_directory
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
    ("Porto do Recife", "recife_pe", -8.03, -34.52),
    ("Porto de Suape", "suape", -8.42, -34.95),

    # Piauí
    ("Porto de Luís Correia", "luis_correia", -2.88, -41.67),

    # Rio de Janeiro
    ("Porto do Rio de Janeiro", "rio_janeiro", -22.9, -43.17),
    ("Terminal da Ilha Guaíba", "ilha_guaiba", -22.85, -43.2),
    ("Porto de Itaguaí", "itaguai", -22.85, -43.78),
    ("Terminal de Angra dos Reis", "angra_reis", -23.01, -44.32),
    ("Porto de Cabo Frio", "cabo_frio", -22.88, -42.02),
    ("Barra de São João", "barra_sao_joao", -22.62, -41.95),

    # Rio Grande do Norte
    ("Porto de Natal", "natal", -5.78, -35.2),
    ("Terminal Salineiro de Areia Branca", "areia_branca", -4.95, -37.13),
    ("Porto de Macau", "macau", -5.12, -36.63),
    ("Terminal Salineiro de Grossos", "grossos", -4.98, -37.15),

    # Rio Grande do Sul
    ("Porto de Rio Grande", "rio_grande", -32.03, -52.1),

    # Santa Catarina
    ("Porto de Itajaí", "itajai", -26.9, -48.67),
    ("Porto de São Francisco do Sul", "sao_francisco_sul", -26.24, -48.63),
    ("Porto de Imbituba", "imbituba", -28.24, -48.67),
    ("Terminal Portuário de Navegantes", "navegantes", -26.9, -48.65),

    # São Paulo
    ("Porto de Santos", "santos_sp", -23.96, -46.33),
    ("Terminal de São Sebastião", "sao_sebastiao", -23.8, -45.4),

    # Sergipe
    ("Porto de Sergipe", "sergipe", -10.9, -37.05),
    ("Terminal Marítimo Inácio Barbosa", "inacio_barbosa", -10.92, -37.05),

    # Especial
    ("Estação Antártica Comandante Ferraz", "antartica", -62.08, -58.4),
]

# Carregar dados de marés do JSON
def carregar_dados_mares():
    try:
        with open('banco_mareas.json', 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        print("Arquivo banco_mareas.json não encontrado!")
        return []

DADOS_MARES = carregar_dados_mares()

def calcular_distancia(lat1, lon1, lat2, lon2):
    
    R = 6371  # Raio da Terra em km
    
    lat1_rad = math.radians(lat1)
    lon1_rad = math.radians(lon1)
    lat2_rad = math.radians(lat2)
    lon2_rad = math.radians(lon2)
    
    dlat = lat2_rad - lat1_rad
    dlon = lon2_rad - lon1_rad
    
    a = math.sin(dlat/2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon/2)**2
    c = 2 * math.atan2(math.sqrt(a), math.sqrt(1-a))
    
    return R * c

def encontrar_porto_mais_proximo(lat, lon):

    menor_distancia = float('inf')
    porto_mais_proximo = None
    
    for nome, slug, porto_lat, porto_lon in PORTOS_DISPONIVEIS:
        distancia = calcular_distancia(lat, lon, porto_lat, porto_lon)
        if distancia < menor_distancia:
            menor_distancia = distancia
            porto_mais_proximo = (nome, slug, porto_lat, porto_lon)
    
    return porto_mais_proximo

def buscar_dados_mare_por_local(termo_busca):
    
    termo_busca_json = termo_busca.lower().replace(" ", "_").replace("ã", "a").replace("ç", "c")
    
 
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    for item in DADOS_MARES:
        if termo_busca_json in item.get('local', '').lower() and item.get('data') == data_hoje:
            return item


    datas_disponiveis = [item for item in DADOS_MARES if termo_busca_json in item.get('local', '').lower()]
    if datas_disponiveis:
        datas_disponiveis.sort(key=lambda x: x['data'], reverse=True)
        return datas_disponiveis[0]

    return None

def formatar_dados_mare_para_clima(dados_mare):
    if not dados_mare or not dados_mare.get('mares'):
        return None

    mares = dados_mare['mares']
   
    mares_ordenados = sorted(mares, key=lambda x: x['altura_m'])
    
  
    maresBaixas = mares_ordenados[:len(mares_ordenados)//2] if len(mares_ordenados) > 1 else [mares_ordenados[0]]

    maresAltas = mares_ordenados[len(mares_ordenados)//2:] if len(mares_ordenados) > 1 else [mares_ordenados[0]]

    local_completo = dados_mare.get('local', '')
    nome_porto = f"Porto de {local_completo.title()}"

    resultado = {
        'local': nome_porto,
        'data': dados_mare.get('data', ''),
        'mare_alta': maresAltas,
        'mare_baixa': maresBaixas,
        'proxima_mare': None
    }

    # Encontrar próxima maré
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


@app.route('/tabua_mares')
def tabua_mares():
    """API para gerar tábua de marés mensal"""
    cidade = request.args.get('cidade', '').lower()
    mes = request.args.get('mes', type=int)
    ano = request.args.get('ano', 2025, type=int)
    
    if not cidade or not mes:
        return jsonify({"erro": "Parâmetros cidade e mes são obrigatórios"}), 400
    
    if mes < 1 or mes > 12:
        return jsonify({"erro": "Mês deve estar entre 1 e 12"}), 400
    
    # cidade busca no JSON
    termo_busca = cidade.replace(" ", "_").replace("ã", "a").replace("ç", "c")
    
    dados_mes = []
    for item in DADOS_MARES:
        if termo_busca in item.get('local', '').lower():
            data_item = datetime.strptime(item['data'], '%Y-%m-%d')
            if data_item.year == ano and data_item.month == mes:
                dados_mes.append(item)
    
    if not dados_mes:
        return jsonify({"erro": f"Nenhum dado encontrado para {cidade} em {mes:02d}/{ano}"}), 404
    
    tabua = {}
    for item in dados_mes:
        dia = datetime.strptime(item['data'], '%Y-%m-%d').day
        mares = item['mares']
        
        if not mares:
            continue
            
        mares_ordenados = sorted(mares, key=lambda x: x['altura_m'])
        
        mare_mais_baixa = mares_ordenados[0]  
        mare_mais_alta = mares_ordenados[-1]  
        
        tabua[dia] = {
            'dia': dia,
            'data': item['data'],
            'mare_mais_baixa': mare_mais_baixa,
            'mare_mais_alta': mare_mais_alta,
            'todas_mares': mares
        }
    
    tabua_lista = [tabua[dia] for dia in sorted(tabua.keys())]
    
    return jsonify({
        "cidade": cidade.title(),
        "mes": mes,
        "ano": ano,
        "total_dias": len(tabua_lista),
        "tabua": tabua_lista
    })

@app.route('/alertas_alagamento')
def alertas_alagamento():
    """API para análise de risco de alagamento"""
    cidade = request.args.get('cidade')
    lat = request.args.get('lat', type=float)
    lon = request.args.get('lon', type=float)
    
    if not cidade and (not lat or not lon):
        return jsonify({"erro": "Forneça cidade ou coordenadas (lat, lon)"}), 400
    
    if lat and lon:
        porto_info = encontrar_porto_mais_proximo(lat, lon)
        if porto_info:
            cidade = porto_info[1]  # slug do porto
    
    try:
        if lat and lon:
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?lat={lat}&lon={lon}&appid={API_KEY}&units=metric&lang=pt_br"
        else:
            weather_url = f"http://api.openweathermap.org/data/2.5/weather?q={cidade}&appid={API_KEY}&units=metric&lang=pt_br"
        
        response = requests.get(weather_url)
        if response.status_code != 200:
            return jsonify({"erro": "Dados meteorológicos não disponíveis"}), 404
            
        dados_clima = response.json()
        
    except Exception as e:
        return jsonify({"erro": f"Erro ao buscar dados meteorológicos: {str(e)}"}), 500
    
    # Buscar dados de marés
    dados_mare = buscar_dados_mare_por_local(cidade)
    
    # Análise de risco
    risco = analisar_risco_alagamento(dados_clima, dados_mare)
    
    return jsonify({
        "cidade": cidade.title(),
        "coordenadas": {"lat": lat, "lon": lon} if lat and lon else None,
        "analise_risco": risco,
        "dados_clima": {
            "temperatura": dados_clima['main']['temp'],
            "umidade": dados_clima['main']['humidity'],
            "pressao": dados_clima['main']['pressure'],
            "nuvens": dados_clima['clouds']['all'],
            "descricao": dados_clima['weather'][0]['description']
        },
        "dados_mare": formatar_dados_mare_para_clima(dados_mare) if dados_mare else None
    })

def analisar_risco_alagamento(dados_clima, dados_mare):
    """Analisa risco de alagamento baseado em dados meteorológicos e de marés"""
    
    # Extrair dados meteorológicos
    umidade = dados_clima['main']['humidity']
    pressao = dados_clima['main']['pressure']
    nuvens = dados_clima['clouds']['all']
    
    # Verificar se há previsão de chuva
    chuva = dados_clima.get('rain', {}).get('1h', 0)  # mm/h
    
    # Analisar marés
    mare_alta_max = 0
    if dados_mare and dados_mare.get('mares'):
        alturas = [m['altura_m'] for m in dados_mare['mares']]
        mare_alta_max = max(alturas)
    
    # Calcular pontuação de risco
    pontos_risco = 0
    fatores = []
    
    # Critérios meteorológicos
    if umidade > 80:
        pontos_risco += 2
        fatores.append("Umidade alta (>80%)")
    
    if pressao < 1000:
        pontos_risco += 2
        fatores.append("Pressão baixa (<1000 hPa)")
    
    if nuvens > 70:
        pontos_risco += 1
        fatores.append("Muitas nuvens (>70%)")
    
    if chuva > 5:
        pontos_risco += 3
        fatores.append(f"Chuva intensa ({chuva:.1f}mm/h)")
    elif chuva > 0:
        pontos_risco += 1
        fatores.append(f"Chuva leve ({chuva:.1f}mm/h)")
    
    # Critérios de maré
    if mare_alta_max > 4.0:
        pontos_risco += 3
        fatores.append(f"Maré muito alta ({mare_alta_max:.1f}m)")
    elif mare_alta_max > 3.0:
        pontos_risco += 2
        fatores.append(f"Maré alta ({mare_alta_max:.1f}m)")
    elif mare_alta_max > 2.0:
        pontos_risco += 1
        fatores.append(f"Maré moderada ({mare_alta_max:.1f}m)")
    
    # Determinar nível de risco
    if pontos_risco >= 6:
        nivel = "Alto"
        cor = "#ef4444"
        recomendacao = "Evite áreas baixas e próximas ao mar. Monitore alertas oficiais."
    elif pontos_risco >= 3:
        nivel = "Moderado"
        cor = "#f59e0b"
        recomendacao = "Atenção redobrada em áreas costeiras. Evite deslocamentos desnecessários."
    else:
        nivel = "Baixo"
        cor = "#10b981"
        recomendacao = "Condições normais. Mantenha-se informado sobre mudanças climáticas."
    
    return {
        "nivel": nivel,
        "pontuacao": pontos_risco,
        "cor": cor,
        "fatores": fatores,
        "recomendacao": recomendacao,
        "mare_maxima": mare_alta_max
    }

# --- ROTA PARA SERVIR BANCO DE DADOS ---
@app.route('/banco_mareas.json')
def servir_banco_mares():
    """Servir arquivo JSON de marés"""
    try:
        return send_from_directory('.', 'banco_mareas.json')
    except FileNotFoundError:
        return jsonify({"erro": "Arquivo banco_mareas.json não encontrado"}), 404

# --- ROTAS ORIGINAIS (MANTIDAS) ---


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
            print(f"🌊 Cidade litorânea encontrada! Porto: {nome_porto} (distância: {dist:.1f}km)")
            dados_mare = obter_dados_mare_do_banco(porto_id)
            if dados_mare:
                resultado["mare"] = formatar_dados_mare_para_clima(dados_mare)
                resultado["eh_litoranea"] = True
                print(f"✅ Dados de maré adicionados para {nome_porto}")
            else:
                resultado["mare"] = None
                resultado["eh_litoranea"] = True  # ainda litorânea, só que sem dados disponíveis
                print(f"⚠️ Porto litorâneo mas sem dados de maré disponíveis")
        else:
            resultado["mare"] = None
            resultado["eh_litoranea"] = False
            print(f"🏔️ Cidade não litorânea (distância do porto mais próximo: {dist:.1f}km)")

        # Forçar como litorânea para teste (remover depois)
        # resultado["eh_litoranea"] = True

        return jsonify(resultado)

    except KeyError as e:
        return jsonify({"erro": f"Erro ao processar os dados do clima: {e}"}), 500

def converter_timestamp(timestamp, timezone_offset):
    """Converte timestamp Unix para horário local"""
    dt = datetime.fromtimestamp(timestamp, tz=timezone.utc)
    dt_local = dt + timedelta(seconds=timezone_offset)
    return dt_local.strftime('%H:%M')

def porto_mais_proximo(lat, lon):
    """Encontra o porto mais próximo das coordenadas"""
    menor_distancia = float('inf')
    porto_mais_proximo = None
    
    for nome, slug, porto_lat, porto_lon in PORTOS_DISPONIVEIS:
        distancia = calcular_distancia(lat, lon, porto_lat, porto_lon)
        if distancia < menor_distancia:
            menor_distancia = distancia
            porto_mais_proximo = (menor_distancia, slug, nome)
    
    return porto_mais_proximo

def obter_dados_mare_do_banco(porto_id):
    """Obtém dados de maré do banco para um porto específico"""
    print(f"🔍 Buscando dados de maré para porto: {porto_id}")
    
    # Tentar diferentes variações do nome
    variacoes = [
        porto_id,
        porto_id.lower(),
        porto_id.replace("_", " "),
        porto_id.replace("_", ""),
        porto_id.split("_")[0] if "_" in porto_id else porto_id
    ]
    
    data_hoje = datetime.now().strftime('%Y-%m-%d')
    
    for variacao in variacoes:
        print(f"  Tentando variação: '{variacao}'")
        
        # Buscar dados para hoje
        for item in DADOS_MARES:
            local_item = item.get('local', '').lower()
            if variacao.lower() in local_item:
                print(f"  ✅ Encontrado: {item.get('local')} para {item.get('data')}")
                return item
    
    # Se não encontrar, pegar qualquer dado disponível do primeiro porto
    if DADOS_MARES:
        print(f"  ⚠️ Usando dados do primeiro porto disponível: {DADOS_MARES[0].get('local')}")
        return DADOS_MARES[0]
    
    print(f"  ❌ Nenhum dado encontrado")
    return None

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)

