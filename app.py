import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
import numpy as np
import os
import base64

# --- SEITEN-KONFIGURATION & STADION-FLUTLICHT DESIGN ---
st.set_page_config(page_title="NFL Tippspiel 2026/27", page_icon="🏈", layout="wide")

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
    .game-card {
        background-color: rgba(30, 41, 59, 0.88);
        border-radius: 12px;
        padding: 18px;
        border: 1px solid rgba(255, 255, 255, 0.15);
        margin-bottom: 15px;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
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
    .team-box {
        display: flex;
        align-items: center;
        gap: 12px;
    }
    .team-name {
        font-size: 1.1rem;
        font-weight: 800;
        color: #f8fafc;
    }
    .score-badge {
        font-size: 1.4rem;
        font-weight: 900;
        color: #38bdf8;
        background: rgba(15, 23, 42, 0.8);
        padding: 4px 12px;
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
    
    .demo-banner {
        background: linear-gradient(90deg, #0284c7 0%, #38bdf8 50%, #0284c7 100%);
        color: #ffffff;
        font-weight: 800;
        text-align: center;
        padding: 10px;
        border-radius: 10px;
        font-size: 1.1rem;
        letter-spacing: 1px;
        margin-bottom: 20px;
        box-shadow: 0 4px 15px rgba(56, 189, 248, 0.4);
    }
    .chat-bubble {
        background: rgba(30, 41, 59, 0.85);
        border-left: 4px solid #38bdf8;
        padding: 10px 15px;
        border-radius: 8px;
        margin-bottom: 10px;
    }
    .profile-box {
        background: rgba(30, 41, 59, 0.95);
        border: 1px solid #38bdf8;
        border-radius: 12px;
        padding: 12px 20px;
        margin-bottom: 20px;
        text-align: center;
    }
    .bracket-node {
        background: rgba(15, 23, 42, 0.9);
        border: 1px solid #0284c7;
        border-radius: 8px;
        padding: 10px;
        margin-bottom: 8px;
        text-align: center;
        font-weight: bold;
    }
    </style>
""", unsafe_allow_html=True)

# --- MITSPIELER LISTE ---
MITSPIELER = ["Andy", "Ronny", "Bauzzen", "Bössi", "Jerome", "Mäni", "Domi", "Pädu"]

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

# --- DATENBANK VERWALTUNG ---
DB_FILE = "nfl_tippspiel_data.json"

DEFAULT_COMMENTS = {
    "1": [
        {"user": "Pädu", "text": "Ronny danke fürs kochen! 🍳🔥", "time": "21:05"},
        {"user": "Ronny", "text": "Immer gerne, dafür holst du am Sonntag 0 Punkte! 😜", "time": "21:08"}
    ]
}

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
    if gh_data:
        with open(DB_FILE, "w") as f:
            json.dump(gh_data, f, indent=4)
        return (
            gh_data.get("tipps_db", {u: {} for u in MITSPIELER}),
            gh_data.get("bonus_db", {u: {} for u in MITSPIELER}),
            gh_data.get("bonus_results", {}),
            gh_data.get("joker_db", {u: {} for u in MITSPIELER}),
            gh_data.get("comments_db", DEFAULT_COMMENTS),
            gh_data.get("hosts_db", {w: "Noch offen" for w in WEEK_SUNDAYS.keys()}),
            gh_data.get("playoff_db", {u: {} for u in MITSPIELER})
        )
    
    if os.path.exists(DB_FILE):
        try:
            with open(DB_FILE, "r") as f:
                data = json.load(f)
                return (
                    data.get("tipps_db", {u: {} for u in MITSPIELER}),
                    data.get("bonus_db", {u: {} for u in MITSPIELER}),
                    data.get("bonus_results", {}),
                    data.get("joker_db", {u: {} for u in MITSPIELER}),
                    data.get("comments_db", DEFAULT_COMMENTS),
                    data.get("hosts_db", {w: "Noch offen" for w in WEEK_SUNDAYS.keys()}),
                    data.get("playoff_db", {u: {} for u in MITSPIELER})
                )
        except Exception:
            pass
            
    return (
        {u: {} for u in MITSPIELER}, 
        {u: {} for u in MITSPIELER}, 
        {}, 
        {u: {} for u in MITSPIELER}, 
        DEFAULT_COMMENTS,
        {w: "Noch offen" for w in WEEK_SUNDAYS.keys()},
        {u: {} for u in MITSPIELER}
    )

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

# --- ESPN API ---
@st.cache_data(ttl=300)
def get_nfl_games(week_num=1, season_type=2):
    current_year = datetime.now().year
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={current_year}&week={week_num}&seasontype={season_type}"
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
            
            # Führendes Team bei laufenden Spielen bestimmen
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

# --- PUNKTE LOGIK ---
def calculate_scores(all_games, phase="Regular Season", week_num=1):
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
            
    for u in MITSPIELER:
        u_bonus = bonus_db.get(u, {})
        for q_idx, correct_ans in bonus_results.items():
            if correct_ans and u_bonus.get(q_idx, "").strip().lower() == correct_ans.strip().lower():
                scores[u] += 15

    return scores, weekly_hits

# --- APP UI HEADER & PROFIL AUSWAHL ---
st.markdown("<h1 class='main-title'>🏈 NFL TIPPSPIEL 2026/27</h1>", unsafe_allow_html=True)

col_l1, col_l2, col_l3 = st.columns([1, 2, 1])
with col_l2:
    st.markdown("<div class='profile-box'>", unsafe_allow_html=True)
    active_user = st.selectbox("👤 Wähle deinen Namen aus:", MITSPIELER, key="global_active_user")
    st.markdown("</div>", unsafe_allow_html=True)

# WOCHEN SLIDER
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    woche = st.slider("Woche / Spieltag auswählen", min_value=1, max_value=18, value=current_default_week)
    phase_choice = "Regular Season" if woche <= 18 else "Playoffs"

nfl_games = get_nfl_games(week_num=woche, season_type=2)
scores, hits = calculate_scores(nfl_games, phase=phase_choice, week_num=woche)

sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
bottom_two = [sorted_scores[-1][0], sorted_scores[-2][0]] if len(sorted_scores) >= 2 else []

now = datetime.now()
week1_deadline = datetime(2026, 9, 10, 12, 0, 0)

if woche == 1:
    is_after_thursday_noon = now >= week1_deadline
else:
    is_after_thursday_noon = (now.weekday() == 3 and now.hour >= 12) or (now.weekday() > 3)

# NEUE UNTERTEILUNG IN TABS INKLUSIVE 3, 4, 5!
tab1, tab2, tab3, tab4, tab5, tab6, tab7, tab8, tab9, tab10 = st.tabs([
    "📊 Leaderboard", 
    "🚨 RedZone Live",
    "🏠 Host-Kalender",
    "📈 Saisonverlauf", 
    "📊 Tipp-Analytics",
    "🏆 Playoff Bracket",
    "⚔️ Head-to-Head & Trash Talk", 
    "📋 Tipp-Übersicht", 
    "🗓️ Spielplan & Scores", 
    "🏈 Tippen & Bonustipps"
])

# --- TAB 1: RANGLISTE ---
with tab1:
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

# --- FEATURE 5: TAB 2 - REDZONE LIVE CENTER (ECHTZEIT SCOREBOARD) ---
with tab2:
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
                    <div class='game-card' style='border-color: #f43f5e;'>
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

# --- TAB 3: HOST-KALENDER ---
with tab3:
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

# --- TAB 4: SAISONVERLAUF ---
with tab4:
    st.subheader("📈 Der Kampf um die Krone (Punkteverlauf)")
    history_data = {u: [0] for u in MITSPIELER}
    for w in range(1, woche + 1):
        w_games = get_nfl_games(week_num=w)
        w_scores, _ = calculate_scores(w_games, week_num=w)
        for u in MITSPIELER:
            prev = history_data[u][-1]
            history_data[u].append(prev + w_scores[u])
            
    chart_df = pd.DataFrame(history_data, index=[f"Start"] + [f"Woche {i}" for i in range(1, woche + 1)])
    st.line_chart(chart_df)

# --- FEATURE 4: TAB 5 - TIPP ANALYTICS & TRENDS ---
with tab5:
    st.subheader("📊 Tipp-Trends & Gruppen-Analyse")
    st.caption("Statistische Auswertung aller abgegebenen Tipps der 8 Mitspieler.")
    
    # 1. Lieblingsteams der Gruppe
    all_picked_teams = []
    for u in MITSPIELER:
        for game_id, team in tipps_db.get(u, {}).items():
            if team and team != "-":
                all_picked_teams.append(team)
                
    col_an1, col_an2 = st.columns(2)
    with col_an1:
        st.markdown("### 🔝 Top-5 Lieblingsteams der Gruppe")
        if all_picked_teams:
            team_counts = pd.Series(all_picked_teams).value_counts().head(5)
            st.bar_chart(team_counts)
        else:
            st.info("Noch keine echten Tippdaten vorhanden.")

    # 2. Übereinstimmungs-Matrix
    with col_an2:
        st.markdown("### 🤝 Tipp-Übereinstimmung (Agreement Rate)")
        matrix_data = {}
        for u1 in MITSPIELER:
            row = {}
            for u2 in MITSPIELER:
                tipps1 = tipps_db.get(u1, {})
                tipps2 = tipps_db.get(u2, {})
                common = set(tipps1.keys()) & set(tipps2.keys())
                if common:
                    matches = sum(1 for k in common if tipps1[k] == tipps2[k])
                    pct = int((matches / len(common)) * 100)
                else:
                    pct = 100 if u1 == u2 else 0
                row[u2] = pct
            matrix_data[u1] = row
            
        df_matrix = pd.DataFrame(matrix_data)
        st.dataframe(df_matrix.style.background_gradient(cmap='Blues'), width="stretch")
        st.caption("Zeigt in %, wie oft zwei Mitspieler exakt dieselben Sieger getippt haben.")

# --- FEATURE 3: TAB 6 - PLAYOFF BRACKET & POSTSEASON ---
with tab6:
    st.subheader("🏆 NFL Playoff Bracket & Postseason Multiplikatoren")
    st.info("🔥 In den Playoffs steigen die Punkte pro richtigem Tipp! Wild Card: 2x Punkte | Super Bowl LXI: 3x Punkte!")
    
    col_b1, col_b2, col_b3, col_b4 = st.columns(4)
    with col_b1:
        st.markdown("#### Wild Card Round (2x)")
        st.markdown("<div class='bracket-node'>AFC Wild Card 1</div>", unsafe_allow_html=True)
        st.markdown("<div class='bracket-node'>AFC Wild Card 2</div>", unsafe_allow_html=True)
        st.markdown("<div class='bracket-node'>NFC Wild Card 1</div>", unsafe_allow_html=True)
        st.markdown("<div class='bracket-node'>NFC Wild Card 2</div>", unsafe_allow_html=True)
    with col_b2:
        st.markdown("#### Divisional Round (2x)")
        st.markdown("<div class='bracket-node'>AFC Divisional 1</div>", unsafe_allow_html=True)
        st.markdown("<div class='bracket-node'>NFC Divisional 1</div>", unsafe_allow_html=True)
    with col_b3:
        st.markdown("#### Conference Finals (2.5x)")
        st.markdown("<div class='bracket-node'>👑 AFC Championship</div>", unsafe_allow_html=True)
        st.markdown("<div class='bracket-node'>👑 NFC Championship</div>", unsafe_allow_html=True)
    with col_b4:
        st.markdown("#### Super Bowl LXI (3x)")
        st.markdown("<div class='bracket-node' style='border-color:#f59e0b; color:#f59e0b;'>🏈 SUPER BOWL CHAMPION</div>", unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("### 🎯 Dein Super Bowl Champion Tipp (25 Bonuspunkte)")
    u_playoff_pick = playoff_db.get(active_user, {}).get("sb_winner", "")
    with st.form("sb_winner_form"):
        sb_choice = st.text_input("Wer gewinnt den Super Bowl LXI?", value=u_playoff_pick)
        if st.form_submit_button("🏆 Super Bowl Tipp speichern"):
            if active_user not in playoff_db: playoff_db[active_user] = {}
            playoff_db[active_user]["sb_winner"] = sb_choice.strip()
            save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db)
            st.success(f"✅ Super Bowl Tipp '{sb_choice}' für {active_user} gespeichert!")

# --- TAB 7: HEAD-TO-HEAD & TRASH TALK ---
with tab7:
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
    w_comments = comments_db.get(str(woche), DEFAULT_COMMENTS.get(str(woche), []))
    for c in w_comments:
        st.markdown(f"<div class='chat-bubble'><b>{c['user']}:</b> {c['text']} <span style='font-size:0.75rem; color:#94a3b8;'>({c['time']})</span></div>", unsafe_allow_html=True)
        
    st.markdown("##### ✏️ Spruch auf die Pinnwand posten:")
    with st.form("comment_form"):
        st.write(f"Posten als: **{active_user}**")
        c_text = st.text_input("Dein Spruch / Kommentar zur Woche:")
        if st.form_submit_button("💬 Kommentar posten"):
            if c_text.strip():
                if str(woche) not in comments_db:
                    comments_db[str(woche)] = []
                comments_db[str(woche)].append({
                    "user": active_user,
                    "text": c_text.strip(),
                    "time": datetime.now().strftime("%H:%M")
                })
                save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db)
                st.success("Spruch gepostet!")
                st.rerun()

# --- TAB 8: TABLEARISCHE UBERSICHT ---
with tab8:
    st.subheader(f"Tipp-Vergleich aller 8 Mitspieler")
    show_demo = st.checkbox("💡 DEMO-MODUS ANZEIGEN (Vorschau für die Gruppe)", value=not is_after_thursday_noon)

    def style_team_colors(val):
        clean_val = str(val).replace(" 🃏 2x", "").strip()
        bg_color = TEAM_COLORS.get(clean_val, "#334155")
        text_color = "#0f172a" if clean_val in ["PIT", "NO"] else "#ffffff"
        style = f'background-color: {bg_color}; color: {text_color}; font-weight: bold; border-radius: 6px;'
        if "🃏" in str(val):
            style += ' border: 2.5px solid #f59e0b; box-shadow: 0 0 8px #f59e0b;'
        return style

    if show_demo:
        st.markdown("<div class='demo-banner'>⚡ VORSCHAU: Tipp-Übersicht in den echten Team-Farben! ⚡</div>", unsafe_allow_html=True)
        demo_games = [
            {"Matchup": "Chiefs (KC) vs. Eagles (PHI)", "Andy": "KC", "Ronny": "KC", "Bauzzen": "PHI", "Bössi": "KC", "Jerome": "PHI", "Mäni": "KC 🃏 2x", "Domi": "PHI 🃏 2x", "Pädu": "KC"},
            {"Matchup": "49ers (SF) vs. Cowboys (DAL)", "Andy": "SF", "Ronny": "SF", "Bauzzen": "SF", "Bössi": "DAL", "Jerome": "SF", "Mäni": "DAL", "Domi": "SF", "Pädu": "SF"},
            {"Matchup": "Lions (DET) vs. Packers (GB)", "Andy": "DET", "Ronny": "GB", "Bauzzen": "DET", "Bössi": "DET", "Jerome": "GB", "Mäni": "GB", "Domi": "DET", "Pädu": "DET"},
            {"Matchup": "Bills (BUF) vs. Dolphins (MIA)", "Andy": "BUF", "Ronny": "BUF", "Bauzzen": "MIA", "Bössi": "BUF", "Jerome": "BUF", "Mäni": "BUF", "Domi": "MIA", "Pädu": "BUF"},
            {"Matchup": "Ravens (BAL) vs. Bengals (CIN)", "Andy": "BAL", "Ronny": "BAL", "Bauzzen": "BAL", "Bössi": "CIN", "Jerome": "BAL", "Mäni": "CIN", "Domi": "BAL", "Pädu": "BAL"}
        ]
        df_demo = pd.DataFrame(demo_games)
        styled_df = df_demo.style.apply(lambda col: [style_team_colors(v) for v in col] if col.name in MITSPIELER else [''] * len(col))
        st.dataframe(styled_df, width="stretch", height=280)
    elif not is_after_thursday_noon:
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
            st.dataframe(styled_real_df, width="stretch")

# --- TAB 9: SPIELPLAN & SCORES ---
with tab9:
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
                            <div class='team-box'>
                                <img src='{g['home_logo']}' width='45'>
                                <span class='team-name {h_win}'>{g['home_team']}</span>
                            </div>
                            <div class='score-badge'>{g['home_score']} : {g['away_score']}</div>
                            <div class='team-box' style='flex-direction: row-reverse;'>
                                <img src='{g['away_logo']}' width='45'>
                                <span class='team-name {a_win}'>{g['away_team']}</span>
                            </div>
                        </div>
                    </div>
                """, unsafe_allow_html=True)

# --- TAB 10: TIPPEN & BONUSTIPPS ---
with tab10:
    st.subheader(f"Tipps abgeben für {active_user}")
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
    if active_user in bottom_two:
        st.warning("🃏 **Catch-Up Joker verfügbar!** Da du aktuell auf den hinteren Plätzen liegst, kannst du für EIN Spiel dieser Woche die doppelte Punkteanzahl (2x) aktivieren.")
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
            st.markdown("<div class='game-card'>", unsafe_allow_html=True)
            col_a, col_vs, col_b = st.columns([2, 1, 2])
            with col_a:
                st.image(game['home_logo'], width=50)
                st.write(f"**{game['home_team']}**")
            with col_vs:
                st.write("VS")
                st.caption(game['status_detail'])
            with col_b:
                st.image(game['away_logo'], width=50)
                st.write(f"**{game['away_team']}**")

            options = [game['home_abbr'], game['away_abbr']]
            current_choice = user_existing_tipps.get(game['id'])
            idx = options.index(current_choice) if current_choice in options else None
            
            selected = st.radio(
                f"Tipp: {game['home_team']} vs {game['away_team']}",
                options, index=idx, key=f"r_{active_user}_{game['id']}", horizontal=True,
                disabled=is_after_thursday_noon
            )
            if selected:
                new_tipps[game['id']] = selected
            st.markdown("</div>", unsafe_allow_html=True)

        if not is_after_thursday_noon:
            if st.form_submit_button("🏈 Tipps & Joker speichern"):
                tipps_db[active_user] = new_tipps
                if active_user in bottom_two:
                    if active_user not in joker_db:
                        joker_db[active_user] = {}
                    joker_db[active_user][str(woche)] = selected_joker_game
                
                if save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
                    st.success(f"✅ **ERFOLGREICH GESPEICHERT!** Alle Tipps für **{active_user}** (Woche {woche}) wurden sicher eingetragen.")
                    st.toast("Tipps erfolgreich gespeichert!", icon="🏈")

    st.markdown("---")
    st.subheader("🎯 Saison-Bonustipps (Je 15 Punkte)")
    u_bonus = bonus_db.get(active_user, {})
    new_b = {}
    with st.form("bonus_form"):
        for idx, q in enumerate(BONUS_QUESTIONS):
            q_key = f"q_{idx}"
            current_val = u_bonus.get(q_key, "")
            new_b[q_key] = st.text_input(q, value=current_val)
        if st.form_submit_button("🎯 Bonustipps speichern"):
            bonus_db[active_user] = new_b
            if save_db(tipps_db, bonus_db, bonus_results, joker_db, comments_db, hosts_db, playoff_db):
                st.success(f"✅ Bonustipps für **{active_user}** wurden gespeichert!")
