# CliMar - Aplicativo de Clima e Marés

## Resumo das Alterações Implementadas

## Como Executar o Aplicativo

### Pré-requisitos
- Python 3.11+
- Flask
- Requests
- Outras dependências listadas no código

### Passos para Execução

1. **Navegue até o diretório do projeto:**
   ```bash
   cd weather-cloud
   ```

2. **Execute o aplicativo Flask:**
   ```bash
   python app.py
   ```

3. **Acesse no navegador:**
   ```
   http://localhost:5000/
   ```

### Funcionalidades Disponíveis

#### Aba Clima
- Busca por cidade ou clique no mapa
- Exibição de dados meteorológicos completos
- Dados de maré para cidades litorâneas
- **NOVO:** Alertas de alagamento baseados em análise de risco

#### Aba Marés
- Consulta específica de marés por porto e data
- Interface de pergunta em linguagem natural
- Visualização de marés altas e baixas por dia

#### Aba Tábua por Mês (NOVA)
- Busca por cidade ou clique no mapa
- Gráfico interativo com dados mensais de maré usando Chart.js
- Exibição de dados de maré alta e baixa por mês
- Interface responsiva e intuitiva
- Mapa funcional com clique para seleção de localização
- Campo de digitação para busca por cidade


### Sistema de Alertas de Alagamento
- ✅ Análise cruzada de dados climáticos e de maré
- ✅ Três níveis de alerta: Baixo, Médio e Alto
- ✅ Exibição visual dos alertas na aba "Clima"
- ✅ Critérios baseados em chuva, maré alta crítica e combinação de fatores


## Detalhes Técnicos das Implementações

### Backend (app.py)
- **Nova rota `/tabua_mes`:** Processa dados de maré mensais
- **Nova rota `/alertas_alagamento`:** Analisa risco de alagamento
- **Função `analisar_risco_alagamento`:** Cruza dados climáticos e de maré

### Frontend (templates/index.html)
- **Páginas:** Interface completa para tábua mensal
- **Gráfico Chart.js:** Visualização interativa de dados
- **Sistema de alertas:** Exibição visual com cores e ícones


### Critérios de Alerta de Alagamento

#### Risco Baixo
- Condições climáticas e de maré favoráveis
- Sem chuva significativa e maré normal

#### Risco Médio
- Presença de chuva OU maré alta crítica (>3.0m)
- Possibilidade de alagamentos localizados

#### Risco Alto
- Combinação de chuva intensa E maré alta crítica
- Alto potencial para alagamentos severos

## Estrutura dos Dados

### Resposta da API `/tabua_mes`
```json
{
  "cidade": "Nome da Cidade",
  "pais": "BR",
  "latitude": -3.7319,
  "longitude": -38.5267,
  "mes_extenso": "Junho",
  "ano": 2025,
  "mares_mensais": [
    {
      "dia": 1,
      "altura_max_alta": 2.5,
      "altura_min_baixa": 0.3
    }
  ]
}
```

### Resposta da API `/alertas_alagamento`
```json
{
  "nivel": "baixo|medio|alto",
  "alertas": [
    "Mensagem de alerta específica"
  ]
}
```

## Observações Importantes

1. **API Key:** Certifique-se de que a variável `API_KEY` está configurada com uma chave válida da OpenWeatherMap
2. **Dados de Maré:** O sistema utiliza o arquivo `banco_mareas.json` para dados de referência
3. **Responsividade:** A interface é totalmente responsiva e funciona em dispositivos móveis
4. **Performance:** Os mapas são carregados de forma independente para evitar conflitos

## Melhorias Futuras Sugeridas

- Integração com APIs de maré em tempo real
- Histórico de alertas de alagamento
- Notificações push para alertas críticos
- Exportação de dados em PDF/CSV
- Previsões de maré estendidas



## 5. Tecnologias e Infraestrutura

A aplicação CliMar é construída com um conjunto de tecnologias modernas e é implantada em uma infraestrutura de nuvem robusta para garantir desempenho e escalabilidade.

### 5.1. Tecnologias Principais

- **Backend:** Python 3 com Flask (microframework web).
- **Frontend:** HTML5, CSS3, JavaScript, Leaflet.js (mapas interativos), Chart.js (gráficos).
- **Banco de Dados (simplificado):** Arquivo JSON (`banco_mareas.json`) para dados de maré estáticos.

### 5.2. Infraestrutura de Nuvem

A aplicação está hospedada na plataforma **Railway**, que oferece um ambiente de implantação contínua e escalável. Para gerenciamento de dados em memória e potencial cache, é utilizado o **Redis**.

- **Railway:** Plataforma de desenvolvimento e implantação que simplifica o processo de colocar aplicações em produção, oferecendo implantação contínua, ambientes isolados e escalabilidade.
- **Redis:** Armazenamento de estrutura de dados em memória, utilizado para cache de dados e outras operações que exigem alta velocidade.

## 6. Testes e Integração Contínua (CI/CD)

A qualidade do código e a agilidade na entrega são garantidas através de testes automatizados e um pipeline de Integração Contínua/Entrega Contínua (CI/CD) configurado no Git.

### 6.1. Testes Automatizados

- **Pytest:** Framework de testes para Python, utilizado para testes unitários e de integração do backend.
- **Bandit:** Ferramenta de segurança estática para Python, utilizada para identificar vulnerabilidades no código-fonte.

### 6.2. CI/CD no Git

O workflow de CI/CD (provavelmente configurado via GitHub Actions, dado o repositório) automatiza as seguintes etapas:

- **Build:** Preparação do ambiente de execução.
- **Testes:** Execução automática dos testes Pytest e Bandit a cada push ou pull request.
- **Deploy:** Implantação automática da aplicação no Railway após a aprovação dos testes.



