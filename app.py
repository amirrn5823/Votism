import streamlit as st
import sqlite3
import pandas as pd
import json
import os
import pycountry
from datetime import datetime

st.set_page_config(
    page_title="Global Voting & AI Insights Platform",
    page_icon="📊",
    layout="wide"
)

DB_FILE = "database.db"

AI_MODELS = [
    "Gemini",
    "ChatGPT",
    "Claude",
    "Grok",
    "Llama (Meta)",
    "DeepSeek",
    "Qwen"
]

COUNTRIES = sorted([country.name for country in pycountry.countries])

AGE_GROUPS = [
    "Under 18",
    "18 to 26",
    "26 to 35",
    "35 to 45",
    "45 to 60",
    "60 and above"
]

FINANCIAL_STATUSES = [
    "Above Average",
    "Approximately Average",
    "Below Average"
]

MARITAL_STATUSES = [
    "Single without children",
    "In a relationship without children",
    "In a relationship with children",
    "Single with children"
]

def get_connection():
    conn = sqlite3.connect(DB_FILE, check_same_thread=False)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            username TEXT PRIMARY KEY,
            password TEXT NOT NULL,
            gender TEXT NOT NULL,
            age_group TEXT,
            country TEXT,
            financial_status TEXT,
            marital_status TEXT,
            ai_model TEXT
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS polls (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            title TEXT NOT NULL,
            poll_date TEXT NOT NULL,
            description TEXT NOT NULL,
            options TEXT NOT NULL
        )
    """)
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS votes (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            poll_id INTEGER NOT NULL,
            username TEXT NOT NULL,
            selected_option TEXT NOT NULL,
            FOREIGN KEY (poll_id) REFERENCES polls (id),
            FOREIGN KEY (username) REFERENCES users (username),
            UNIQUE(poll_id, username)
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

if "logged_in" not in st.session_state:
    st.session_state["logged_in"] = False
if "username" not in st.session_state:
    st.session_state["username"] = None

def get_registered_ai_models():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT ai_model FROM users WHERE gender = 'AI' AND ai_model IS NOT NULL")
    rows = cursor.fetchall()
    conn.close()
    return [row["ai_model"] for row in rows]

def get_user_by_username(username):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM users WHERE username = ?", (username,))
    user = cursor.fetchone()
    conn.close()
    return user

def render_vote_bar(options, counts, total_votes):
    if total_votes == 0:
        st.info("No votes recorded yet for this criteria.")
        return
    for opt in options:
        count = counts.get(opt, 0)
        percentage = (count / total_votes) * 100
        st.write(f"**{opt}**: {count} votes ({percentage:.1f}%)")
        st.progress(int(percentage))

def export_database_json():
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM users")
    users_data = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM polls")
    polls_data = [dict(row) for row in cursor.fetchall()]
    
    cursor.execute("SELECT * FROM votes")
    votes_data = [dict(row) for row in cursor.fetchall()]
    
    conn.close()
    
    export_data = {
        "users": users_data,
        "polls": polls_data,
        "votes": votes_data
    }
    return json.dumps(export_data, indent=4)

def import_database_json(json_str):
    data = json.loads(json_str)
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM votes")
    cursor.execute("DELETE FROM polls")
    cursor.execute("DELETE FROM users")
    
    for u in data.get("users", []):
        cursor.execute("""
            INSERT INTO users (username, password, gender, age_group, country, financial_status, marital_status, ai_model)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
        """, (u["username"], u["password"], u["gender"], u.get("age_group"), u.get("country"), u.get("financial_status"), u.get("marital_status"), u.get("ai_model")))
        
    for p in data.get("polls", []):
        cursor.execute("""
            INSERT INTO polls (id, title, poll_date, description, options)
            VALUES (?, ?, ?, ?, ?)
        """, (p["id"], p["title"], p["poll_date"], p["description"], p["options"]))
        
    for v in data.get("votes", []):
        cursor.execute("""
            INSERT INTO votes (poll_id, username, selected_option)
            VALUES (?, ?, ?)
        """, (v["poll_id"], v["username"], v["selected_option"]))
        
    conn.commit()
    conn.close()

st.sidebar.title("Navigation & Account")
menu_options = ["Home", "Auth (Login / Register)", "Polls Ecosystem"]

if st.session_state["logged_in"] and st.session_state["username"] == "amir":
    menu_options.extend(["Poll Control Panel", "Database Backup Panel"])

choice = st.sidebar.radio("Select Menu", menu_options)

if choice == "Home":
    if os.path.exists("profile.jpg"):
        st.image("profile.jpg", use_container_width=True)

    st.markdown("""
Welcome to the Votism platform! Here, we will regularly host engaging polls centered on "gray-area" ethical issues. By creating a profile and providing a few basic details, you can participate in these polls and view the results in real time. You can also explore detailed breakdowns based on various categories, as well as insights from different Ai models.

Be sure to subscribe our YouTube channel.

Let’s get to know the world better.
""")
    
    st.markdown(
        '<p><a href="https://www.youtube.com/@amirrn5823" target="_blank"><button style="background-color: #FF0000; color: white; padding: 10px 20px; border: none; border-radius: 5px; cursor: pointer; font-size: 16px; font-weight: bold;">Subscribe to YouTube Channel</button></a></p>',
        unsafe_allow_html=True
    )

elif choice == "Auth (Login / Register)":
    st.header("Authentication & Profile Setup")
    
    if st.session_state["logged_in"]:
        st.success(f"Currently logged in as: **{st.session_state['username']}**")
        if st.button("Logout"):
            st.session_state["logged_in"] = False
            st.session_state["username"] = None
            st.rerun()
    else:
        auth_mode = st.radio("Choose Mode", ["Login", "Register"])
        
        if auth_mode == "Login":
            st.subheader("User Login")
            login_user = st.text_input("Username")
            login_pass = st.text_input("Password", type="password")
            
            if st.button("Login"):
                user = get_user_by_username(login_user)
                if user and user["password"] == login_pass:
                    st.session_state["logged_in"] = True
                    st.session_state["username"] = login_user
                    st.success(f"Welcome back, {login_user}!")
                    st.rerun()
                else:
                    st.error("Invalid username or password.")
                    
        elif auth_mode == "Register":
            st.subheader("Create New Account")
            
            reg_username = st.text_input("Choose Username")
            reg_password = st.text_input("Choose Password", type="password")
            
            registered_ais = get_registered_ai_models()
            available_ais = [m for m in AI_MODELS if m not in registered_ais]
            
            gender_options = ["Male", "Female"]
            if len(available_ais) > 0:
                gender_options.append("AI")
                
            selected_gender = st.selectbox("Select Profile Type / Gender", gender_options)
            
            reg_age = None
            reg_country = None
            reg_financial = None
            reg_marital = None
            selected_ai = None
            
            if selected_gender in ["Male", "Female"]:
                reg_age = st.selectbox("Age Group", AGE_GROUPS)
                reg_country = st.selectbox("Country", COUNTRIES)
                reg_financial = st.selectbox("Financial Status Relative to Community", FINANCIAL_STATUSES)
                reg_marital = st.selectbox("Marital / Relationship Status", MARITAL_STATUSES)
            else:
                selected_ai = st.selectbox("Select AI Model", available_ais)
                
            if st.button("Register Account"):
                if not reg_username.strip():
                    st.error("Username cannot be empty.")
                elif not reg_password.strip():
                    st.error("Password cannot be empty.")
                else:
                    existing_user = get_user_by_username(reg_username.strip())
                    if existing_user:
                        st.error("Username already taken! Please choose another username.")
                    else:
                        conn = get_connection()
                        cursor = conn.cursor()
                        cursor.execute("""
                            INSERT INTO users (username, password, gender, age_group, country, financial_status, marital_status, ai_model)
                            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                        """, (reg_username.strip(), reg_password, selected_gender, reg_age, reg_country, reg_financial, reg_marital, selected_ai))
                        conn.commit()
                        conn.close()
                        st.success("Registration successful! You can now log in.")

elif choice == "Polls Ecosystem":
    st.header("Global Polls & Demographic Insights")
    
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM polls ORDER BY id DESC")
    polls = cursor.fetchall()
    conn.close()
    
    if not polls:
        st.info("No active polls available yet.")
    else:
        poll_titles = [f"{p['id']}: {p['title']}" for p in polls]
        selected_poll_str = st.selectbox("Select Poll to View or Vote", poll_titles)
        selected_poll_id = int(selected_poll_str.split(":")[0])
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM polls WHERE id = ?", (selected_poll_id,))
        poll = cursor.fetchone()
        conn.close()
        
        st.markdown(f"### {poll['title']}")
        st.caption(f"Date: {poll['poll_date']}")
        st.write(poll["description"])
        
        options = json.loads(poll["options"])
        
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM votes WHERE poll_id = ?", (selected_poll_id,))
        all_votes = cursor.fetchall()
        conn.close()
        
        user_voted = False
        user_vote_option = None
        current_username = st.session_state.get("username")
        
        if st.session_state["logged_in"]:
            for v in all_votes:
                if v["username"] == current_username:
                    user_voted = True
                    user_vote_option = v["selected_option"]
                    break
                    
        st.divider()
        
        if st.session_state["logged_in"] and not user_voted:
            st.subheader("Cast Your Vote")
            selected_choice = st.radio("Choose your option:", options)
            if st.button("Submit Vote"):
                conn = get_connection()
                cursor = conn.cursor()
                cursor.execute("""
                    INSERT INTO votes (poll_id, username, selected_option)
                    VALUES (?, ?, ?)
                """, (selected_poll_id, current_username, selected_choice))
                conn.commit()
                conn.close()
                st.success("Your vote has been recorded!")
                st.rerun()
        elif not st.session_state["logged_in"]:
            st.warning("Please log in to participate in voting and unlock segmented analytics.")
        else:
            st.success(f"You voted for: **{user_vote_option}**")

        st.divider()
        st.subheader("Results & Analytics")
        
        total_vote_count = len(all_votes)
        overall_counts = {opt: 0 for opt in options}
        for v in all_votes:
            if v["selected_option"] in overall_counts:
                overall_counts[v["selected_option"]] += 1
                
        st.markdown("#### Overall Results (All Votes)")
        render_vote_bar(options, overall_counts, total_vote_count)
        
        if st.session_state["logged_in"] and user_voted:
            st.divider()
            st.subheader("Detailed Demographic & AI Breakdowns")
            
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("""
                SELECT votes.selected_option, users.gender, users.age_group, users.country, 
                       users.financial_status, users.marital_status, users.ai_model, users.username
                FROM votes
                JOIN users ON votes.username = users.username
                WHERE votes.poll_id = ?
            """, (selected_poll_id,))
            detailed_votes = [dict(row) for row in cursor.fetchall()]
            conn.close()
            
            human_votes = [v for v in detailed_votes if v["gender"] != "AI"]
            ai_votes = [v for v in detailed_votes if v["gender"] == "AI"]
            
            col1, col2 = st.columns(2)
            with col1:
                st.markdown("#### Human Votes")
                h_counts = {opt: 0 for opt in options}
                for v in human_votes:
                    if v["selected_option"] in h_counts:
                        h_counts[v["selected_option"]] += 1
                render_vote_bar(options, h_counts, len(human_votes))
                
            with col2:
                st.markdown("#### AI Models Average Votes")
                ai_counts = {opt: 0 for opt in options}
                for v in ai_votes:
                    if v["selected_option"] in ai_counts:
                        ai_counts[v["selected_option"]] += 1
                render_vote_bar(options, ai_counts, len(ai_votes))
                
            st.divider()
            filter_type = st.selectbox(
                "Filter Specific Demographic Category",
                ["Gender", "Age Group", "Country", "Financial Status", "Marital Status", "AIs Detailed Votes"]
            )
            
            if filter_type == "Gender":
                g_selected = st.radio("Select Gender Filter", ["Male", "Female"])
                filtered = [v for v in human_votes if v["gender"] == g_selected]
                f_counts = {opt: 0 for opt in options}
                for v in filtered:
                    f_counts[v["selected_option"]] += 1
                st.markdown(f"##### Results for Gender: {g_selected}")
                render_vote_bar(options, f_counts, len(filtered))
                
            elif filter_type == "Age Group":
                a_selected = st.selectbox("Select Age Filter", AGE_GROUPS)
                filtered = [v for v in human_votes if v["age_group"] == a_selected]
                f_counts = {opt: 0 for opt in options}
                for v in filtered:
                    f_counts[v["selected_option"]] += 1
                st.markdown(f"##### Results for Age Group: {a_selected}")
                render_vote_bar(options, f_counts, len(filtered))
                
            elif filter_type == "Country":
                c_selected = st.selectbox("Select Country Filter", COUNTRIES)
                filtered = [v for v in human_votes if v["country"] == c_selected]
                f_counts = {opt: 0 for opt in options}
                for v in filtered:
                    f_counts[v["selected_option"]] += 1
                st.markdown(f"##### Results for Country: {c_selected}")
                render_vote_bar(options, f_counts, len(filtered))
                
            elif filter_type == "Financial Status":
                fin_selected = st.selectbox("Select Financial Filter", FINANCIAL_STATUSES)
                filtered = [v for v in human_votes if v["financial_status"] == fin_selected]
                f_counts = {opt: 0 for opt in options}
                for v in filtered:
                    f_counts[v["selected_option"]] += 1
                st.markdown(f"##### Results for Financial Status: {fin_selected}")
                render_vote_bar(options, f_counts, len(filtered))
                
            elif filter_type == "Marital Status":
                m_selected = st.selectbox("Select Marital Filter", MARITAL_STATUSES)
                filtered = [v for v in human_votes if v["marital_status"] == m_selected]
                f_counts = {opt: 0 for opt in options}
                for v in filtered:
                    f_counts[v["selected_option"]] += 1
                st.markdown(f"##### Results for Marital Status: {m_selected}")
                render_vote_bar(options, f_counts, len(filtered))
                
            elif filter_type == "AIs Detailed Votes":
                st.markdown("##### Individual AI Votes")
                if not ai_votes:
                    st.info("No AI models have voted in this poll yet.")
                else:
                    for v in ai_votes:
                        st.write(f"🤖 **{v['ai_model']}** voted for: **{v['selected_option']}**")

elif choice == "Poll Control Panel":
    if not (st.session_state["logged_in"] and st.session_state["username"] == "amir"):
        st.error("Access restricted to admin only.")
    else:
        st.header("Admin Control Panel: Manage Polls")
        
        tab1, tab2 = st.tabs(["Create New Poll", "Manage Existing Polls"])
        
        with tab1:
            st.subheader("Add Poll")
            new_title = st.text_input("Poll Title")
            new_date = st.date_input("Poll Date", datetime.now()).strftime("%Y-%m-%d")
            new_desc = st.text_area("Poll Narrative / Description")
            options_count = st.number_input("Number of Options", min_value=2, max_value=10, value=3)
            
            new_options = []
            for i in range(int(options_count)):
                opt = st.text_input(f"Option {i+1}", key=f"new_opt_{i}")
                new_options.append(opt)
                
            if st.button("Create Poll"):
                if not new_title.strip() or not new_desc.strip():
                    st.error("Title and Description are required.")
                elif any(not o.strip() for o in new_options):
                    st.error("All option fields must be filled.")
                else:
                    conn = get_connection()
                    cursor = conn.cursor()
                    cursor.execute("""
                        INSERT INTO polls (title, poll_date, description, options)
                        VALUES (?, ?, ?, ?)
                    """, (new_title.strip(), new_date, new_desc.strip(), json.dumps(new_options)))
                    conn.commit()
                    conn.close()
                    st.success("Poll successfully created!")
                    st.rerun()
                    
        with tab2:
            st.subheader("Existing Polls")
            conn = get_connection()
            cursor = conn.cursor()
            cursor.execute("SELECT * FROM polls ORDER BY id DESC")
            all_polls = cursor.fetchall()
            conn.close()
            
            if not all_polls:
                st.info("No polls found.")
            else:
                for p in all_polls:
                    with st.expander(f"ID {p['id']}: {p['title']}"):
                        edit_title = st.text_input("Title", p['title'], key=f"edit_t_{p['id']}")
                        edit_date = st.text_input("Date", p['poll_date'], key=f"edit_d_{p['id']}")
                        edit_desc = st.text_area("Description", p['description'], key=f"edit_desc_{p['id']}")
                        
                        existing_opts = json.loads(p['options'])
                        edit_opts_str = st.text_area("Options (JSON Array)", json.dumps(existing_opts), key=f"edit_opt_{p['id']}")
                        
                        col_a, col_b = st.columns(2)
                        with col_a:
                            if st.button("Update Poll", key=f"btn_upd_{p['id']}"):
                                try:
                                    parsed_opts = json.loads(edit_opts_str)
                                    conn = get_connection()
                                    cursor = conn.cursor()
                                    cursor.execute("""
                                        UPDATE polls SET title = ?, poll_date = ?, description = ?, options = ?
                                        WHERE id = ?
                                    """, (edit_title, edit_date, edit_desc, json.dumps(parsed_opts), p['id']))
                                    conn.commit()
                                    conn.close()
                                    st.success("Poll updated!")
                                    st.rerun()
                                except Exception as e:
                                    st.error(f"Invalid options JSON format: {e}")
                                    
                        with col_b:
                            if st.button("Delete Poll", key=f"btn_del_{p['id']}"):
                                conn = get_connection()
                                cursor = conn.cursor()
                                cursor.execute("DELETE FROM votes WHERE poll_id = ?", (p['id'],))
                                cursor.execute("DELETE FROM polls WHERE id = ?", (p['id'],))
                                conn.commit()
                                conn.close()
                                st.warning("Poll and associated votes deleted.")
                                st.rerun()

elif choice == "Database Backup Panel":
    if not (st.session_state["logged_in"] and st.session_state["username"] == "amir"):
        st.error("Access restricted to admin only.")
    else:
        st.header("Admin Database Backup & Restore")
        
        st.subheader("1. Download Full Database Export")
        json_data = export_database_json()
        st.download_button(
            label="Download JSON Backup File",
            data=json_data,
            file_name="database_backup.json",
            mime="application/json"
        )
        
        st.divider()
        st.subheader("2. Upload & Restore Database")
        uploaded_file = st.file_uploader("Upload Backup JSON File", type=["json"])
        
        if uploaded_file is not None:
            if st.button("Restore Database From File"):
                try:
                    content = uploaded_file.read().decode("utf-8")
                    import_database_json(content)
                    st.success("Database restored successfully from backup!")
                    st.rerun()
                except Exception as e:
                    st.error(f"Failed to restore database: {e}")
