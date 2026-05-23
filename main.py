import argparse
from scrape_brazilian_leagues import run_pipeline, BRAZILIAN_LEAGUES

def main():
    """Função principal para execução via CLI ou botão Play do VS Code."""
    parser = argparse.ArgumentParser(
        description="Interface de execução para o Scraper FBref - Gol Raiz FC"
    )
    parser.add_argument(
        '--league',
        choices=list(BRAZILIAN_LEAGUES.keys()),
        help="Campeonato específico a fazer scraping (padrão: todos)"
    )
    parser.add_argument(
        '--year',
        type=int,
        default=None,
        help="Ano da competição (ex: 2023). Se omitido, busca a temporada atual."
    )
    parser.add_argument(
        '--mode',
        choices=['all', 'outfield', 'keepers', 'team-for', 'team-vs'],
        default='all',
        help="Tipo de dados a fazer scraping (padrão: todos)"
    )
    parser.add_argument(
        '--list',
        action='store_true',
        help="Lista campeonatos disponíveis"
    )
    parser.add_argument(
        '--db', 
        action='store_true', 
        default=True,
        help="Habilita persistência no SQL Server local (Banco: futebol)"
    )
    
    args = parser.parse_args()
    
    if args.list:
        print("Campeonatos disponíveis para o Gol Raiz FC:")
        for key, league in BRAZILIAN_LEAGUES.items():
            print(f"  {key:20} - {league['name']}")
        return

    # Inicia o pipeline de dados
    run_pipeline(league_to_run=args.league, year=args.year, mode=args.mode, to_db=args.db)
    
    print("\n" + "="*60)
    print("✓ PIPELINE DE DADOS CONCLUÍDO!")
    print("Os dados foram inseridos diretamente no banco 'futebol'.")
    input("\nPressione ENTER para fechar esta janela...")

if __name__ == "__main__":
    main()