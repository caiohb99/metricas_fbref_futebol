"""Command-line interface for the FBref scraper package."""
import argparse
from scrape_fbref import scraper

def main():
    parser = argparse.ArgumentParser(description='Scrape FBref competition data')
    parser.add_argument('--top', required=True, help='Top part of URL, e.g. https://fbref.com/en/comps/9/')
    parser.add_argument('--end', required=True, help="End part of URL, e.g. /Premier-League-Stats")
    parser.add_argument('--mode', choices=['outfield','keepers','team-for','team-vs'], default='outfield')
    parser.add_argument('--output', default=None, help='Output CSV path')
    args = parser.parse_args()

    top = args.top
    end = args.end
    mode = args.mode
    out = args.output

    if mode == 'outfield':
        df = scraper.get_outfield_data(top, end)
        out = out or 'outfield.csv'
    elif mode == 'keepers':
        df = scraper.get_keeper_data(top, end)
        out = out or 'keepers.csv'
    elif mode == 'team-for':
        df = scraper.get_team_data(top, end, 'for')
        out = out or 'teams_for.csv'
    else:
        df = scraper.get_team_data(top, end, 'vs')
        out = out or 'teams_vs.csv'

    df.to_csv(out, index=False)
    print(f"Saved {len(df)} rows to {out}")

if __name__ == '__main__':
    main()
