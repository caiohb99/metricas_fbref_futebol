"""FBref scraper functions using undetected-chromedriver to bypass Cloudflare."""
from typing import List, Tuple
import re
import time
import undetected_chromedriver as uc
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import pandas as pd

# Feature lists (kept from the notebook)
stats = ["player","nationality","position","team","age","birth_year","games","games_starts","minutes","goals","assists","pens_made","pens_att","cards_yellow","cards_red","goals_per90","assists_per90","goals_assists_per90","goals_pens_per90","goals_assists_pens_per90","xg","npxg","xg_assists","xg_per90","xg_assists_per90","xg_xg_assists_per90","npxg_per90","npxg_xg_assists_per90"]
stats3 = ["players_used","possession","games","games_starts","minutes","goals","assists","pens_made","pens_att","cards_yellow","cards_red","goals_per90","assists_per90","goals_assists_per90","goals_pens_per90","goals_assists_pens_per90","xg","npxg","xg_assists","xg_per90","xg_assists_per90","xg_xg_assists_per90","npxg_per90","npxg_xg_assists_per90"]

keepers = ["player","nationality","position","team","age","birth_year","gk_games","gk_games_starts","gk_minutes","gk_goals_against","gk_goals_against_per90","gk_shots_on_target_against","gk_saves","gk_save_pct","gk_wins","gk_draws","gk_losses","gk_clean_sheets","gk_clean_sheets_pct","gk_pens_att","gk_pens_allowed","gk_pens_saved","gk_pens_missed"]
keepers3 = ["players_used","gk_games","gk_games_starts","gk_minutes","gk_goals_against","gk_goals_against_per90","gk_shots_on_target_against","gk_saves","gk_save_pct","gk_wins","gk_draws","gk_losses","gk_clean_sheets","gk_clean_sheets_pct","gk_pens_att","gk_pens_allowed","gk_pens_saved","gk_pens_missed"]

# Lista correta para Goleiros Avançado (Players)
keepersadv_player = ["player","nationality","position","team","age","birth_year","minutes_90s","gk_goals_against","gk_pens_allowed","gk_pens_saved","gk_pens_missed","gk_free_kick_goals_against","gk_corner_kick_goals_against","gk_own_goals_against","gk_psxg","gk_psxg_net","gk_psxg_net_per90","gk_passes_completed_launched","gk_passes_launched","gk_passes_pct_launched","gk_passes","gk_passes_throws","gk_pct_passes_launched","gk_passes_length_avg","gk_goal_kicks","gk_pct_goal_kicks_launched","gk_goal_kick_length_avg","gk_crosses","gk_crosses_stopped","gk_crosses_stopped_pct","gk_def_actions_outside_pen_area","gk_def_actions_outside_pen_area_per90","gk_avg_distance_def_actions"]

shooting2 = ["minutes_90s","goals","pens_made","pens_att","shots_total","shots_on_target","shots_free_kicks","shots_on_target_pct","shots_total_per90","shots_on_target_per90","goals_per_shot","goals_per_shot_on_target","xg","npxg","npxg_per_shot","xg_net","npxg_net"]
passing2 = ["passes_completed","passes","passes_pct","passes_total_distance","passes_progressive_distance","passes_completed_short","passes_short","passes_pct_short","passes_completed_medium","passes_medium","passes_pct_medium","passes_completed_long","passes_long","passes_pct_long","assists","xg_assists","xg_assists_net","assisted_shots","passes_into_final_third","passes_into_penalty_area","crosses_into_penalty_area","progressive_passes"]
passing_types2 = ["passes","passes_live","passes_dead","passes_free_kicks","through_balls","passes_pressure","passes_switches","crosses","corner_kicks","corner_kicks_in","corner_kicks_out","corner_kicks_straight","passes_ground","passes_low","passes_high","passes_left_foot","passes_right_foot","passes_head","throw_ins","passes_other_body","passes_completed","passes_offsides","passes_oob","passes_intercepted","passes_blocked"]
gca2 = ["sca","sca_per90","sca_passes_live","sca_passes_dead","sca_dribbles","sca_shots","sca_fouled","gca","gca_per90","gca_passes_live","gca_passes_dead","gca_dribbles","gca_shots","gca_fouled","gca_defense"]
defense2 = ["tackles","tackles_won","tackles_def_3rd","tackles_mid_3rd","tackles_att_3rd","dribble_tackles","dribbles_vs","dribble_tackles_pct","dribbled_past","blocks","blocked_shots","blocked_shots_saves","blocked_passes","interceptions","clearances","errors"]
possession2 = ["touches","touches_def_pen_area","touches_def_3rd","touches_mid_3rd","touches_att_3rd","touches_att_pen_area","touches_live_ball","dribbles_completed","dribbles","dribbles_completed_pct","players_dribbled_past","nutmegs","carries","carry_distance","carry_progressive_distance","progressive_carries","carries_into_final_third","carries_into_penalty_area","pass_targets","passes_received","passes_received_pct","miscontrols","dispossessed"]
misc2 = ["cards_yellow","cards_red","cards_yellow_red","fouls","fouled","offsides","crosses","interceptions","tackles_won","pens_won","pens_conceded","own_goals","ball_recoveries","aerials_won","aerials_lost","aerials_won_pct"]

def _get_driver():
    """Create and return an undetected ChromeDriver instance to bypass Cloudflare."""
    def _create_options():
        options = uc.ChromeOptions()
        options.add_argument('--no-sandbox')
        options.add_argument('--disable-dev-shm-usage')
        options.add_argument('--window-size=1920,1080')
        options.add_argument('--disable-blink-features=AutomationControlled')
        return options

    try:
        # Tenta inicialização padrão usando subprocesso (mais estável no Windows)
        return uc.Chrome(options=_create_options(), use_subprocess=True)
    except Exception as e:
        err_msg = str(e)
        # Se houver erro de versão, extraímos a versão correta e tentamos novamente
        if "browser version is" in err_msg.lower():
            match = re.search(r"browser version is ([\d.]+)", err_msg)
            if match:
                major_version = int(match.group(1).split('.')[0])
                print(f"  ⚠ Versão do Chrome ({major_version}) detectada. Sincronizando driver compatível...")
                return uc.Chrome(options=_create_options(), version_main=major_version, use_subprocess=True)
        raise e

def _clean_text(cell) -> str:
    if cell is None:
        return ''
    return cell.get_text(strip=True)

def _to_number(text: str):
    if text is None or text == '':
        return 0.0
    try:
        return float(text.replace(',',''))
    except ValueError:
        return 0.0

def get_tables(url: str, text: str, driver=None) -> Tuple[BeautifulSoup, BeautifulSoup]:
    """Fetch URL using undetected-chromedriver and return parsed tables."""
    managed_driver = False
    if driver is None:
        driver = _get_driver()
        managed_driver = True
        
    print(f"  Carregando {url}...")
    try:
        driver.get(url)
        
        # Espera mínima inicial
        time.sleep(1.5)
        
        # Espera até que pelo menos uma tabela ou o footer apareça
        WebDriverWait(driver, 15).until(EC.presence_of_element_located((By.ID, 'footer')))
        
        # Scroll parcial costuma ser suficiente para carregar os scripts de tabela
        driver.execute_script("window.scrollTo(0, 1000);")
        driver.execute_script("window.scrollTo(0, 0);")
        
        html = driver.page_source
    except Exception as e:
        print(f"    ⚠ Erro ao carregar: {e}")
        html = driver.page_source
    finally:
        if managed_driver:
            driver.quit()
    
    comm = re.compile(r"<!--|-->")
    soup = BeautifulSoup(comm.sub('', html), 'lxml')
    all_tables = soup.find_all('tbody')

    # Se não encontrar nenhuma tabela, o Cloudflare provavelmente bloqueou a requisição
    if not all_tables:
        print("\n" + "!"*60)
        print("  ⚠ CAPTCHA OU BLOQUEIO DETECTADO!")
        print("  Por favor, resolva o CAPTCHA/desafio no navegador que abriu.")
        print("  Certifique-se de que a tabela apareceu na tela.")
        print("  Assim que as tabelas aparecerem, pressione ENTER aqui no terminal.")
        print("!"*60 + "\n")
        input("Aguardando resolução... Pressione ENTER para continuar.")
        time.sleep(2) # Pequena pausa para garantir que o DOM atualizou
        # Tenta capturar o conteúdo novamente após a interação humana
        html = driver.page_source
        soup = BeautifulSoup(comm.sub('', html), 'lxml')
        all_tables = soup.find_all('tbody')

    if not all_tables:
        # Tenta uma última vez recarregar o HTML caso o Selenium tenha falhado
        time.sleep(1)
        html = driver.page_source
        soup = BeautifulSoup(comm.sub('', html), 'lxml')
        all_tables = soup.find_all('tbody')

    # Estratégia de localização de tabelas mais robusta
    player_table = None
    team_table = None
    team_vs_table = None

    # 1. Tenta por IDs conhecidos que variam por categoria
    # Procura tabelas que contenham 'squads' ou 'team' no ID
    t_for = soup.find('table', id=lambda x: x and 'squads' in x and 'for' in x)
    if not t_for:
        t_for = soup.find('table', id=lambda x: x and 'stats_team' in x and 'for' in x)
        
    if t_for: team_table = t_for.find('tbody')
    
    t_vs = soup.find('table', id=lambda x: x and 'squads' in x and ('against' in x or 'vs' in x))
    if not t_vs:
        t_vs = soup.find('table', id=lambda x: x and 'stats_team' in x and ('against' in x or 'vs' in x))
        
    if t_vs: team_vs_table = t_vs.find('tbody')

    # 2. Busca tabela de jogadores (procurando pela coluna 'player' no cabeçalho)
    stat_tables = soup.find_all('table', class_='stats_table')
    for table in stat_tables:
        header = table.find('thead')
        if header and header.find(['th', 'td'], {"data-stat": ["player", "player_name"]}):
            player_table = table.find('tbody')
            break

    # 3. Fallbacks finais se a busca estruturada falhar
    if not team_table and all_tables:
        team_table = all_tables[0]
    if not player_table and len(all_tables) > 2:
        player_table = all_tables[2]
    elif not player_table and all_tables:
        # Em Copas, a tabela de jogadores costuma ser maior. 
        # Vamos pegar a que tiver mais linhas como fallback.
        player_table = max(all_tables, key=lambda x: len(x.find_all('tr')))

    if text == 'for':
        return player_table, (team_table or player_table if player_table else None)
    if text == 'vs':
        return player_table, (team_vs_table or player_table if player_table else None)
    return player_table, (team_table or player_table if player_table else None)

def get_frame(features: List[str], player_table) -> pd.DataFrame:
    if player_table is None:
        return pd.DataFrame()
    # Garante que as chaves de identificação sempre existam para o merge
    keys = ['player', 'nationality', 'position', 'team', 'age', 'birth_year']
    all_fields = list(dict.fromkeys(keys + features))
    pre_df = {f: [] for f in all_fields}
    rows = player_table.find_all('tr')
    for row in rows:
        # Filtro robusto para o novo site: ignora cabeçalhos e separadores
        if row.get('class') and any(c in row.get('class') for c in ['thead', 'spacer', 'over_header']):
            continue
        
        # FBref pode usar 'player' ou 'player_name'
        player_cell = row.find(['th', 'td'], {"data-stat": ["player", "player_name"]})
        player_name = _clean_text(player_cell)
        
        if not player_name or player_name.lower() == "player":
            continue
            
        squad_cell = row.find(['th', 'td'], {"data-stat": ["team", "squad", "team_name"]})
        squad_name = _clean_text(squad_cell)

        for f in all_fields:
            if f == 'player':
                pre_df[f].append(player_name)
                continue
            if f in ['squad', 'team']:
                pre_df[f].append(squad_name)
                continue

            # Procura por data-stat original ou variações
            cell = row.find(['td', 'th'], {"data-stat": f})
            text = _clean_text(cell)
            if text == '' and f not in keys:
                text = '0'
            
            if f not in keys:
                val = _to_number(text)
            else:
                val = text
            pre_df[f].append(val)
    print(f"    → Processados {len(pre_df[features[0]])} registros.")
    return pd.DataFrame(pre_df)

def get_frame_team(features: List[str], team_table) -> pd.DataFrame:
    pre_df = {"squad": []}
    for f in features:
        if f != "squad": pre_df.setdefault(f, [])
    
    if team_table is None:
        return pd.DataFrame(pre_df)

    rows = team_table.find_all('tr')
    for row in rows:
        # No novo layout, o nome do time está em 'team', 'squad' ou 'team_name'
        squad_cell = row.find(['th', 'td'], {"data-stat": ["team", "squad", "team_name"]})
        squad_name = _clean_text(squad_cell)
        
        if not squad_name or squad_name.lower() in ["squad", "team", "team_name", ""]:
            continue

        pre_df['squad'].append(squad_name)
        for f in pre_df.keys():
            if f == 'squad': continue
            # Alguns campos de time usam prefixo 'team_'
            cell = row.find(['td', 'th'], {"data-stat": f}) or row.find(['td', 'th'], {"data-stat": f"team_{f}"})
            text = _clean_text(cell)
            if text == '':
                text = '0'
            if f not in ['player','nationality','position','squad','age','birth_year']:
                val = _to_number(text)
            else:
                val = text
            pre_df[f].append(val)
    return pd.DataFrame(pre_df)

def frame_for_category(category: str, top: str, end: str, features: List[str], driver=None) -> pd.DataFrame:
    url = top + category + end
    player_table, _ = get_tables(url, 'for', driver=driver)
    if player_table is None:
        return pd.DataFrame()
    return get_frame(features, player_table)

def frame_for_category_team(category: str, top: str, end: str, features: List[str], text: str, driver=None) -> pd.DataFrame:
    url = top + category + end
    player_table, team_table = get_tables(url, text, driver=driver)
    if team_table is None:
        return pd.DataFrame()
    return get_frame_team(features, team_table)

def _merge_dataframes(dfs: List[pd.DataFrame]) -> pd.DataFrame:
    """Une múltiplos DataFrames garantindo que os jogadores estejam alinhados."""
    if not dfs:
        return pd.DataFrame()
    
    # Colunas usadas como chave para o merge
    keys = ['player', 'nationality', 'position', 'team', 'age', 'birth_year']
    
    final_df = dfs[0]
    for i in range(1, len(dfs)):
        # Verifica quais chaves estão presentes em ambos
        common_keys = [k for k in keys if k in final_df.columns and k in dfs[i].columns]
        
        # Remove colunas duplicadas do DataFrame da direita antes do merge (exceto as chaves)
        cols_to_use = dfs[i].columns.difference(final_df.columns.difference(common_keys))
        
        final_df = pd.merge(final_df, dfs[i][cols_to_use], on=common_keys, how='outer')
    
    return final_df.fillna(0)

def get_outfield_data(top: str, end: str) -> pd.DataFrame:
    driver = _get_driver()
    try:
        categories = [
            ('stats', stats), ('shooting', shooting2), ('passing', passing2),
            ('passing_types', passing_types2), ('gca', gca2), ('defense', defense2),
            ('possession', possession2), ('misc', misc2)
        ]
        dfs = []
        for cat, feat in categories:
            try:
                df_cat = frame_for_category(cat, top, end, feat, driver)
                if not df_cat.empty:
                    dfs.append(df_cat)
            except Exception:
                pass
        
        return _merge_dataframes(dfs)
    finally:
        driver.quit()

def get_keeper_data(top: str, end: str) -> pd.DataFrame:
    driver = _get_driver()
    try:
        dfs = [
        ]
        for cat, feat in [('keepers', keepers), ('keepersadv', keepersadv_player)]:
            try:
                df_cat = frame_for_category(cat, top, end, feat, driver)
                if not df_cat.empty:
                    dfs.append(df_cat)
            except Exception:
                pass
                
        return _merge_dataframes(dfs)
    finally:
        driver.quit()

def get_team_data(top: str, end: str, text: str) -> pd.DataFrame:
    driver = _get_driver()
    try:
        categories = [
            ('stats', stats3), ('keepers', keepers3), ('keepersadv', keepers3),
            ('shooting', shooting2), ('passing', passing2), ('passing_types', passing_types2),
            ('gca', gca2), ('defense', defense2), ('possession', possession2), ('misc', misc2)
        ]
        dfs = []
        for cat, feat in categories:
            df_cat = frame_for_category_team(cat, top, end, feat, text, driver)
            if not df_cat.empty:
                dfs.append(df_cat)
        
        if not dfs: return pd.DataFrame()

        final_df = dfs[0]
        # Para times, a chave única é 'squad'
        for i in range(1, len(dfs)):
            cols_to_use = dfs[i].columns.difference(final_df.columns.difference(['squad']))
            final_df = pd.merge(final_df, dfs[i][cols_to_use], on='squad', how='outer')
        return final_df.fillna(0)
    finally:
        driver.quit()

if __name__ == "__main__":
    print("This module provides functions for scraping FBref pages. Use the CLI script.")
