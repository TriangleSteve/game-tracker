import streamlit as st
from db import *
from datetime import datetime

# Home & Checklist combined
st.title("Game Tracker")

conn = get_connection()

if "instance_id" not in st.session_state:
    # User login
    username = st.text_input("Enter your username", value=st.session_state.get("username", ""), key="username_input")
    
    if username:
        st.session_state["username"] = username
        instances = conn.execute("""
            SELECT i.id, g.name, i.last_updated 
            FROM instance i 
            JOIN game g ON i.game_id = g.id 
            WHERE i.username = ?
            ORDER BY last_updated DESC
        """, (username,)).fetchall()

        if instances:
            st.subheader("Your Game Instances")
            instance_dict = {f"{g_name} (Last updated: {last_updated})": inst_id for inst_id, g_name, last_updated in instances}
            selected_instance = st.selectbox("Select an instance", list(instance_dict.keys()), None)
            if st.button("Load Tracker"):
                st.session_state["instance_id"] = instance_dict[selected_instance]
                st.session_state["username"] = username
                st.rerun()
        else:
            st.write("No game instances found for this user.")

        # New instance creation
        st.subheader("New Tracker")
        games = conn.execute("SELECT id, name FROM game ORDER BY name").fetchall()
        game_dict = {g[1]: g[0] for g in games}
        new_game_name = st.selectbox("Select a game", list(game_dict.keys()), key="new_game_select", index=None)
    
        if st.button("Create New Tracker"):
            if username and new_game_name:
                new_game_id = game_dict[new_game_name]
                conn.execute("INSERT INTO instance (game_id, username) VALUES (?, ?)", (new_game_id, username))
                conn.commit()

                new_instance_id = conn.execute("SELECT last_insert_rowid()").fetchone()[0]
                # conn.execute("SELECT id FROM instance WHERE username = ? ORDER BY last_updated DESC", (username,))
                # new_instance_id = conn.fetchone()[0]
                
                st.session_state["instance_id"] = new_instance_id
                st.session_state["username"] = username
                st.success("New tracker created!")
                st.rerun()
            else:
                st.warning("Please enter a username and select a game.")

else:
    # Checklist Page
    if st.button("Go Back to Tracker Selection"):
        del st.session_state["instance_id"]
        st.rerun()

    instance_id = st.session_state["instance_id"]
    
    tasks = conn.execute("""
        SELECT d.id, c.name, d.checked
        FROM checkbox_data d
        JOIN checkbox c ON c.id = d.checkbox_id 
        WHERE d.instance_id = ?
    """, (instance_id,)).fetchall()

    st.subheader("Checklist")
    checked_state = {}

    for task_id, task_name, checked in tasks:
        checked_state[task_id] = st.checkbox(task_name, value=bool(checked))

    if st.button("Save Checklist"):
        for task_id, checked in checked_state.items():
            conn.execute("""
                UPDATE checkbox_data
                SET checked = ?
                WHERE id = ?
            """, (int(checked), task_id))

        conn.execute("""
            UPDATE instance
            SET last_updated = ?
            WHERE id = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), instance_id))

        conn.commit()
        st.success("Checklist updated!")

conn.close()