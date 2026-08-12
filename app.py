import streamlit as st
import requests
import json
from datetime import datetime
import pandas as pd
from streamlit_gsheets import GSheetsConnection

# --- SEITEN-KONFIGURATION & STADION-FLUTLICHT DESIGN ---
st.set_page_config(page_title="NFL Tippspiel 2026/27", page_icon="🏈", layout="wide")

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
        margin-bottom: 25px;
    }
    
    /* Karten im helleren Stadium-Contrast Look */
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

    /* FIX FÜR INPUT-SCHRIFTFARBE IN DEN BONUSTIPPS & PASSWÖRTERN */
    .stTextInput input {
        color: #ffffff !important;
        background-color: rgba(15, 23, 42, 0.8) !important;
        border: 1px solid #38bdf8 !important;
        border-radius: 8px !important;
    }
    .stTextInput label {
        color: #f8fafc !important;
        font-weight: 600 !important;
    }
    </style>
""", unsafe_allow_html=True)

# --- PASSWÖRTER & MITSPIELER ---
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

# --- GOOGLE SHEETS VERBINDUNG ---
conn = st.connection("gsheets", type=GSheetsConnection)

def load_db():
    try:
        df = conn.read(ttl=0)
        tipps_db = {}
        bonus_db = {}
        bonus_results = {}
        for idx, row in df.iterrows():
            u = str(row['user'])
            if u in MITSPIELER:
                try: tipps_db[u] = json.loads(str(row['tipps_json']))
                except: tipps_db[u] = {}
                try: bonus_db[u] = json.loads(str(row['bonus_json']))
                except: bonus_db[u] = {}
            elif u == "ADMIN_BONUS_RESULTS":
                try: bonus_results = json.loads(str(row['bonus_json']))
                except: bonus_results = {}
        return tipps_db, bonus_db, bonus_results
    except Exception as e:
        return {u: {} for u in MITSPIELER}, {u: {} for u in MITSPIELER}, {}

def save_db(tipps_db, bonus_db, bonus_results):
    rows = []
    for u in MITSPIELER:
        rows.append({
            "user": u, 
            "tipps_json": json.dumps(tipps_db.get(u, {})),
            "bonus_json": json.dumps(bonus_db.get(u, {}))
        })
    rows.append({
        "user": "ADMIN_BONUS_RESULTS",
        "tipps_json": "{}",
        "bonus_json": json.dumps(bonus_results)
    })
    new_df = pd.DataFrame(rows)
    conn.update(data=new_df)

tipps_db, bonus_db, bonus_results = load_db()

# --- ESPN API ---
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
            'winner_abbr': winner_id,
            'status_detail': comp['status']['type']['shortDetail']
        })
    return games

# --- PUNKTE LOGIK ---
def calculate_scores(all_games, phase="Regular Season"):
    scores = {u: 0 for u in MITSPIELER}
    weekly_hits = {u: 0 for u in MITSPIELER}
    
    multiplier = 1 if phase == "Regular Season" else (2 if phase == "Playoffs" else 3)

    for game in all_games:
        if game['completed'] and game['winner_abbr']:
            for u in MITSPIELER:
                if tipps_db.get(u, {}).get(game['id']) == game['winner_abbr']:
                    scores[u] += 5 * multiplier
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

# --- APP UI ---
st.markdown("<h1 class='main-title'>🏈 NFL TIPPSPIEL 2026/27</h1>", unsafe_allow_html=True)

c1, c2, c3 = st.columns([1, 2, 1])
with c2:
    woche = st.slider("Woche / Spieltag auswählen", min_value=1, max_value=18, value=1)
    phase_choice = "Regular Season" if woche <= 18 else "Playoffs"

nfl_games = get_nfl_games(week_num=woche, season_type=2)
scores, hits = calculate_scores(nfl_games, phase=phase_choice)

# --- PRÜFUNG: DEADLINE ---
now = datetime.now()
week1_deadline = datetime(2026, 9, 3, 12, 0, 0)

if woche == 1:
    is_after_thursday_noon = now >= week1_deadline
else:
    is_after_thursday_noon = (now.weekday() == 3 and now.hour >= 12) or (now.weekday() > 3)

tab1, tab2, tab3, tab4 = st.tabs(["📊 Rangliste", "📋 Tipp-Übersicht (Woche)", "🎯 Bonustipps (bis 02.09.)", "🔒 Tippen (Login)"])

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
                    <span style='font-size: 1.3rem; font-weight: bold;'>{badge} {user}</span>
                    <span style='color: #4ade80; font-weight: bold; margin-left: 10px;'>{fire}</span>
                </div>
                <div style='font-size: 1.5rem; font-weight: 800; color: #38bdf8;'>
                    {score} <span style='font-size: 0.9rem; color: #cbd5e1;'>Pkt</span>
                </div>
            </div>
        """, unsafe_allow_html=True)

# --- TAB 2: TABLEARISCHE UBERSICHT ---
with tab2:
    st.subheader(f"Alle Tipps für Woche {woche}")
    
    if not is_after_thursday_noon:
        st.warning("🔒 Die Tipp-Übersicht für diese Woche wird erst am entsprechenden **Donnerstag um 12:00 Uhr** freigeschaltet!")
    else:
        if not nfl_games:
            st.info("Keine Spiele gefunden.")
        else:
            table_data = []
            for g in nfl_games:
                row = {"Begegnung": g['matchup'], "Status": g['status_detail']}
                for u in MITSPIELER:
                    row[u] = tipps_db.get(u, {}).get(g['id'], "-")
                table_data.append(row)
            
            df_table = pd.DataFrame(table_data)
            st.dataframe(df_table, use_container_width=True)

# --- TAB 3: BONUSTIPPS ---
with tab3:
    st.subheader("🎯 Saison-Bonustipps (Je 15 Punkte)")
    
    deadline = datetime(2026, 9, 2, 23, 59, 59)
    can_edit_bonus = datetime.now() <= deadline
    
    if can_edit_bonus:
        st.info("⏳ Die Bonustipps können bis zum **02.09.2026 um 23:59 Uhr** abgegeben/geändert werden.")
    else:
        st.error("🔒 Die Abgabefrist für die Bonustipps (02.09.2026) ist abgelaufen!")

    user_b_login = st.selectbox("Wähle deinen Namen für Bonustipps:", MITSPIELER, key="bonus_user_select")
    pass_b_login = st.text_input("Passwort zur Verifikation", type="password", key="bonus_pass_input")
    
    if pass_b_login == PASSWORDS.get(user_b_login):
        u_bonus = bonus_db.get(user_b_login, {})
        new_b = {}
        
        with st.form("bonus_form"):
            for idx, q in enumerate(BONUS_QUESTIONS):
                q_key = f"q_{idx}"
                current_val = u_bonus.get(q_key, "")
                new_b[q_key] = st.text_input(q, value=current_val, disabled=not can_edit_bonus)
            
            if can_edit_bonus and st.form_submit_button("🎯 Bonustipps speichern"):
                bonus_db[user_b_login] = new_b
                save_db(tipps_db, bonus_db, bonus_results)
                st.success("Bonustipps erfolgreich gespeichert!")
                st.rerun()
    elif pass_b_login != "":
        st.error("Falsches Passwort.")

    with st.expander("⚙️ Admin-Bereich: Bonustipp-Musterlösung eintragen"):
        admin_pass = st.text_input("Admin Passwort (Nutze dein Paedu Passwort)", type="password", key="admin_pass")
        if admin_pass == PASSWORDS["Pädu"]:
            with st.form("admin_bonus_form"):
                admin_new_res = {}
                for idx, q in enumerate(BONUS_QUESTIONS):
                    q_key = f"q_{idx}"
                    admin_new_res[q_key] = st.text_input(f"Lösung: {q}", value=bonus_results.get(q_key, ""))
                if st.form_submit_button("Musterlösung speichern & Punkte verteilen"):
                    bonus_results = admin_new_res
                    save_db(tipps_db, bonus_db, bonus_results)
                    st.success("Musterlösung gespeichert! Punkte wurden aktualisiert.")
                    st.rerun()

# --- TAB 4: NORMALES TIPPEN ---
with tab4:
    st.subheader("Login & Spieltag tippen")
    
    if is_after_thursday_noon:
        st.error(f"🚨 Die Tippabgabe für Woche {woche} ist GESPERRT!")
    else:
        if woche == 1:
            st.info("⏳ Tippabgabe für Woche 1 offen! Frist: **Donnerstag, 03.09.2026 um 12:00 Uhr**.")
        else:
            st.info(f"⏳ Tippabgabe offen! Deadline für Woche {woche}: Dieser Donnerstag um 12:00 Uhr mittags.")

    col_u, col_p = st.columns(2)
    with col_u: active_user = st.selectbox("Wer bist du?", MITSPIELER)
    with col_p: user_input_pass = st.text_input("Dein Passwort", type="password", key="main_pass")

    if user_input_pass == PASSWORDS.get(active_user):
        st.success(f"Willkommen {active_user}!")
        user_existing_tipps = tipps_db.get(active_user, {})
        new_tipps = user_existing_tipps.copy()

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
                current_choice = user_existing_tipps.get(game['id'], game['home_abbr'])
                idx = options.index(current_choice) if current_choice in options else 0
                
                selected = st.radio(
                    f"Tipp: {game['home_team']} vs {game['away_team']}",
                    options, index=idx, key=f"r_{active_user}_{game['id']}", horizontal=True,
                    disabled=is_after_thursday_noon
                )
                new_tipps[game['id']] = selected
                st.markdown("</div>", unsafe_allow_html=True)

            if not is_after_thursday_noon:
                if st.form_submit_button("🏈 Tipps speichern"):
                    tipps_db[active_user] = new_tipps
                    save_db(tipps_db, bonus_db, bonus_results)
                    st.success("Tipps gespeichert!")
                    st.rerun()
            else:
                st.warning("Das Speichern ist nicht mehr möglich, da die Frist abgelaufen ist.")
