"""
Script para fazer scraping de todos os times brasileiros em vários campeonatos.
Define URLs de campeonatos brasileiros e permite scraping em lote.
"""
import os
import pandas as pd
import sqlalchemy as sa
from datetime import datetime
from scrape_fbref import scraper
import urllib

# Campeonatos brasileiros disponíveis no FBref
BRAZILIAN_LEAGUES = {
    "serie-a": {
        "top": "https://fbref.com/en/comps/24",
        "end": "Serie-A-Stats",
        "name": "Série A"
    },
    "serie-b": {
        "top": "https://fbref.com/en/comps/38",
        "end": "Serie-B-Stats",
        "name": "Série B"
    },
    "copa-do-brasil": {
        "top": "https://fbref.com/en/comps/273",
        "end": "Copa-do-Brasil-Stats",
        "name": "Copa do Brasil"
    },
    "libertadores": {
        "top": "https://fbref.com/en/comps/14",
        "end": "Copa-Libertadores-Stats",
        "name": "Copa Libertadores"
    },
    "sul-americana": {
        "top": "https://fbref.com/en/comps/32",
        "end": "Copa-Sudamericana-Stats",
        "name": "Copa Sul-Americana"
    }
}

def get_db_engine(database="futebol"):
    """Configura a conexão com o SQL Server Local."""
    conn_str = (
        "DRIVER={ODBC Driver 17 for SQL Server};"
        "SERVER=localhost\\SQLEXPRESS;"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )
    params = urllib.parse.quote_plus(conn_str)
    # fast_executemany: Melhora brutalmente a velocidade de inserção no SQL Server
    engine = sa.create_engine(f"mssql+pyodbc:///?odbc_connect={params}", fast_executemany=True)
    return engine

def setup_db():
    """Garante que o banco de dados e as tabelas básicas existam."""
    # 1. Verifica/Cria o Banco de Dados conectando no master
    engine_master = get_db_engine("master")
    with engine_master.connect() as conn:
        conn.execution_options(isolation_level="AUTOCOMMIT")
        db_exists = conn.execute(sa.text("SELECT name FROM sys.databases WHERE name = 'futebol'")).fetchone()
        if not db_exists:
            print("  → Banco 'futebol' não encontrado. Criando...")
            conn.execute(sa.text("CREATE DATABASE futebol"))
    
    return get_db_engine("futebol")

def get_sql_types(df):
    """Define tipos de dados otimizados para evitar NVARCHAR(MAX)."""
    dtypes = {}
    for col in df.columns:
        if df[col].dtype == 'object':
            dtypes[col] = sa.types.NVARCHAR(length=255)
        elif 'scraped_at' in col:
            dtypes[col] = sa.types.DateTime()
        elif 'data_execucao' in col:
            dtypes[col] = sa.types.Date()
        elif 'ano_competicao' in col:
            dtypes[col] = sa.types.Integer()
        # O Pandas/SQLAlchemy já mapeia float64 e int64 para FLOAT e INT corretamente
    return dtypes

def scrape_league(league_key: str, year: int = None, mode: str = "all", engine=None) -> dict:
    """
    Faz scraping de um campeonato específico.
    
    Args:
        league_key: chave do campeonato (ex: 'serie-a')
        year: ano da competição (ex: 2023). Se None, pega a temporada atual.
        mode: 'all' (outfield+keepers+team), 'outfield', 'keepers', 'team-for', 'team-vs'
        engine: Engine SQLAlchemy para inserção imediata no banco.
    Retorna um dicionário de DataFrames com metadados injetados.
    """
    if league_key not in BRAZILIAN_LEAGUES:
        print(f"Campeonato '{league_key}' não encontrado.")
        print(f"Disponíveis: {', '.join(BRAZILIAN_LEAGUES.keys())}")
        return {}
    
    league = BRAZILIAN_LEAGUES[league_key]
    league_name = league["name"]
    base_top = league["top"]
    base_end = league["end"]
    scraped_at = datetime.now()
    data_execucao = scraped_at.date()
    effective_year = year if year else scraped_at.year

    # Ajusta URLs para competições passadas
    if year:
        # Formato histórico: .../comps/ID/2023/2023-Serie-A-Stats
        top = f"{base_top}/{year}/"
        end = f"/{year}-{base_end}"
    else:
        # Formato atual: .../comps/ID/Serie-A-Stats
        top = f"{base_top}/"
        end = f"/{base_end}"
    
    print(f"\n{'='*60}")
    print(f"Scraping: {league_name}")
    print(f"{'='*60}\n")
    
    results = {}
    try:
        if mode in ["all", "outfield"]:
            print("  → Fazendo scraping de jogadores outfield...")
            df = scraper.get_outfield_data(top, end)
            df.insert(0, 'ano_competicao', effective_year)
            df.insert(1, 'data_execucao', data_execucao)
            df.insert(2, 'league', league_name)
            df['scraped_at'] = scraped_at
            
            if engine:
                print(f"    → [SQL] Inserindo players_outfield ({league_key})...")
                # Garante que não existam colunas duplicadas ou sufixos bizarros
                df = df.loc[:, ~df.columns.duplicated()]
                df.to_sql('players_outfield', engine, if_exists='append', index=False, dtype=get_sql_types(df))
            
            results['players_outfield'] = df
        
        if mode in ["all", "keepers"]:
            print("  → Fazendo scraping de goleiros...")
            df = scraper.get_keeper_data(top, end)
            df.insert(0, 'ano_competicao', effective_year)
            df.insert(1, 'data_execucao', data_execucao)
            df.insert(2, 'league', league_name)
            df['scraped_at'] = scraped_at
            
            if engine:
                print(f"    → [SQL] Inserindo players_keepers ({league_key})...")
                df = df.loc[:, ~df.columns.duplicated()]
                df.to_sql('players_keepers', engine, if_exists='append', index=False, dtype=get_sql_types(df))
            
            results['players_keepers'] = df
        
        if mode in ["all", "team-for"]:
            print("  → Fazendo scraping de estatísticas dos times (FOR)...")
            df = scraper.get_team_data(top, end, 'for')
            df.insert(0, 'ano_competicao', effective_year)
            df.insert(1, 'data_execucao', data_execucao)
            df.insert(2, 'league', league_name)
            df['scraped_at'] = scraped_at
            
            if engine:
                print(f"    → [SQL] Inserindo teams_stats_for no banco...")
                df.to_sql('teams_stats_for', engine, if_exists='append', index=False, dtype=get_sql_types(df))
            
            results['teams_stats_for'] = df
        
        if mode in ["all", "team-vs"]:
            print("  → Fazendo scraping de estatísticas dos times (VS)...")
            df = scraper.get_team_data(top, end, 'vs')
            df.insert(0, 'ano_competicao', effective_year)
            df.insert(1, 'data_execucao', data_execucao)
            df.insert(2, 'league', league_name)
            df['scraped_at'] = scraped_at
            
            if engine:
                print(f"    → [SQL] Inserindo teams_stats_vs no banco...")
                df.to_sql('teams_stats_vs', engine, if_exists='append', index=False, dtype=get_sql_types(df))
            
            results['teams_stats_vs'] = df

        return results

    except Exception as e:
        print(f"  ✗ Erro: {e}")
        return {}
def run_pipeline(league_to_run=None, year=None, mode="all", to_db=False):
    """Executa o pipeline, consolida e opcionalmente persiste no banco."""
    leagues = [league_to_run] if league_to_run else BRAZILIAN_LEAGUES.keys()
    
    engine = setup_db() if to_db else None

    for l_key in leagues:
        scrape_league(l_key, year=year, mode=mode, engine=engine)
def _consolidate_results(master_dfs, to_db):
    """Agrupa os DataFrames e persiste em CSV, Parquet e SQL Server."""
    output_path = Path("dados_brasileiros/consolidado")
    output_path.mkdir(parents=True, exist_ok=True)

    for table_name, df_list in master_dfs.items():
        if not df_list: continue
        
        final_df = pd.concat(df_list, ignore_index=True)
        
        # Persistência em arquivos
        csv_file = output_path / f"{table_name}_master.csv"
        parquet_file = output_path / f"{table_name}_master.parquet"
        final_df.to_csv(csv_file, index=False)
        final_df.to_parquet(parquet_file, index=False)
        print(f"✓ {table_name} consolidado: CSV e Parquet")
