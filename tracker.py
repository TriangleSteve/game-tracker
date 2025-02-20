import streamlit as st
import pandas as pd
from db import *
from datetime import datetime
import json

# Home & Checklist combined
st.title("Game Tracker")

conn = get_connection()


hide_streamlit_style = """
            <style>
            #MainMenu {visibility: hidden;}
            header {visibility: hidden;}
            footer {visibility: hidden;}
            </style>
            """
st.markdown(hide_streamlit_style, unsafe_allow_html=True)
st.markdown("""
        <style>
               .block-container {
                    padding-top: 1rem;
                    padding-bottom: 0rem;
                }
        </style>
        """, unsafe_allow_html=True)

if "instance_id" not in st.session_state:
    # User login
    username = st.text_input("Enter username", value=st.session_state.get("username", ""), key="username_input")
    
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
            st.subheader("Your Trackers")
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
    
        if st.button("Create Tracker"):
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
    
    # Load filter preferences from instance table
    instance_query = "SELECT hide_completed, selected_categories FROM instance WHERE id = ?"
    instance_settings = conn.execute(instance_query, (instance_id,)).fetchone()

    # Default settings if not set yet
    hide_completed = bool(instance_settings[0]) if instance_settings else False
    selected_categories = json.loads(instance_settings[1]) if instance_settings and instance_settings[1] else []


    # Load all checklist data once
    query = """
        SELECT d.id AS task_id, c.name AS task_name, c.region, c.category, c.details, d.checked
        FROM checkbox_data d
        JOIN checkbox c ON c.id = d.checkbox_id 
        WHERE d.instance_id = ?
        ORDER BY c.sort_order
    """
    df = pd.read_sql(query, conn, params=(instance_id,))

    # Get unique categories for filtering
    categories = df["category"].unique().tolist()
    with st.expander('Filters', expanded=False, icon=":material/filter_list:"):
        selected_categories = st.multiselect("Category", categories, default=categories)
        hide_completed = st.checkbox("Hide Completed", value=hide_completed, key="hide_filter")

    # Apply filters in-memory
    filtered_df = df[df["category"].isin(selected_categories)]
    if hide_completed:
        filtered_df = filtered_df[filtered_df["checked"] == 0]

    # Group tasks by region
    task_groups = filtered_df.groupby("region")

    checked_state = {}

    # Display tasks grouped by region
    for region, tasks in task_groups:
        with st.expander(region, expanded=True):  # Collapsible sections for each region
            for _, row in tasks.iterrows():
                label = f'[{row["category"]}] {row["task_name"]}'
                checked_state[row["task_id"]] = st.checkbox(label, value=bool(row["checked"]))

    if st.button("Save Checklist"):
        modified_tasks = [(int(checked), task_id) for task_id, checked in checked_state.items()]
        
        # Only update rows that have changed
        for checked, task_id in modified_tasks:
            if df.loc[df["task_id"] == task_id, "checked"].values[0] != checked:
                conn.execute("UPDATE checkbox_data SET checked = ? WHERE id = ?", (checked, task_id))

        conn.execute("""
        UPDATE instance 
        SET last_updated = ?, hide_completed = ?, selected_categories = ?
        WHERE id = ?
        """, (datetime.now().strftime('%Y-%m-%d %H:%M:%S'), int(hide_completed), json.dumps(selected_categories), instance_id))

        conn.commit()
        st.success("Checklist updated!")

        st.rerun()

conn.close()
