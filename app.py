import streamlit as st
import requests
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- SEITEN-KONFIGURATION & HELLER STADIUM-LOOK ---
st.set_page_config(page_title="NFL Tippspiel 2026/27", page_icon="🏈", layout="wide")

st.markdown("""
    <style>
    /* Hintergrund-GIF & Helles Theme */
    .stApp {
        background: linear-gradient(rgba(241, 245, 249, 0.88), rgba(226, 232, 240, 0.92)), 
                    url('https://images.unsplash.com/photo-1566577739112-5180d4bf9390?auto=format&fit=crop&w=1920&q=80');
        background-size: cover;
        background-attachment: fixed;
        color: #0f172a;
    }
    
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 900;
        color: #1e3a8a;
        text-shadow: 1px 1px 2px rgba(255,255,255,0.8);
        margin-bottom: 20px;
    }
    
    /* Helle Leaderboard Karten */
    .leaderboard-card {
        background: #ffffff;
        border-left: 6px solid #2563eb;
        border-radius: 12px;
        padding: 16px 24px;
        margin-bottom: 12px;
        display: flex;
        justify-content: space-between;
        align-items: center;
        box-shadow: 0 4px 12px rgba(0,0,0,0.05);
    }
    
    /* Helle Spiel-Karten */
    .game-card {
        background-color: #ffffff;
        border-radius: 12px;
        padding: 18px;
        border: 1px solid #cbd5e1;
        margin-bottom: 15px;
        box-shadow: 0 2px 8px rgba(0,0,0,0.04);
    }
    </style>
""", unsafe_allow_html=True)

# --- DIE 8 MITSPIELER & IHRE PASSWÖRTER ---
PASSWORDS = {
    "Andy": "andy2026",
    "Ronny": "ronny2026",
    "Bauzzen": "bauzzen2026",
    "Bössi": "boessi2026",
    "Jerome": "jerome2026",
    "Mäni": "maeni2026",
    "Domi": "domi2026",
    "Pädu": "paedu2026"
}
MITSPIELER = list(PASSWORDS.keys())

# --- GOOGLE SHEETS VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_all_tipps():
    try:
        df = conn.read(ttl=0)
        tipps_db = {}
        for idx, row in df.iterrows():
            u = str(row['user'])
            if u in MITSPIELER and row['tipps_json']:
                try:
                    tipps_db[u] = json.loads(str(row['tipps_json']))
                except:
                    tipps_db[u] = {}
        return tipps_db
    except Exception as e:
        return {u: {} for u in MITSPIELER}

def save_user_tipp(user, user_tipps):
    all_tipps = load_all_tipps()
    all_tipps[user] = user_tipps
    
    rows = []
    for u in MITSPIELER:
        u_data = all_tipps.get(u, {})
        rows.append({"user": u, "tipps_json": json.dumps(u_data)})
    
    import pandas as pd
    new_df = pd.DataFrame(rows)
    conn.update(data=new_df)

# --- ESPN API: LIVE SPIELE & RESULTATE ---
@st.cache_data(ttl=300)
def get_nfl_games(week_num=1, season_type=2):
    current_year = datetime.now().year
    url = f"https://site.api.espn.com/apis/site/v2/sports/football/nfl/scoreboard?dates={current_year}&week={week_num}&seasontype={season_type}"
    res = requests.get(url).json()
    
    games = []
    events = res.get('events', [])
    for ev in events:
        comp = ev['competitions'][0]
        t1 = comp['competitors'][0]
        t2 = comp['competitors'][1]
        
        status = comp['status']['type']['completed']
        winner_id = None
        if status:
            winner_id = t1['team']['abbreviation'] if t1.get('winner') else t2['team']['abbreviation']

        games.append({
            'id': str(ev['id']),
            'home_team': t1['team']['shortDisplayName'],
            'home_abbr': t1['team']['abbreviation'],
            'home_logo': t1['team']['logo'],
            'home_score': t1.get('score', '0'),
            'away_team': t2['team']['shortDisplayName'],
            'away_abbr': t2['team']['abbreviation'],
            'away_logo': t2['team']['logo'],
            'away_score': t2.get('score', '0'),
            'completed': status,
            'winner_abbr': winner_id,
            'status_detail': comp['status']['type']['shortDetail']
        })
    return games

# --- PUNKTEBERECHNUNG ---
def calculate_scores(all_games, all_tipps, phase="Regular Season"):
    scores = {u: 0 for u in MITSPIELER}
    weekly_hits = {u: 0 for u in MITSPIELER}
    
    multiplier = 1
    if phase == "Playoffs":
        multiplier = 2
    elif phase == "Super Bowl":
        multiplier = 3

    for game in all_games:
        if game['completed'] and game['winner_abbr']:
            for u in MITSPIELER:
                user_tipp = all_tipps.get(u, {}).get(game['id'])
                if user_tipp == game['winner_abbr']:
                    scores[u] += 5 * multiplier
                    weekly_hits[u] += 1

    for u in MITSPIELER:
        if weekly_hits[u] >= 6:
            scores[u] += 10

    return scores, weekly_hits

# --- APP UI ---
st.markdown("<h1 class='main-title'>🏈 NFL TIPPSPIEL 2026/27</h1>", unsafe_allow_html=True)

# Spieltag Auswahl
c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    woche = st.slider("Woche / Spieltag auswählen", min_value=1, max_value=18, value=1)
    phase_choice = "Regular Season"
    if woche > 18:
        phase_choice = "Playoffs"

# Daten abrufen
nfl_games = get_nfl_games(week_num=woche, season_type=2)
all_tipps = load_all_tipps()
scores, hits = calculate_scores(nfl_games, all_tipps, phase=phase_choice)

tab1, tab2 = st.tabs(["📊 Rangliste", "🔒 Tipps abgeben (Login)"])

# --- TAB 1: RANGLISTE ---
with tab1:
    st.subheader(f"Leaderboard — Woche {woche}")
    sorted_scores = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    
    for rank, (user, score) in enumerate(sorted_scores, 1):
        badge = "🥇" if rank == 1 else ("🥈" if rank == 2 else ("🥉" if rank == 3 else f"#{rank}"))
        fire = " 🔥 ON FIRE (+10 Bonus!)" if hits[user] >= 6 else ""
        
        st.markdown(f"""
            <div class='leaderboard-card'>
                <div>
                    <span style='font-size: 1.3rem; font-weight: bold; color: #1e293b;'>{badge} {user}</span>
                    <span style='color: #16a34a; font-weight: bold; margin-left: 10px;'>{fire}</span>
                </div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #1e3a8a;'>
                    {score} <span style='font-size: 0.9rem; color: #64748b;'>Pkt</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- TAB 2: TIPPS ABGEBEN (MIT PASSWORT-SCHUTZ) ---
with tab2:
    st.subheader("Login & Tippabgabe")
    
    col_user, col_pass = st.columns(2)
    with col_user:
        active_user = st.selectbox("Wer bist du?", MITSPIELER)
    with col_pass:
        user_input_pass = st.text_input("Dein Passwort", type="password")

    # Überprüfung des Passworts
    if user_input_pass == PASSWORDS.get(active_user):
        st.success(f"Willkommen zurück, {active_user}! Du kannst jetzt deine Tipps eintragen.")
        
        user_existing_tipps = all_tipps.get(active_user, {})
        new_tipps = user_existing_tipps.copy()

        with st.form("tipp_form"):
            if not nfl_games:
                st.info("Keine Spiele für diesen Spieltag gefunden.")
            else:
                for game in nfl_games:
                    st.markdown("<div class='game-card'>", unsafe_allow_html=True)
                    col_a, col_vs, col_b = st.columns([2, 1, 2])
                    
                    with col_a:
                        st.image(game['home_logo'], width=50)
                        st.write(f"**{game['home_team']}**")
                        if game['completed']:
                            st.caption(f"Score: {game['home_score']}")

                    with col_vs:
                        st.write("VS")
                        st.caption(game['status_detail'])

                    with col_b:
                        st.image(game['away_logo'], width=50)
                        st.write(f"**{game['away_team']}**")
                        if game['completed']:
                            st.caption(f"Score: {game['away_score']}")

                    # Radio Button für Tipp
                    options = [game['home_abbr'], game['away_abbr']]
                    current_choice = user_existing_tipps.get(game['id'], game['home_abbr'])
                    idx = options.index(current_choice) if current_choice in options else 0
                    
                    selected = st.radio(
                        f"Tipp für {game['home_team']} vs {game['away_team']}",
                        options,
                        index=idx,
                        key=f"radio_{active_user}_{game['id']}",
                        horizontal=True
                    )
                    new_tipps[game['id']] = selected
                    st.markdown("</div>", unsafe_allow_html=True)

                if st.form_submit_button("🏈 Tipps speichern"):
                    save_user_tipp(active_user, new_tipps)
                    st.success("Deine Tipps wurden sicher gespeichert!")
                    st.rerun()
    elif user_input_pass != "":
        st.error("Falsches Passwort! Bitte versuche es erneut.")
    else:
        st.info("Bitte gib dein Passwort ein, um deine Tipps freizuschalten.")
