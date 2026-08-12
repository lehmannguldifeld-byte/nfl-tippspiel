import streamlit as st
import requests
import json
from datetime import datetime
from streamlit_gsheets import GSheetsConnection

# --- SEITEN-KONFIGURATION & FANCY NFL STYLING ---
st.set_page_config(page_title="NFL Tippspiel 2026/27", page_icon="🏈", layout="wide")

st.markdown("""
    <style>
    /* Dark NFL-Theme */
    .stApp {
        background-color: #0b0e14;
        color: #f1f5f9;
    }
    .main-title {
        text-align: center;
        font-size: 2.8rem;
        font-weight: 800;
        color: #00d4ff;
        text-shadow: 0 0 12px rgba(0,212,255,0.4);
        margin-bottom: 20px;
    }
    .leaderboard-card {
        background: linear-gradient(135deg, #1e293b 0%, #0f172a 100%);
        border: 1px solid #334155;
        border-radius: 12px;
        padding: 15px 20px;
        margin-bottom: 10px;
        display: flex;
        justify-content: space-between;
        align-items: center;
    }
    .game-card {
        background-color: #1a2332;
        border-radius: 12px;
        padding: 15px;
        border: 1px solid #2d3748;
        margin-bottom: 15px;
    }
    </style>
""", unsafe_allow_html=True)

# --- DIE 8 MITSPIELER ---
MITSPIELER = ["Andy", "Ronny", "Bauzzen", "Bössi", "Jerome", "Mäni", "Domi", "Pädu"]

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

# --- ESPN API: LIVE SPIELE & RESULTATE DER NEUEN SAISON ---
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

    # Bonus: +10 Punkte für 6 Richtige an einem Spieltag
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

tab1, tab2 = st.tabs(["📊 Rangliste", "✏️ Tipps abgeben"])

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
                    <span style='font-size: 1.4rem; font-weight: bold;'>{badge} {user}</span>
                    <span style='color: #22c55e; font-weight: bold; margin-left: 10px;'>{fire}</span>
                </div>
                <div style='font-size: 1.6rem; font-weight: 800; color: #00d4ff;'>
                    {score} <span style='font-size: 0.9rem; color: #94a3b8;'>Pkt</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- TAB 2: TIPPS ABGEBEN ---
with tab2:
    st.subheader("Wähle deinen Namen & tippe die Sieger")
    active_user = st.selectbox("Wer bist du?", MITSPIELER)
    
    user_existing_tipps = all_tipps.get(active_user, {})
    new_tipps = user_existing_tipps.copy()

    with st.form("tipp_form"):
        if not nfl_games:
            st.info("Keine Spiele für diesen Spieltag gefunden.")
        else:
            for game in nfl_games:
                st.markdown(f"<div class='game-card'>", unsafe_allow_html=True)
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
                    f"Dein Tipp für {game['home_team']} vs {game['away_team']}",
                    options,
                    index=idx,
                    key=f"radio_{active_user}_{game['id']}",
                    horizontal=True
                )
                new_tipps[game['id']] = selected
                st.markdown("</div>", unsafe_allow_html=True)

            if st.form_submit_button("🏈 Tipps für Woche speichern"):
                save_user_tipp(active_user, new_tipps)
                st.success("Deine Tipps wurden sicher im Google Sheet gespeichert!")
                st.rerun()
