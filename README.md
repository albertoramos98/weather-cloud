# CliMar - Sistema de Clima e Marés 🌊

Aplicação web para consulta de informações meteorológicas e oceanográficas em tempo real, com nova funcionalidade de **Tábua de Marés** e **Sistema de Alertas de Alagamento**.

## 🆕 Novas Funcionalidades

### 📊 Tábua de Marés Mensal
- **Seleção Intuitiva**: Escolha o porto e mês de 2025 através de dropdowns
- **Gráfico Interativo**: Visualização das variações de maré ao longo do mês
- **Dados Detalhados**: Tabela com horários e alturas das marés mais altas e baixas de cada dia
- **56 Portos Disponíveis**: Cobertura completa do litoral brasileiro

### ⚠️ Sistema de Alertas de Alagamento
- **Análise Inteligente**: Combina dados meteorológicos e de marés
- **3 Níveis de Risco**: Baixo, Moderado e Alto
- **Critérios Técnicos**:
  - Umidade > 80% + Nuvens > 70%
  - Pressão atmosférica < 1000 hPa
  - Marés altas > 4.0m
  - Previsão de chuva > 20mm/24h
- **Recomendações**: Orientações específicas para cada nível de risco

## 🚀 Como Atualizar Seu Projeto

### Arquivos para Substituir:
1. **`app.py`** → Substitua o arquivo raiz do seu projeto
2. **`templates/index.html`** → Substitua o arquivo na pasta templates

### Arquivos que Permanecem Iguais:
- `banco_mareas.json` ✅
- `.env` ✅  
- `requirements.txt` ✅
- `static/image1(1).png` ✅

## 📋 Instalação e Execução

### 1. Instalar Dependências
```bash
pip install -r requirements.txt
```

### 2. Configurar Variáveis de Ambiente
Certifique-se que o arquivo `.env` contém:
```
OPENWEATHER_API_KEY=sua_chave_aqui
```

### 3. Executar Aplicação
```bash
python app.py
```

### 4. Acessar no Navegador
```
http://localhost:5000
```

## 🎯 Como Usar as Novas Funcionalidades

### Tábua de Marés:
1. Clique na aba **"Marés"**
2. Selecione um **porto** no dropdown
3. Escolha um **mês de 2025**
4. Clique em **"Gerar Tábua de Marés"**
5. Visualize o gráfico e dados detalhados

### Alertas de Alagamento:
- **Na aba Clima**: Aparecem automaticamente ao buscar cidades litorâneas
- **Na aba Marés**: Exibidos ao selecionar um porto específico

## 🏗️ Estrutura do Projeto

```
seu_projeto/
├── app.py               
├── templates/
│   └── index.html       
├── static/
│   └── image1(1).png     
├── banco_mareas.json    
├── .env                  
├── requirements.txt      
└── README.md            # 📖 Este arquivo
```

## 🔧 Tecnologias Utilizadas

- **Backend**: Flask, Python 3.11
- **Frontend**: HTML5, CSS3, JavaScript ES6+
- **Gráficos**: Chart.js
- **Mapas**: Leaflet.js
- **APIs**: OpenWeatherMap
- **Dados**: JSON estruturado (56 portos brasileiros)

## 📡 Novas APIs Disponíveis

### 1. Lista de Portos
```http
GET /portos_disponiveis
```
Retorna todos os portos disponíveis para seleção.

### 2. Tábua de Marés
```http
GET /tabua_mares?porto=recife&mes=1
```
Gera tábua de marés para porto específico em determinado mês.

### 3. Alertas de Alagamento
```http
GET /alertas_alagamento?cidade=Recife
# ou
GET /alertas_alagamento?lat=-8.03&lon=-34.52
```
Analisa risco de alagamento baseado em dados meteorológicos e de marés.

## 🌊 Portos Disponíveis

A aplicação suporta **56 portos** distribuídos por todo o litoral brasileiro:

- **Norte**: Amapá (3), Pará (6)
- **Nordeste**: Maranhão (4), Piauí (1), Ceará (2), RN (4), Paraíba (1), Pernambuco (2), Alagoas (1), Sergipe (2), Bahia (4)
- **Sudeste**: Espírito Santo (4), Rio de Janeiro (6), São Paulo (2)
- **Sul**: Paraná (4), Santa Catarina (4), Rio Grande do Sul (1)
- **Especial**: Antártica (1)

## 📊 Dados das Marés

- **Fonte**: Dados oficiais brasileiros para 2025
- **Cobertura**: 365 dias do ano
- **Precisão**: Horários e alturas exatas
- **Formato**: JSON estruturado
- **Sem dados simulados**: 100% dados reais

## 🎨 Interface

- **Design Responsivo**: Funciona em desktop e mobile
- **Tema Moderno**: Gradientes e animações suaves
- **Acessibilidade**: Cores contrastantes e navegação intuitiva
- **Performance**: Carregamento rápido e interações fluidas

## 🔍 Funcionalidades Existentes (Mantidas)

- ✅ Consulta de clima por cidade
- ✅ Mapa interativo com clique
- ✅ Dados meteorológicos completos
- ✅ Informações de marés para cidades litorâneas
- ✅ Interface responsiva

## 🆘 Suporte

Se encontrar algum problema:

1. Verifique se todos os arquivos estão no lugar correto
2. Confirme que a API key do OpenWeatherMap está configurada
3. Certifique-se que as dependências estão instaladas
4. Verifique se o arquivo `banco_mareas.json` está presente

## 📝 Changelog

### Versão 2.0 (Nova)
- ➕ Tábua de marés mensal com gráfico interativo
- ➕ Sistema de alertas de alagamento
- ➕ Seleção de portos por dropdown
- ➕ 3 novas APIs REST
- ➕ Interface modernizada
- ➕ Análise de risco meteorológico

### Versão 1.0 (Original)
- ✅ Consulta de clima
- ✅ Mapa interativo
- ✅ Dados de marés básicos

---

