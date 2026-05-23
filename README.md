# Scrape FBref Data - Brazilian Teams

Este pacote realiza o web scraping automatizado de estatísticas avançadas (Shooting, Passing, Defense, etc.) do [FBref.com](https://fbref.com). Ele foi projetado para analistas de desempenho e entusiastas de dados que precisam de estatísticas de ligas brasileiras e competições da CONMEBOL integradas em um banco de dados **SQL Server**.

## 🚀 Funcionalidades Principais
- **Persistência em SQL Server**: Utiliza `SQLAlchemy` com `fast_executemany` para inserção de alta performance.
- **Suporte a Dados Históricos**: Permite extrair dados de temporadas anteriores (ex: 2022, 2023) através do parâmetro `--year`.
- **Controle de Ligas Ativas**: Dicionário centralizado no código para ativar/desativar competições específicas no processamento em lote.
- **Resiliência a Bloqueios**: Implementação com `undetected-chromedriver` e sistema de pausa inteligente para resolução manual de CAPTCHAs.
- **Auditoria de Dados**: Colunas automáticas `scraped_at`, `data_execucao` e `ano_competicao` em todas as tabelas.

## 📋 Requisitos e Instalação

### 1. Requisitos de Sistema
- **Python 3.8+**
- **Google Chrome** atualizado.
- **Microsoft ODBC Driver 17 for SQL Server** (para persistência no banco).

### 2. Configuração do Ambiente
```bash
git clone <seu-repositorio>
cd metricas_fbref_futebol
pip install -r requirements.txt
```

Você também precisa ter **Chrome** ou **Chromium** instalado no seu sistema, pois o scraper usa Selenium.

## Uso

### Script para baixar todos os campeonatos brasileiros

Para baixar dados de todos os times brasileiros de todos os campeonatos:

```bash
python scrape_brazilian_leagues.py
```

Dados serão salvos em `dados_brasileiros/` organizado por campeonato.

### Opções

**Listar campeonatos disponíveis:**
```bash
python scrape_brazilian_leagues.py --list
```

**Baixar um campeonato específico:**
```bash
python scrape_brazilian_leagues.py --league serie-a
```

**Baixar apenas um tipo de dado (ex: apenas jogadores outfield):**
```bash
python scrape_brazilian_leagues.py --league serie-a --mode outfield
```

Opções de `--mode`:
- `all` (padrão) - todos os dados (outfield + keepers + teams)
- `outfield` - apenas jogadores de linha
- `keepers` - apenas goleiros
- `team-for` - estatísticas dos times (offensiva)
- `team-vs` - estatísticas dos times (defesa)

### CLI genérica para qualquer competição

Para fazer scraping de qualquer competição no FBref:

```bash
python cli.py --top "https://fbref.com/en/comps/9/" --end "/Premier-League-Stats" --mode outfield --output resultado.csv
```

## Campeonatos Brasileiros Disponíveis

- `serie-a` - Série A
- `serie-b` - Série B  
- `libertadores` - Copa Libertadores
- `sul-americana` - Copa Sul-Americana

## Estrutura de Dados

Cada arquivo CSV contém:

### outfield.csv
- Dados de jogadores de linha (estatísticas ofensivas, defesas, passes, etc)
- Inclui: goals, assists, xG, passes, tackles, etc

### keepers.csv
- Dados de goleiros
- Inclui: saves, save%, goals against, passes launched, etc

### teams_for.csv
- Estatísticas dos times (o que fazem em ataque)
- Inclui: goals, possession, xG, passes, tackles, etc

### teams_vs.csv
- Estatísticas dos times (o que sofrem em defesa)
- Inclui: goals against, shots on target against, etc

## Tempo de Execução

Cada campeonato leva ~5-10 minutos para fazer scraping completo (depende de sua conexão).

## Solução de Problemas

### "403 Forbidden" error
Se receber erro 403, FBref está bloqueando. O Selenium (navegador real) deve contornar isso.

### ChromeDriver issues
Se o Selenium não encontrar o ChromeDriver, instale o chromedriver:
```bash
pip install chromedriver-binary
```

### Erro de "Nome de coluna inválido" no SQL Server
Isso acontece quando você atualiza o script e ele tenta enviar novas colunas para uma tabela antiga no banco. 
Para resolver, rode o script uma vez com o comando `--reset`:
```bash
python main.py --reset
```
**Atenção:** Isso apagará os dados atuais das tabelas para recriá-las com a estrutura correta.

## Dados Cortesia

Todos os dados são cortesia de **StatsBomb** via **FBref**.
