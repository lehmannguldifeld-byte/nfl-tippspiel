import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import numpy as np
import os
import base64
import urllib.parse

# --- SEITEN-KONFIGURATION & STADION-FLUTLICHT DESIGN ---
st.set_page_config(page_title="NFL Tippspiel 2026/27", page_icon="🏈", layout="wide")

# ESPN FANTASY LEAGUE CONFIG
ESPN_LEAGUE_ID = "434475025"

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

st.markdown("""
    <style>
    /* Stadion-Flutlicht Effect Background */
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
    .team-box-left {
        display: flex;
        align-items: center;
        justify-content: flex-end;
        gap: 6px;
    }
    .team-box-right {
        display: flex;
        align-items: center;
        justify-content: flex-start;
        gap: 6px;
    }
    .team-name {
        font-size: 0.95rem;
        font-weight: 800;
        color: #f8fafc;
    }
    .score-badge {
        font-size: 1.2rem;
        font-weight: 900;
        color: #38bdf8;
        background: rgba(15, 23, 42, 0.8);
        padding: 4px 10px;
        border-radius: 8px;
        border: 1px solid rgba(255,255,255,0.1);
    }
    .winner-highlight {
        color: #f59e0b !important;
        text-shadow: 0 0 10px rgba(245, 158, 11, 0.5);
    }

    .stTextInput input, .stSelectbox select {
        color: #ffffff !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    .stTextInput label, .stSelectbox label {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    
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
    </style>
""", unsafe_allow_html=True)

# --- PASSWÖRTER & MITSPIELER LISTE ---
PASSWORDS = {
    "Andy": "andy2026", "Ronny": "ronny2026", "Bauzzen": "bauzzen2026", "Bössi": "boessi2026",
    "Jerome": "jerome2026", "Mäni": "maeni2026", "Domi": "domi2026", "Pädu": "paedu2026"
}
MITSPIELER = list(PASSWORDS.keys())

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

# NFL Saison-Sonntage 2026/27
WEEK_SUNDAYS = {
    "1": "13.09.2026", "2": "20.09.2026", "3": "27.09.2026", "4": "04.10.2026",
    "5": "11.10.2026", "6": "18.10.2026", "7": "25.10.2026", "8": "01.11.2026",
    "9": "08.11.2026", "10": "15.11.2026", "11": "22.11.2026", "12": "29.11.2026",
    "13": "06.12.2026", "14": "13.12.2026", "15": "20.12.2026", "16": "27.12.2026",
    "17": "03.01.2027", "18": "10.01.2027"
}

# --- SESSION STATE LOGIN VERWALTUNG ---
if "logged_user" not in st.session_state:
    st.session_state["logged_user"] = None

# --- DATENBANK VERWALTUNG ---
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
    now = datetime.now()
    week1_deadline = datetime(2026, 9, 10, 12, 0, 0)
    if now < week1_deadline:
        return 1
    days_diff = (now - week1_deadline).days
    calc_week = 1 + (days_diff // 7)
    return min(max(calc_week, 1), 18)

current_default_week = get_current_nfl_week()

# --- ESPN API FOR NFL GAMES ---
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

# --- ESPN FANTASY LEAGUE API FETCH (INTELLIGENT FALLBACK) ---
@st.cache_data(ttl=120)
def fetch_espn_fantasy_data(league_id):
    years_to_try = [2026, datetime.now().year]
    cookies = {}
    espn_s2 = st.secrets.get("ESPN_S2")
    swid = st.secrets.get("ESPN_SWID")
    if espn_s2 and swid:
        cookies = {"espn_s2": espn_s2, "SWID": swid}

    for season_year in set(years_to_try):
        url = f"https://fantasy.espn.com/apis/v3/games/ffl/seasons/{season_year}/segments/0/leagues/{league_id}?view=mMatchupScore&view=mScoreboard&view=mTeam&view=mSettings"
        try:
            res = requests.get(url, cookies=cookies)
            if res.status_code == 200:
                data = res.json()
                teams_map = {}
                teams_list = []
                for t in data.get('teams', []):
                    name = f"{t.get('location', '')} {t.get('nickname', '')}".strip()
                    if not name:
                        name = f"Team {t.get('id')}"
                    logo = t.get('logo', '')
                    record = t.get('record', {}).get('overall', {})
                    wins = record.get('wins', 0)
                    losses = record.get('losses', 0)
                    ties = record.get('ties', 0)
                    points = record.get('pointsFor', 0.0)
                    
                    teams_map[t['id']] = {'name': name, 'logo': logo}
                    teams_list.append({
                        'Team': name,
                        'W': wins,
                        'L': losses,
                        'T': ties,
                        'Punkte': round(points, 1)
                    })

                scoring_period = data.get('scoringPeriodId', 1)
                schedule = data.get('schedule', [])
                
                current_matchups = []
                for m in schedule:
                    if m.get('matchupPeriodId') == scoring_period:
                        h_id = m.get('home', {}).get('teamId')
                        a_id = m.get('away', {}).get('teamId')
                        h_score = m.get('home', {}).get('totalPoints', 0.0)
                        a_score = m.get('away', {}).get('totalPoints', 0.0)
                        
                        home_team_info = teams_map.get(h_id, {'name': f"Team {h_id}", 'logo': ''})
                        away_team_info = teams_map.get(a_id, {'name': f"Team {a_id}", 'logo': ''})
                        
                        current_matchups.append({
                            'home_name': home_team_info['name'],
                            'home_logo': home_team_info['logo'],
                            'home_score': round(h_score, 2),
                            'away_name': away_team_info['name'],
                            'away_logo': away_team_info['logo'],
                            'away_score': round(a_score, 2)
                        })
                        
                return {
                    'league_name': data.get('settings', {}).get('name', 'ESPN Fantasy League'),
                    'week': scoring_period,
                    'matchups': current_matchups,
                    'standings': teams_list
                }, None
        except Exception:
            pass
    return None, "Konnte Liga-Daten von ESPN nicht abrufen."

# --- PUNKTE LOGIK ---
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
        if weekly_hits[u] >= 6:
            scores[u] += 10
            
    if include_bonus:
        for u in MITSPIELER:
            u_bonus = bonus_db.get(u, {})
            for q_idx, correct_ans in bonus_results.items():
                if correct_ans and u_bonus.get(q_idx, "").strip().lower() == correct_ans.strip().lower():
                    scores[u] += 15
            
            # Super Bowl Champion Bonus (+25 Pkt)
            sb_correct = bonus_results.get("sb_winner", "")
            u_sb = playoff_db.get(u, {}).get("sb_winner", "")
            if sb_correct and u_sb and u_sb.strip().lower() == sb_correct.strip().lower():
                scores[u] += 25

    return scores, weekly_hits

# --- APP UI HEADER & LOGIN SYSTEM ---
st.markdown("<h1 class='main-title'>🏈 NFL TIPPSPIEL 2026/27</h1>", unsafe_allow_html=True)

# LOGIN BANNER / SYSTEM
with st.container():
    col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
    with col_l2:
        if st.session_state["logged_user"] is None:
            st.markdown("<div class='login-box'>", unsafe_allow_html=True)
            st.write("🔑 **Bitte einmalig einloggen, um deine Tipps abzugeben:**")
            col_u, col_p, col_b = st.columns([2, 2, 1])
            with col_u:
                user_try = st.selectbox("Wer bist du?", MITSPIELER, key="global_user")
            with col_p:
                pass_try = st.text_input("Passwort", type="password", key="global_pass")
            with col_b:
                st.write("") # Spacer
                if st.button("🔓 Login"):
                    if PASSWORDS.get(user_try) == pass_try:
                        st.session_state["logged_user"] = user_try
                        st.success(f"Angemeldet als {user_try}!")
                        st.rerun()
                    else:
                        st.error("Falsches Passwort!")
            st.markdown("</div>", unsafe_allow_html=True)
        else:
            active_user = st.session_state["logged_user"]
            st.markdown(f"""
                <div class='login-box' style='border-color: #4ade80;'>
                    <span style='font-size: 1.1rem;'>✅ Eingeloggt als: <b>{active_user}</b></span>
                </div>
            """, unsafe_allow_html=True)
            if st.button("🔒 Ausloggen", key="logout_btn"):
                st.session_state["logged_user"] = None
                st.rerun()

# WOCHEN SLIDER
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    woche = st.slider("Woche / Spieltag auswählen", min_value=1, max_value=18, value=current_default_week)
    phase_choice = "Regular Season" if woche <= 18 else "Playoffs"

nfl_games = get_nfl_games(week_num=woche, season_type=2)
scores, hits = calculate_scores(nfl_games, phase=phase_choice, week_num=woche, include_bonus=True)

sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
bottom_two = [sorted_scores[-1][0], sorted_scores[-2][0]] if (len(sorted_scores) >= 2 and woche > 1) else []

now = datetime.now()
week1_deadline = datetime(2026, 9, 10, 12, 0, 0)
bonus_deadline = datetime(2026, 9, 10, 12, 0, 0)

# PRÄZISE FRISTEN-LOGIK FÜR VERGANGENE / AKTUELLE / ZUKÜNFTIGE WOCHEN
if woche < current_default_week:
    is_after_thursday_noon = True
elif woche > current_default_week:
    is_after_thursday_noon = False
else:
    if woche == 1:
        is_after_thursday_noon = now >= week1_deadline
    else:
        is_after_thursday_noon = (now.weekday() == 3 and now.hour >= 12) or (now.weekday() > 3)

can_edit_bonus = now < bonus_deadline

tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10, tab11 = st.tabs([
    "🏈 Tippen", 
    "📊 Leaderboard", 
    "📋 Tipp-Übersicht", 
    "🚨 RedZone Live", 
    "⚔️ Head-to-Head & Trash Talk", 
    "🏠 Host-Kalender", 
    "🗓️ Spielplan & Scores", 
    "📈 Saisonverlauf", 
    "📊 Tipp-Analytics", 
    "🎯 Bonustipps",
    "🏈 ESPN Fantasy"
])

# --- TAB 1: TIPP-FORMULAR + ADMIN ---
with tab1:
    if st.session_state["logged_user"] == "Pädu":
        st.markdown("<div class='admin-box'>", unsafe_allow_html=True)
        st.markdown(f"### 👑 Admin-Kontrollzentrum (Woche {woche})")
        
        game_ids_wk = [g['id'] for g in nfl_games]
        total_games_wk = len(game_ids_wk)
        
        missing_users = []
        done_users = []
        
        col_adm1, col_adm2 = st.columns(2)
        with col_adm1:
            st.write("📊 **Tipp-Status der 8 Mitspieler:**")
            for u in MITSPIELER:
                u_tipps = tipps_db.get(u, {})
                count = sum(1 for g_id in game_ids_wk if u_tipps.get(g_id))
                if count == total_games_wk and total_games_wk > 0:
                    st.markdown(f"🟢 **{u}**: {count}/{total_games_wk} Tipps abgegeben ✅")
                    done_users.append(u)
                elif count > 0:
                    st.markdown(f"🟡 **{u}**: {count}/{total_games_wk} Tipps (unvollständig)")
                    missing_users.append(u)
                else:
                    st.markdown(f"🔴 **{u}**: Noch nicht getippt (0/{total_games_wk})")
                    missing_users.append(u)
                    
        with col_adm2:
            st.write("📲 **Gruppe benachrichtigen / erinnern:**")
            if missing_users:
                missing_str = ", ".join(missing_users)
                msg = f"Hallo Leute! 🏈 Kurze Erinnerung für Woche {woche}: Folgende Spieler müssen noch tippen: {missing_str}. Deadline ist Donnerstag um 12:00 Uhr!"
                encoded_msg = urllib.parse.quote(msg)
                st.markdown(f'<a href="https://api.whatsapp.com/send?text={encoded_msg}" target="_blank"><button style="background-color:#25D366; color:white; border:none; padding:10px 15px; border-radius:8px; font-weight:bold; cursor:pointer;">💬 WhatsApp-Erinnerung senden</button></a>', unsafe_allow_html=True)
            else:
                st.success("🎉 Genial! Alle 8 Mitspieler haben für Woche " + str(woche) + " vollständig getippt!")
        st.markdown("</div>", unsafe_allow_html=True)

    if not st.session_state["logged_user"]:
        st.warning("🔑 Bitte logge dich oben ein, um deine Tipps abzugeben.")
    else:
        active_user = st.session_state["logged_user"]
        st.subheader(f"Tipps abgeben für {active_user} (Woche {woche})")
        if is_after_thursday_noon:
            st.error(f"🚨 Die Tippabgabe für Woche {woche} ist GESPERRT!")
        else:
            if woche == 1:
                st.info("⏳ Tippabgabe für Woche 1 offen! Frist: **Donnerstag, 10.09.2026 um 12:00 Uhr**.")
            else:
                st.info(f"⏳ Tippabgabe offen! Deadline für Woche {woche}: Dieser Donnerstag um 12:00 Uhr mittags.")

        user_existing_tipps = tipps_db.get(active_user, {})
        new_tipps = user_existing_tipps.copy()

        selected_joker_game = None
        if active_user in bottom_two and woche > 1:
            st.warning("🃏 **Catch-Up Joker verfügbar!** Da du auf den hinteren Plätzen liegst, kannst du für EIN Spiel 2x Punkte aktivieren.")
            joker_options = {"Kein Joker": None}
            for g in nfl_games:
                joker_options[g['matchup']] = g['id']
            
            current_joker = joker_db.get(active_user, {}).get(str(woche))
            default_idx = 0
            if current_joker:
                for idx, (label, g_id) in enumerate(joker_options.items()):
                    if g_id == current_joker:
                        default_idx = idx
                        break

            chosen_joker_label = st.selectbox("Wähle dein Joker-Spiel für 2x Punkte:", list(joker_options.keys()), index=default_idx)
            selected_joker_game = joker_options[chosen_joker_label]

        with st.form("tipp_form"):
            for game in nfl_games:
                st.markdown("<div class='game-card-compact'>", unsafe_allow_html=True)
                
                col_home, col_pick, col_away = st.columns([1, 1, 1])
                
                with col_home:
                    st.markdown(f"""
                        <div class='team-box-left'>
                            <span class='team-name'>{game['home_team']}</span>
                            <img src='{game['home_logo']}' width='32'>
                        </div>
                    """, unsafe_allow_html=True)
                    
                with col_pick:
                    options = [game['home_abbr'], game['away_abbr']]
                    current_choice = user_existing_tipps.get(game['id'])
                    idx = options.index(current_choice) if current_choice in options else None
                    
                    selected = st.radio(
                        label=f"Radio_{game['id']}",
                        options=options,
                        index=idx,
                        key=f"r_{active_user}_{game['id']}",
                        horizontal=True,
                        disabled=is_after_thursday_noon,
                        label_visibility="collapsed"
                    )
                    if selected:
                        new_tipps[game['id']] = selected
                        
                with col_away:
                    st.markdown(f"""
                        <div class='team-box-right'>
                            <img src='{game['away_logo']}' width='32'>
                            <span class='team-name'>{game['away_team']}</span>
                        </div>
                    """, unsafe_allow_html=True)
                    
                st.markdown("</div>", unsafe_allow_html=True)

            if not is_after_thursday_noon:
                if st.form_submit_button("🏈 Tipps speichern"):
                    tipps_db[active_user] = new_tipps
                    if active_user in bottom_two and woche > 1:
                        if active_user not in joker_db:
                            joker_db[active_user] = {}
                        joker_db[active_user][str(woche)] = selected_joker_game
                    
                    if save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
                        st.success(f"✅ **Tipps für {active_user} (Woche {woche}) gespeichert!**")
                        st.toast("Tipps erfolgreich gespeichert!", icon="🏈")

# --- TAB 2: LEADERBOARD ---
with tab2:
    st.subheader(f"Gesamtwertung — Woche {woche}")
    for rank, (user, score) in enumerate(sorted_scores, 1):
        badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        fire = " 🔥 ON FIRE (+10 Bonus!)" if hits[user] >= 6 else ""
        joker_badge = " 🃏 (Joker-Berechtigt!)" if user in bottom_two else ""
        
        st.markdown(f"""
            <div class='leaderboard-card'>
                <div>
                    <span style='font-size: 1.3rem; font-weight: bold;'>{badge} {user}</span>
                    <span style='color: #4ade80; font-weight: bold; margin-left: 10px;'>{fire}</span>
                    <span style='color: #f59e0b; font-weight: bold; margin-left: 10px;'>{joker_badge}</span>
                </div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #38bdf8;'>
                    {score} <span style='font-size: 0.9rem; color: #cbd5e1;'>Pkt</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- TAB 3: TIPP-ÜBERSICHT ---
with tab3:
    st.subheader(f"Tipp-Vergleich aller 8 Mitspieler")
    def style_team_colors(val):
        clean_val = str(val).replace(" 🃏 2x", "").strip()
        bg_color = TEAM_COLORS.get(clean_val, "#334155")
        text_color = "#0f172a" if clean_val in ["PIT", "NO"] else "#ffffff"
        style = f'background-color: {bg_color}; color: {text_color}; font-weight: bold; border-radius: 6px;'
        if "🃏" in str(val):
            style += ' border: 2.5px solid #f59e0b; box-shadow: 0 0 8px #f59e0b;'
        return style

    if not is_after_thursday_noon:
        st.warning("🔒 Die echten Tipps für diese Woche werden erst am **Donnerstag um 12:00 Uhr** freigeschaltet!")
    else:
        if not nfl_games:
            st.info("Keine Spiele gefunden.")
        else:
            table_data = []
            for g in nfl_games:
                row = {"Begegnung": g['matchup'], "Status": g['status_detail']}
                for u in MITSPIELER:
                    t = tipps_db.get(u, {}).get(g['id'], "-")
                    if joker_db.get(u, {}).get(str(woche)) == g['id']:
                        t += " 🃏 2x"
                    row[u] = t
                table_data.append(row)
            df_table = pd.DataFrame(table_data)
            styled_real_df = df_table.style.apply(lambda col: [style_team_colors(v) for v in col] if col.name in MITSPIELER else [''] * len(col))
            st.dataframe(styled_real_df, use_container_width=True)

# --- TAB 4: REDZONE LIVE ---
with tab4:
    st.subheader(f"🚨 RedZone Live Center — Spieltag {woche}")
    st.caption("Echtzeit-Berechnung der Punkte während der laufenden NFL-Spiele!")
    
    live_scores = scores.copy()
    live_games_count = 0
    
    for g in nfl_games:
        if g['in_progress'] and g['leading_abbr']:
            live_games_count += 1
            for u in MITSPIELER:
                if tipps_db.get(u, {}).get(g['id']) == g['leading_abbr']:
                    j_mult = 2 if joker_db.get(u, {}).get(str(woche)) == g['id'] else 1
                    live_scores[u] += 5 * j_mult

    if live_games_count > 0:
        st.error(f"🔴 **LIVE IN PROGRESS:** {live_games_count} Spiel(e) laufen aktuell!")
    else:
        st.info("ℹ️ Aktuell laufen keine Live-Spiele. Die Live-Tabelle zeigt den Stand der beendeten Spiele.")

    sorted_live = sorted(live_scores.items(), key=lambda x: x[1], reverse=True)
    
    col_rz1, col_rz2 = st.columns([1, 1])
    with col_rz1:
        st.markdown("### 🏆 Live-Tabelle (Inkl. Führungspunkte)")
        for r_idx, (u, l_pts) in enumerate(sorted_live, 1):
            diff = l_pts - scores[u]
            diff_text = f" <span style='color:#f43f5e; font-size:0.9rem;'>(+{diff} Live!)</span>" if diff > 0 else ""
            st.markdown(f"""
                <div class='redzone-card'>
                    <div style='display:flex; justify-content:space-between; align-items:center;'>
                        <span style='font-size:1.1rem; font-weight:bold;'>#{r_idx} {u} {diff_text}</span>
                        <span style='font-size:1.4rem; font-weight:bold; color:#f43f5e;'>{l_pts} Pkt</span>
                    </div>
                </div>
            """, unsafe_allow_html=True)

    with col_rz2:
        st.markdown("### 📺 Aktuelle Live-Spiele & Trends")
        for g in nfl_games:
            if g['in_progress']:
                st.markdown(f"""
                    <div class='game-card-compact' style='border-color: #f43f5e;'>
                        <div style='color:#f43f5e; font-weight:bold; margin-bottom:5px;'>🔴 LIVE: {g['status_detail']}</div>
                        <div style='display:flex; justify-content:space-between; align-items:center;'>
                            <span><b>{g['home_team']}</b> ({g['home_score']})</span>
                            <span style='font-size:1.2rem; font-weight:bold;'>VS</span>
                            <span><b>{g['away_team']}</b> ({g['away_score']})</span>
                        </div>
                    </div>
                """, unsafe_allow_html=True)
            elif g['completed']:
                st.caption(f"✅ Beendet: {g['matchup']} — Endstand: {g['home_score']}:{g['away_score']}")

# --- TAB 5: HEAD-TO-HEAD & TRASH TALK ---
with tab5:
    st.subheader("⚔️ Head-to-Head Vergleich")
    col_p1, col_p2 = st.columns(2)
    with col_p1: p1 = st.selectbox("Spieler 1:", MITSPIELER, index=0)
    with col_p2: p2 = st.selectbox("Spieler 2:", MITSPIELER, index=1)
    
    if p1 != p2:
        diff_count = 0
        st.markdown(f"**Vergleich für Woche {woche}:**")
        for g in nfl_games:
            t1 = tipps_db.get(p1, {}).get(g['id'], "-")
            t2 = tipps_db.get(p2, {}).get(g['id'], "-")
            if t1 != t2 and is_after_thursday_noon:
                diff_count += 1
                st.info(f"⚡ **{g['matchup']}**: {p1} setzt auf **{t1}** 🆚 {p2} setzt auf **{t2}**")
        if diff_count == 0 and is_after_thursday_noon:
            st.success("Beide Spieler haben in dieser Woche exakt dieselben Teams getippt!")
        elif not is_after_thursday_noon:
            st.warning("🔒 Der direkte Tipp-Vergleich schaltet sich am Donnerstag um 12:00 Uhr frei!")

    st.markdown("---")
    st.subheader("💬 Trash Talk Pinnwand")
    w_comments = comments_db.get(str(woche), [])
    if not w_comments:
        st.info("Noch keine Sprüche für diese Woche vorhanden. Sei der Erste!")
    else:
        for c in w_comments:
            st.markdown(f"<div class='chat-bubble'><b>{c['user']}:</b> {c['text']} <span style='font-size:0.75rem; color:#94a3b8;'>({c['time']})</span></div>", unsafe_allow_html=True)
        
    st.markdown("##### ✏️ Spruch auf die Pinnwand posten:")
    if st.session_state["logged_user"]:
        curr_u = st.session_state["logged_user"]
        with st.form("comment_form"):
            st.write(f"Posten als: **{curr_u}**")
            c_text = st.text_input("Dein Spruch / Kommentar zur Woche:")
            if st.form_submit_button("💬 Kommentar posten"):
                if c_text.strip():
                    if str(woche) not in comments_db:
                        comments_db[str(woche)] = []
                    comments_db[str(woche)].append({
                        "user": curr_u,
                        "text": c_text.strip(),
                        "time": datetime.now().strftime("%H:%M")
                    })
                    save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db)
                    st.success("Spruch gepostet!")
                    st.rerun()
    else:
        st.warning("🔑 Bitte logge dich oben ein, um auf der Pinnwand zu posten.")

# --- TAB 6: HOST-KALENDER ---
with tab6:
    st.subheader("🏠 Football-Homezone — Bei wem schauen wir Sonntags?")
    current_wk_str = str(current_default_week)
    col_h1, col_h2 = st.columns(2)
    for w_idx in range(1, 19):
        w_str = str(w_idx)
        sunday_date = WEEK_SUNDAYS[w_str]
        host_name = hosts_db.get(w_str, "Noch offen")
        target_col = col_h1 if w_idx % 2 != 0 else col_h2
        is_next = (w_str == current_wk_str)
        card_class = "host-card host-card-next" if is_next else "host-card"
        next_badge = " 🔥 <span style='color:#38bdf8; font-weight:bold;'>(Nächster Sonntag!)</span>" if is_next else ""
        
        with target_col:
            st.markdown(f"""
                <div class='{card_class}'>
                    <div>
                        <div style='font-size: 1.1rem; font-weight: 800; color: #f8fafc;'>
                            Woche {w_idx} — 📅 {sunday_date} {next_badge}
                        </div>
                        <div style='font-size: 0.95rem; color: #94a3b8;'>
                            Gastgeber: <b style='color: #38bdf8;'>{host_name}</b>
                        </div>
                    </div>
                    <div style='font-size: 1.8rem;'>🏠</div>
                </div>
            """, unsafe_allow_html=True)

    st.markdown("---")
    with st.expander("📝 Gastgeber eintragen / anpassen"):
        with st.form("host_form"):
            new_hosts = hosts_db.copy()
            col_f1, col_f2 = st.columns(2)
            for w_i in range(1, 19):
                w_s = str(w_i)
                t_col = col_f1 if w_i <= 9 else col_f2
                host_options = ["Noch offen"] + MITSPIELER
                current_host = hosts_db.get(w_s, "Noch offen")
                idx_h = host_options.index(current_host) if current_host in host_options else 0
                with t_col:
                    new_hosts[w_s] = st.selectbox(f"Woche {w_i} ({WEEK_SUNDAYS[w_s]}):", host_options, index=idx_h, key=f"host_select_{w_s}")
            if st.form_submit_button("💾 Gastgeber-Kalender speichern"):
                hosts_db = new_hosts
                if save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
                    st.success("✅ **Gastgeber-Kalender erfolgreich gespeichert!**")
                    st.rerun()

# --- TAB 7: SPIELPLAN & SCORES ---
with tab7:
    st.subheader(f"🏈 NFL Game Center — Woche {woche}")
    if not nfl_games:
        st.info("Keine Begegnungen für diese Woche gefunden.")
    else:
        col_a, col_b = st.columns(2)
        for idx, g in enumerate(nfl_games):
            target_col = col_a if idx % 2 == 0 else col_b
            is_completed = g['completed']
            h_win = "winner-highlight" if is_completed and g['winner_abbr'] == g['home_abbr'] else ""
            a_win = "winner-highlight" if is_completed and g['winner_abbr'] == g['away_abbr'] else ""
            
            with target_col:
                st.markdown(f"""
                    <div class='schedule-card'>
                        <div style='text-align: center; color: #94a3b8; font-size: 0.85rem; font-weight: 700; margin-bottom: 12px; letter-spacing: 0.5px;'>
                            {g['status_detail']}
                        </div>
                        <div style='display: flex; justify-content: space-between; align-items: center;'>
                            <div class='team-box-right'>
                                <img src='{g['home_logo']}' width='45'>
                                <span class='team-name {h_win}'>{g['home_team']}</span>
                            </div>
                            <div class='score-badge'>{g['home_score']} : {g['away_score']}</div>
                            <div class='team-box-right' style='flex-direction: row-reverse;'>
                                <img src='{g['away_logo']}' width='45'>
                                <span class='team-name {a_win}'>{g['away_team']}</span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# --- TAB 8: SAISONVERLAUF (KORREKTE WOCHEN-SUMMIERUNG OHNE DUPLIZIERTE BONUS-PUNKTE) ---
with tab8:
    st.subheader("📈 Der Kampf um die Krone (Punkteverlauf)")
    history_data = {u: [0] for u in MITSPIELER}
    for w in range(1, woche + 1):
        w_games = get_nfl_games(week_num=w)
        # include_bonus=False verhindert die Mehrfach-Hinzurechnung von Bonuspunkten in der Schleife!
        w_scores, _ = calculate_scores(w_games, week_num=w, include_bonus=False)
        for u in MITSPIELER:
            prev = history_data[u][-1]
            history_data[u].append(prev + w_scores[u])
            
    chart_df = pd.DataFrame(history_data, index=[f"Start"] + [f"Woche {i}" for i in range(1, woche + 1)])
    st.line_chart(chart_df)

# --- TAB 9: STRICKTE TIPP ANALYTICS ---
with tab9:
    st.subheader("📊 Tipp-Trends & Gruppen-Analyse")
    st.caption("Statistische Auswertung aller abgegebenen Tipps der 8 Mitspieler.")
    
    valid_team_abbrs = set(TEAM_COLORS.keys())
    all_picked_teams = []
    
    for u in MITSPIELER:
        for game_id, team in tipps_db.get(u, {}).items():
            val = str(team).strip()
            if val in valid_team_abbrs:
                all_picked_teams.append(val)

    if len(all_picked_teams) == 0:
        st.info("ℹ️ Noch keine echten Tippdaten in der Gruppe vorhanden. Die Auswertung schaltet sich automatisch frei, sobald die ersten Tipps abgegeben wurden!")
    else:
        col_an1, col_an2 = st.columns(2)
        with col_an1:
            st.markdown("### 🔝 Top-5 Lieblingsteams der Gruppe")
            team_counts = pd.Series(all_picked_teams).value_counts().head(5)
            st.bar_chart(team_counts)

        with col_an2:
            st.markdown("### 🤝 Tipp-Übereinstimmung (Agreement Rate)")
            matrix_data = {}
            for u1 in MITSPIELER:
                row = {}
                for u2 in MITSPIELER:
                    tipps1 = {k: v for k, v in tipps_db.get(u1, {}).items() if str(v).strip() in valid_team_abbrs}
                    tipps2 = {k: v for k, v in tipps_db.get(u2, {}).items() if str(v).strip() in valid_team_abbrs}
                    common = set(tipps1.keys()) & set(tipps2.keys())
                    if len(common) > 0:
                        matches = sum(1 for k in common if tipps1[k] == tipps2[k])
                        pct = int((matches / len(common)) * 100)
                    else:
                        pct = "-"
                    row[u2] = f"{pct}%" if pct != "-" else "-"
                matrix_data[u1] = row
                
            df_matrix = pd.DataFrame(matrix_data)
            st.dataframe(df_matrix, use_container_width=True)
            st.caption("Zeigt in %, wie oft zwei Mitspieler exakt dieselben Sieger getippt haben.")

# --- TAB 10: BONUSTIPPS, UBERSICHT & ADMIN RESOLUTION ---
with tab10:
    st.subheader("🎯 Saison-Bonustipps & Super Bowl Champion")
    
    if can_edit_bonus:
        st.info("⏳ Die Bonustipps können bis zum **10.09.2026 um 12:00 Uhr** abgegeben werden.")
    else:
        st.error("🔒 Die Abgabefrist für die Bonustipps ist abgelaufen!")

    if st.session_state["logged_user"]:
        active_u = st.session_state["logged_user"]
        
        st.markdown(f"### ✏️ Bonustipps eingeben / anpassen ({active_u})")
        u_playoff_pick = playoff_db.get(active_u, {}).get("sb_winner", "")
        u_bonus = bonus_db.get(active_u, {})
        
        with st.form("bonus_form_tab"):
            sb_choice = st.text_input("🏆 Wer gewinnt den Super Bowl LXI? (25 Pkt)", value=u_playoff_pick, disabled=not can_edit_bonus)
            
            new_b = {}
            for idx, q in enumerate(BONUS_QUESTIONS):
                q_key = f"q_{idx}"
                current_val = u_bonus.get(q_key, "")
                new_b[q_key] = st.text_input(q, value=current_val, disabled=not can_edit_bonus)
                
            if can_edit_bonus and st.form_submit_button("🎯 Bonustipps speichern"):
                if active_u not in playoff_db: playoff_db[active_u] = {}
                playoff_db[active_u]["sb_winner"] = sb_choice.strip()
                bonus_db[active_u] = new_b
                if save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
                    st.success(f"✅ Bonustipps für **{active_u}** wurden erfolgreich gespeichert!")
                    st.rerun()
    else:
        st.warning("🔑 Bitte logge dich oben ein, um deine Bonustipps einzutragen.")

    st.markdown("---")
    
    st.markdown("### 📋 Übersicht aller Bonustipps der Gruppe")
    if can_edit_bonus:
        st.warning("🔒 Die Bonustipps der anderen Mitspieler werden erst am **10.09.2026 um 12:00 Uhr** sichtbar!")
    else:
        overview_data = []
        sb_row = {"Frage": "🏆 Super Bowl LXI Champion"}
        for u in MITSPIELER:
            sb_row[u] = playoff_db.get(u, {}).get("sb_winner", "-")
        overview_data.append(sb_row)
        
        for idx, q in enumerate(BONUS_QUESTIONS):
            q_key = f"q_{idx}"
            q_row = {"Frage": q}
            for u in MITSPIELER:
                q_row[u] = bonus_db.get(u, {}).get(q_key, "-")
            overview_data.append(q_row)
            
        df_bonus_overview = pd.DataFrame(overview_data)
        st.dataframe(df_bonus_overview, use_container_width=True)

    if st.session_state["logged_user"] == "Pädu":
        st.markdown("---")
        with st.expander("⚙️ Admin-Bereich: Auswertung, Musterlösung & RESET (Nur für Pädu)"):
            st.write("Trage hier die offiziellen Endergebnisse der Saison ein. Richtige Antworten geben automatisch **+15 Punkte** (Super Bowl = **+25 Pkt**) im Leaderboard!")
            with st.form("admin_bonus_form"):
                admin_new_res = {}
                admin_new_res["sb_winner"] = st.text_input("Richtiger Super Bowl Winner:", value=bonus_results.get("sb_winner", ""))
                for idx, q in enumerate(BONUS_QUESTIONS):
                    q_key = f"q_{idx}"
                    admin_new_res[q_key] = st.text_input(f"Richtige Lösung: {q}", value=bonus_results.get(q_key, ""))
                if st.form_submit_button("💾 Musterlösung speichern & Punkte verteilen"):
                    bonus_results = admin_new_res
                    if save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
                        st.success("✅ **Musterlösung erfolgreich gespeichert! Punkte wurden neu berechnet.**")
                        st.rerun()

            st.markdown("---")
            st.markdown("#### 🚨 Datenbank komplett zurücksetzen")
            st.warning("Achtung: Dieser Button löscht ALLE Tipp-Einträge, Bonustipps und Kommentare auf GitHub und setzt das Spiel auf 0 zurück!")
            if st.button("🚨 ALLES ZURÜCKSETZEN (RESET)", type="primary"):
                empty_tipps = {u: {} for u in MITSPIELER}
                empty_bonus = {u: {} for u in MITSPIELER}
                empty_joker = {u: {} for u in MITSPIELER}
                empty_playoff = {u: {} for u in MITSPIELER}
                empty_hosts = {w: "Noch offen" for w in WEEK_SUNDAYS.keys()}
                
                if save_db(empty_tipps, empty_bonus, {}, empty_joker, {}, empty_hosts, empty_playoff):
                    st.success("💥 **DATENBANK ERFOLGREICH ZURÜCKGESETZT!** Die App ist jetzt komplett leer und bereit für die Saison.")
                    st.rerun()

# --- TAB 11: ESPN FANTASY INTEGRATION ---
with tab11:
    st.subheader("🏈 ESPN Fantasy Football Live Center")
    st.caption(f"Angebunden an ESPN League ID: **{ESPN_LEAGUE_ID}**")
    
    fantasy_data, err_msg = fetch_espn_fantasy_data(ESPN_LEAGUE_ID)
    
    if err_msg or not fantasy_data:
        st.error("⚠️ **ESPN Liga nicht erreichbar oder als Privat markiert.**")
        st.info("""
            **So machst du eure Liga öffentlich (Empfohlen):**
            1. Logge dich auf `fantasy.espn.com` ein.
            2. Gehe zu **League** -> **Settings**.
            3. Ändere die Sichtbarkeit unter **Make League Viewable to Public** auf **Yes**.
            
            *Falls die Liga privat bleiben soll, trage deinen `ESPN_S2` und `SWID` Cookie in Streamlit Secrets ein.*
        """)
    else:
        st.success(f"🏆 **{fantasy_data['league_name']}** — Spieltag {fantasy_data['week']}")
        
        st.markdown("### ⚔️ Live-Matchups dieser Woche")
        if not fantasy_data['matchups']:
            st.info("Keine aktiven Matchups für diese Woche gefunden.")
        else:
            col_f1, col_f2 = st.columns(2)
            for idx, m in enumerate(fantasy_data['matchups']):
                target_col = col_f1 if idx % 2 == 0 else col_f2
                with target_col:
                    st.markdown(f"""
                        <div class='schedule-card'>
                            <div style='display: flex; justify-content: space-between; align-items: center;'>
                                <div style='display: flex; align-items: center; gap: 8px;'>
                                    {'<img src="' + m['home_logo'] + '" width="30">' if m['home_logo'] else ''}
                                    <b>{m['home_name']}</b>
                                </div>
                                <div class='score-badge'>{m['home_score']} : {m['away_score']}</div>
                                <div style='display: flex; align-items: center; gap: 8px;'>
                                    <b>{m['away_name']}</b>
                                    {'<img src="' + m['away_logo'] + '" width="30">' if m['away_logo'] else ''}
                                </div>
                            </div>
                        </div>
                    """, unsafe_allow_html=True)
                    
        st.markdown("---")
        st.markdown("### 📊 Aktuelle Fantasy-Tabelle (Standings)")
        if fantasy_data['standings']:
            df_standings = pd.DataFrame(fantasy_data['standings'])
            st.dataframe(df_standings, use_container_width=True)
