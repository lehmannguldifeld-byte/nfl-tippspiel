import streamlit as st
import requests
import json
from datetime import datetime
from zoneinfo import ZoneInfo
import pandas as pd
import numpy as np
import os
import base64
import urllib.parse
import textwrap
import io

# REPORTLAB IMPORTS FÜR REICHHALTIGES 2-SEITEN PDF ZEITUNGSLAYOUT
try:
    from reportlab.lib.pagesizes import A4
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak, HRFlowable
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib import colors
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False

# --- SEITEN-KONFIGURATION ---
st.set_page_config(page_title="NFL Tippspiel 2026/27", page_icon="🏈", layout="wide")

# SLEEPER FANTASY LEAGUE CONFIG
SLEEPER_LEAGUE_ID = "1410923268445114368"

# --- PASSWÖRTER & MITSPIELER LISTE ---
PASSWORDS = {
    "Andy": "andy2026", "Ronny": "ronny2026", "Bauzzen": "bauzzen2026", "Bössi": "boessi2026",
    "Jerome": "jerome2026", "Mäni": "maeni2026", "Domi": "domi2026", "Pädu": "paedu2026"
}
MITSPIELER = list(PASSWORDS.keys())

# --- SESSION STATE LOGIN VERWALTUNG ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None

# --- DYNAMISCHES DESIGN (BÖSSI HIGH-CONTRAST MOBILE MODE VS. STADION DESIGN) ---
active_user_check = st.session_state.get("logged_user")

if active_user_check == "Bössi":
    st.markdown("""<style>
.stApp { background-color: #0f172a !important; background-image: none !important; color: #ffffff !important; }
.main-title { text-align: center; font-size: 3rem; font-weight: 900; color: #38bdf8 !important; text-shadow: none !important; margin-bottom: 10px; }
.leaderboard-card, .game-card-compact, .schedule-card, .host-card, .redzone-card, .chat-bubble, .login-box, .admin-box { background-color: #1e293b !important; border: 2px solid #475569 !important; border-radius: 12px; padding: 16px; margin-bottom: 12px; color: #ffffff !important; box-shadow: none !important; }
.team-name { font-size: 1.05rem !important; font-weight: 900 !important; color: #ffffff !important; }
.score-badge { background-color: #0284c7 !important; color: #ffffff !important; font-weight: 900 !important; }
</style>""", unsafe_allow_html=True)
else:
    st.markdown("""<style>
.stApp {
    background: radial-gradient(circle at 50% -10%, rgba(255, 255, 255, 0.45) 0%, rgba(30, 41, 59, 0.85) 55%, rgba(15, 23, 42, 0.98) 100%),
                url('https://images.unsplash.com/photo-1566577739112-5180d4bf9390?auto=format&fit=crop&w=1920&q=80');
    background-size: cover;
    background-attachment: fixed;
    color: #f8fafc;
}
.main-title {
    text-align: center;
    font-size: 3rem;
    font-weight: 900;
    color: #0284c7;
    text-shadow: 0 0 18px rgba(255, 255, 255, 0.8), 0 0 30px rgba(56, 189, 248, 0.5);
    margin-bottom: 10px;
}
.leaderboard-card {
    background: rgba(30, 41, 59, 0.90);
    border-left: 6px solid #38bdf8;
    border-radius: 12px;
    padding: 16px 24px;
    margin-bottom: 12px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 8px 20px rgba(0, 0, 0, 0.35);
    backdrop-filter: blur(4px);
}
.game-card-compact {
    background-color: rgba(30, 41, 59, 0.88);
    border-radius: 10px;
    padding: 8px 12px;
    border: 1px solid rgba(255, 255, 255, 0.15);
    margin-bottom: 8px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.2);
}
.schedule-card {
    background: linear-gradient(135deg, rgba(30, 41, 59, 0.95) 0%, rgba(15, 23, 42, 0.95) 100%);
    border: 1px solid rgba(56, 189, 248, 0.3);
    border-radius: 16px;
    padding: 16px 20px;
    margin-bottom: 16px;
    box-shadow: 0 8px 25px rgba(0,0,0,0.4);
    backdrop-filter: blur(6px);
}
.host-card {
    background: rgba(30, 41, 59, 0.90);
    border: 1px solid rgba(56, 189, 248, 0.2);
    border-radius: 12px;
    padding: 14px 20px;
    margin-bottom: 10px;
    display: flex;
    justify-content: space-between;
    align-items: center;
    box-shadow: 0 4px 15px rgba(0,0,0,0.3);
}
.host-card-next {
    background: linear-gradient(135deg, rgba(2, 132, 199, 0.4) 0%, rgba(30, 41, 59, 0.95) 100%);
    border: 2px solid #38bdf8;
    box-shadow: 0 0 15px rgba(56, 189, 248, 0.4);
}
.redzone-card {
    background: linear-gradient(135deg, rgba(225, 29, 72, 0.25) 0%, rgba(30, 41, 59, 0.95) 100%);
    border: 2px solid #f43f5e;
    border-radius: 12px;
    padding: 16px;
    margin-bottom: 15px;
    box-shadow: 0 0 15px rgba(244, 63, 94, 0.3);
}
.team-box-left { display: flex; align-items: center; justify-content: flex-end; gap: 6px; }
.team-box-right { display: flex; align-items: center; justify-content: flex-start; gap: 6px; }
.team-name { font-size: 0.95rem; font-weight: 800; color: #f8fafc; }
.score-badge {
    font-size: 1.2rem;
    font-weight: 900;
    color: #38bdf8;
    background: rgba(15, 23, 42, 0.8);
    padding: 4px 10px;
    border-radius: 8px;
    border: 1px solid rgba(255,255,255,0.1);
}
.winner-highlight { color: #f59e0b !important; text-shadow: 0 0 10px rgba(245, 158, 11, 0.5); }
.stTextInput input, .stSelectbox select {
    color: #ffffff !important;
    background-color: rgba(15, 23, 42, 0.8) !important;
    border: 1px solid #38bdf8 !important;
    border-radius: 8px !important;
}
.stTextInput label, .stSelectbox label { color: #f8fafc !important; font-weight: 600 !important; }
.chat-bubble {
    background: rgba(30, 41, 59, 0.85);
    border-left: 4px solid #38bdf8;
    padding: 10px 15px;
    border-radius: 8px;
    margin-bottom: 10px;
}
.login-box {
    background: rgba(30, 41, 59, 0.95);
    border: 1px solid #38bdf8;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
    text-align: center;
}
.admin-box {
    background: rgba(15, 23, 42, 0.95);
    border: 2px solid #f59e0b;
    border-radius: 12px;
    padding: 15px;
    margin-bottom: 20px;
}
.paper-box {
    background: #ffffff !important;
    color: #0f172a !important;
    padding: 30px;
    border-radius: 12px;
    border: 2px solid #0f172a;
    font-family: 'Georgia', serif;
    box-shadow: 0 10px 25px rgba(0,0,0,0.5);
    margin-bottom: 20px;
}
</style>""", unsafe_allow_html=True)

# --- SCHWEIZER ZEITZONE HELPER ---
def get_swiss_now():
    return datetime.now(ZoneInfo("Europe/Zurich")).replace(tzinfo=None)

# --- OFFIZIELLE NFL TEAM FARBEN ---
TEAM_COLORS = {
    "ARI": "#97233F", "ATL": "#A71930", "BAL": "#241773", "BUF": "#00338D",
    "CAR": "#0085CA", "CHI": "#0B162A", "CIN": "#FB4F14", "CLE": "#311D00",
    "DAL": "#002244", "DEN": "#FB4F14", "DET": "#0076B6", "GB":  "#203731",
    "HOU": "#03202F", "IND": "#002C5F", "JAX": "#006778", "KC":  "#E31837",
    "LV":  "#000000", "LAC": "#0080C6", "LAR": "#003594", "MIA": "#008E97",
    "MIN": "#4F2683", "NE":  "#002244", "NO":  "#D3BC8D", "NYG": "#0B2265",
    "NYJ": "#125740", "PHI": "#004C54", "PIT": "#FFB612", "SF":  "#AA0000",
    "SEA": "#002244", "TB":  "#D50A0A", "TEN": "#0C2340", "WAS": "#5A1414"
}

BONUS_QUESTIONS = [
    "1) Spieler mit den meisten Yards in der Luft (Passing Yards)",
    "2) Spieler mit den meisten Yards am Boden (Rushing Yards)",
    "3) Längstes Fieldgoal der Saison (in Yards)",
    "4) Schlechtestes Team der Saison",
    "5) Bestes Team der Saison",
    "6) Höchster Record eines Teams (z.B. 15-2)",
    "7) MVP der Saison",
    "8) Team mit den meisten Punkten der Saison"
]

WEEK_SUNDAYS = {
    "1": "13.09.2026", "2": "20.09.2026", "3": "27.09.2026", "4": "04.10.2026",
    "5": "11.10.2026", "6": "18.10.2026", "7": "25.10.2026", "8": "01.11.2026",
    "9": "08.11.2026", "10": "15.11.2026", "11": "22.11.2026", "12": "29.11.2026",
    "13": "06.12.2026", "14": "13.12.2026", "15": "20.12.2026", "16": "27.12.2026",
    "17": "03.01.2027", "18": "10.01.2027"
}

DB_FILE = "nfl_tippspiel_data.json"

def clean_dict_data(data):
    if not isinstance(data, dict):
        return {u: {} for u in MITSPIELER}
    cleaned = {u: {} for u in MITSPIELER}
    for u in MITSPIELER:
        if u in data and isinstance(data[u], dict):
            for k, v in data[u].items():
                if v and str(v).strip() not in ["", "-", "None"]:
                    cleaned[u][k] = str(v).strip()
    return cleaned

def fetch_from_github():
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo = st.secrets.get("GITHUB_REPO")
        if not token or not repo:
            return None
        url = f"https://api.github.com/repos/{repo}/contents/{DB_FILE}"
        headers = {"Authorization": f"token {token}"}
        res = requests.get(url, headers=headers)
        if res.status_code == 200:
            content_b64 = res.json().get("content", "")
            content_json = base64.b64decode(content_b64).decode("utf-8")
            return json.loads(content_json)
    except Exception:
        pass
    return None

def load_db():
    gh_data = fetch_from_github()
    raw_data = gh_data if gh_data else {}
    
    if not raw_data and os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                raw_data = json.load(f)
        except Exception:
            raw_data = {}

    tipps_db = clean_dict_data(raw_data.get("tipps_db"))
    bonus_db = clean_dict_data(raw_data.get("bonus_db"))
    joker_db = clean_dict_data(raw_data.get("joker_db"))
    playoff_db = clean_dict_data(raw_data.get("playoff_db"))
    
    bonus_results = raw_data.get("bonus_results", {})
    if not isinstance(bonus_results, dict): bonus_results = {}
    
    comments_db = raw_data.get("comments_db", {})
    if not isinstance(comments_db, dict): comments_db = {}
    
    hosts_db = raw_data.get("hosts_db", {w: "Noch offen" for w in WEEK_SUNDAYS.keys()})
    if not isinstance(hosts_db, dict): hosts_db = {w: "Noch offen" for w in WEEK_SUNDAYS.keys()}

    return tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db

def sync_to_github(data_dict):
    try:
        token = st.secrets.get("GITHUB_TOKEN")
        repo = st.secrets.get("GITHUB_REPO")
        if not token or not repo:
            return False
        url = f"https://api.github.com/repos/{repo}/contents/{DB_FILE}"
        headers = {"Authorization": f"token {token}"}
        get_res = requests.get(url, headers=headers)
        sha = get_res.json().get("sha") if get_res.status_code == 200 else None
        
        content_json = json.dumps(data_dict, indent=4)
        content_b64 = base64.b64encode(content_json.encode("utf-8")).decode("utf-8")
        
        payload = {
            "message": "Automated backup: Update tippspiel data",
            "content": content_b64,
            "branch": "main"
        }
        if sha:
            payload["sha"] = sha
            
        put_res = requests.put(url, headers=headers, json=payload)
        return put_res.status_code in [200, 201]
    except Exception:
        return False

def save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
    data = {
        "tipps_db": tipps_db,
        "bonus_db": bonus_db,
        "bonus_results": bonus_results,
        "joker_db": joker_db,
        "comments_db": comments_db,
        "hosts_db": hosts_db,
        "playoff_db": playoff_db
    }
    with open(DB_FILE, "w") as f:
        json.dump(data, f, indent=4)
    sync_to_github(data)
    return True

tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db = load_db()

def get_current_nfl_week():
    now = get_swiss_now()
    week1_switch = datetime(2026, 9, 15, 0, 0, 0)
    if now < week1_switch:
        return 1
    days_diff = (now - week1_switch).days
    calc_week = 2 + (days_diff // 7)
    return min(max(calc_week, 1), 18)

current_default_week = get_current_nfl_week()

@st.cache_data(ttl=300)
def get_nfl_games(week_num=1, season_type=2):
    season_year = 2026
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={season_year}&week={week_num}&seasontype={season_type}"
    try:
        res = requests.get(url).json()
        games = []
        events = res.get('events', [])
        for ev in events:
            comp = ev['competitions'][0]
            t1 = comp['competitors'][0]
            t2 = comp['competitors'][1]
            status = comp['status']['type']['completed']
            in_progress = comp['status']['type']['state'] == 'in'
            
            leading_team = None
            if in_progress:
                s1, s2 = int(t1.get('score', 0)), int(t2.get('score', 0))
                if s1 > s2: leading_team = t1['team']['abbreviation']
                elif s2 > s1: leading_team = t2['team']['abbreviation']

            winner_id = None
            if status:
                winner_id = t1['team']['abbreviation'] if t1.get('winner') else t2['team']['abbreviation']

            games.append({
                'id': str(ev['id']),
                'matchup': f"{t1['team']['shortDisplayName']} vs {t2['team']['shortDisplayName']}",
                'home_team': t1['team']['shortDisplayName'],
                'home_abbr': t1['team']['abbreviation'],
                'home_logo': t1['team']['logo'],
                'home_score': t1.get('score', '0'),
                'away_team': t2['team']['shortDisplayName'],
                'away_abbr': t2['team']['abbreviation'],
                'away_logo': t2['team']['logo'],
                'away_score': t2.get('score', '0'),
                'completed': status,
                'in_progress': in_progress,
                'leading_abbr': leading_team,
                'winner_abbr': winner_id,
                'status_detail': comp['status']['type']['shortDetail']
            })
        return games
    except Exception:
        return []

@st.cache_data(ttl=86400)
def get_sleeper_players():
    try:
        res = requests.get("https://api.sleeper.app/v1/players/nfl", timeout=8)
        if res.status_code == 200:
            return res.json()
    except Exception:
        pass
    return {}

@st.cache_data(ttl=120)
def fetch_sleeper_fantasy_data(league_id, week_num):
    base_url = f"https://api.sleeper.app/v1/league/{league_id}"
    players_db = get_sleeper_players()
    
    try:
        league_res = requests.get(base_url, timeout=5).json()
        league_name = league_res.get("name", "Sleeper Fantasy League")
        season = league_res.get("season", "2026")

        users_res = requests.get(f"{base_url}/users", timeout=5).json()
        users_map = {}
        for u in users_res:
            u_id = u.get("user_id")
            disp_name = u.get("display_name", f"User {u_id}")
            meta_team_name = u.get("metadata", {}).get("team_name") if u.get("metadata") else None
            team_name = meta_team_name if meta_team_name else disp_name
            avatar_id = u.get("avatar")
            avatar_url = f"https://sleepercdn.com/avatars/thumbs/{avatar_id}" if avatar_id else "https://sleepercdn.com/images/v2/icons/player_default.webp"
            users_map[u_id] = {"display_name": disp_name, "team_name": team_name, "avatar": avatar_url}

        rosters_res = requests.get(f"{base_url}/rosters", timeout=5).json()
        rosters_map = {}
        standings_list = []
        
        for r in rosters_res:
            r_id = r.get("roster_id")
            owner_id = r.get("owner_id")
            u_info = users_map.get(owner_id, {"display_name": f"Team {r_id}", "team_name": f"Team {r_id}", "avatar": "https://sleepercdn.com/images/v2/icons/player_default.webp"})
            settings = r.get("settings", {})
            wins = settings.get("wins", 0)
            losses = settings.get("losses", 0)
            ties = settings.get("ties", 0)
            fpts = settings.get("fpts", 0) + (settings.get("fpts_decimal", 0) / 100.0)
            fpts_against = settings.get("fpts_against", 0) + (settings.get("fpts_against_decimal", 0) / 100.0)
            
            rosters_map[r_id] = {"team_name": u_info["team_name"], "manager": u_info["display_name"], "avatar": u_info["avatar"], "wins": wins, "losses": losses, "ties": ties, "fpts": round(fpts, 2)}
            standings_list.append({"avatar": u_info["avatar"], "team_name": u_info["team_name"], "manager": u_info["display_name"], "wins": wins, "losses": losses, "ties": ties, "fpts": round(fpts, 2), "fpts_against": round(fpts_against, 2)})
        
        standings_list = sorted(standings_list, key=lambda x: (x["wins"], x["fpts"]), reverse=True)

        matchups_res = requests.get(f"{base_url}/matchups/{week_num}", timeout=5).json()
        matchups_grouped = {}
        for m in matchups_res:
            m_id = m.get("matchup_id")
            if not m_id: continue
            r_id = m.get("roster_id")
            pts = round(m.get("points", 0.0), 2)
            r_info = rosters_map.get(r_id, {"team_name": f"Team {r_id}", "manager": "-", "avatar": ""})
            
            starters = m.get("starters", []) or []
            starters_pts = m.get("starters_points", []) or []
            players_pts = m.get("players_points", {}) or {}
            
            starters_list = []
            for idx, p_id in enumerate(starters):
                p_score = starters_pts[idx] if idx < len(starters_pts) else players_pts.get(p_id, 0.0)
                p_info = players_db.get(str(p_id), {}) if players_db else {}
                p_fn = p_info.get("first_name", "")
                p_ln = p_info.get("last_name", "")
                full_n = p_info.get("full_name") or f"{p_fn} {p_ln}".strip() or f"Player {p_id}"
                pos = p_info.get("position", "FLX")
                team = p_info.get("team") or "FA"
                starters_list.append({"name": full_n, "pos": pos, "team": team, "pts": round(p_score, 2)})

            if m_id not in matchups_grouped: matchups_grouped[m_id] = []
            matchups_grouped[m_id].append({"team_name": r_info["team_name"], "manager": r_info["manager"], "avatar": r_info["avatar"], "points": pts, "starters": starters_list})

        matchups_list = []
        for m_id, teams in matchups_grouped.items():
            if len(teams) >= 2:
                matchups_list.append({"team1": teams[0], "team2": teams[1]})

        return {"league_name": league_name, "season": season, "matchups": matchups_list, "standings": standings_list}, None
    except Exception as e:
        return None, str(e)

# --- PUNKTE RECHNUNGEN ---
def calculate_scores(all_games, phase="Regular Season", week_num=1, include_bonus=True):
    scores = {u: 0 for u in MITSPIELER}
    weekly_hits = {u: 0 for u in MITSPIELER}
    multiplier = 1 if phase == "Regular Season" else (2 if phase == "Playoffs" else 3)

    for game in all_games:
        if game['completed'] and game['winner_abbr']:
            for u in MITSPIELER:
                if tipps_db.get(u, {}).get(game['id']) == game['winner_abbr']:
                    joker_game_id = joker_db.get(u, {}).get(str(week_num))
                    joker_mult = 2 if (joker_game_id and joker_game_id == game['id']) else 1
                    scores[u] += 5 * multiplier * joker_mult
                    weekly_hits[u] += 1

    for u in MITSPIELER:
        if weekly_hits[u] >= 6: scores[u] += 10
            
    if include_bonus:
        for u in MITSPIELER:
            u_bonus = bonus_db.get(u, {})
            for q_idx, correct_ans in bonus_results.items():
                if correct_ans and u_bonus.get(q_idx, "").strip().lower() == correct_ans.strip().lower():
                    scores[u] += 15
            sb_correct = bonus_results.get("sb_winner", "")
            u_sb = playoff_db.get(u, {}).get("sb_winner", "")
            if sb_correct and u_sb and u_sb.strip().lower() == sb_correct.strip().lower():
                scores[u] += 25

    return scores, weekly_hits

def get_cumulative_scores(target_week):
    total_scores = {u: 0 for u in MITSPIELER}
    current_week_hits = {u: 0 for u in MITSPIELER}
    
    for w in range(1, target_week + 1):
        w_games = get_nfl_games(week_num=w)
        w_phase = "Regular Season" if w <= 18 else "Playoffs"
        w_scores, w_hits = calculate_scores(w_games, phase=w_phase, week_num=w, include_bonus=False)
        for u in MITSPIELER: total_scores[u] += w_scores[u]
        if w == target_week: current_week_hits = w_hits
            
    for u in MITSPIELER:
        u_bonus = bonus_db.get(u, {})
        for q_idx, correct_ans in bonus_results.items():
            if correct_ans and u_bonus.get(q_idx, "").strip().lower() == correct_ans.strip().lower():
                total_scores[u] += 15
        sb_correct = bonus_results.get("sb_winner", "")
        u_sb = playoff_db.get(u, {}).get("sb_winner", "")
        if sb_correct and u_sb and u_sb.strip().lower() == sb_correct.strip().lower():
            total_scores[u] += 25

    return total_scores, current_week_hits

# --- HELPER: AUTOMATISCHE DATEN-ANALYSE FÜR DEN ZEITUNGS-BERICHT ---
def get_weekly_newspaper_data(week_num, tipps_db, sleeper_data, comments_db, hosts_db, scores):
    w_games = get_nfl_games(week_num=week_num)
    w_scores, w_hits = calculate_scores(w_games, phase="Regular Season" if week_num <= 18 else "Playoffs", week_num=week_num, include_bonus=False)
    
    sorted_weekly = sorted(w_scores.items(), key=lambda x: x[1], reverse=True)
    weekly_winner = sorted_weekly[0][0] if sorted_weekly else "N/A"
    weekly_winner_pts = sorted_weekly[0][1] if sorted_weekly else 0
    weekly_winner_hits = w_hits.get(weekly_winner, 0)
    
    weekly_flop = sorted_weekly[-1][0] if sorted_weekly else "N/A"
    weekly_flop_pts = sorted_weekly[-1][1] if sorted_weekly else 0
    
    sorted_overall = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    overall_leader = sorted_overall[0][0] if sorted_overall else "N/A"
    overall_leader_pts = sorted_overall[0][1] if sorted_overall else 0
    
    fantasy_mvp_name = "N/A"
    fantasy_mvp_pts = 0.0
    fantasy_pechvogel = "N/A"
    closest_match_text = "Keine aktiven Matchup-Daten vorhanden."
    
    if sleeper_data and sleeper_data.get("matchups"):
        all_teams = []
        matchup_diffs = []
        for m in sleeper_data["matchups"]:
            t1, t2 = m["team1"], m["team2"]
            all_teams.append(t1)
            all_teams.append(t2)
            diff = abs(t1["points"] - t2["points"])
