import streamlit as st
import sqlitecloud

# SQLite Cloud connection
def get_connection():
    return sqlitecloud.connect(st.secrets["sqlite_cloud"]["url"])

# Home & Checklist combined
st.title("Game Tracker")

conn = get_connection()
cursor = conn.cursor()

if "instance_id" not in st.session_state:
    # User login
    username = st.text_input("Enter your username", key="username_input")
    
    if username:
        cursor.execute("""
            SELECT i.id, g.name, i.last_updated 
            FROM instance i 
            JOIN game g ON i.game_id = g.id 
            WHERE i.username = ?
            ORDER BY last_updated DESC
        """, (username,))
        instances = cursor.fetchall()

        if instances:
            st.subheader("Your Game Instances")
            instance_dict = {f"{g_name} (Last updated: {last_updated})": inst_id for inst_id, g_name, last_updated in instances}
            selected_instance = st.selectbox("Select an instance", list(instance_dict.keys()))
            if st.button("Load Checklist"):
                st.session_state["instance_id"] = instance_dict[selected_instance]
                st.session_state["username"] = username
                st.rerun()
        else:
            st.write("No game instances found for this user.")

    # New instance creation
    st.subheader("New Tracker")
    new_username = st.text_input("Enter username for new tracker", key="new_username")
    cursor.execute("SELECT id, name FROM game ORDER BY name")
    games = cursor.fetchall()
    game_dict = {g[1]: g[0] for g in games}
    new_game_name = st.selectbox("Select a game", list(game_dict.keys()), key="new_game_select", index=None)

    if st.button("Create New Tracker"):
        if new_username and new_game_name:
            new_game_id = game_dict[new_game_name]
            cursor.execute("INSERT INTO instance (game_id, username) VALUES (?, ?)", (new_game_id, new_username))
            conn.commit()
            cursor.execute("SELECT id FROM instance WHERE username = ? ORDER BY last_updated DESC", (new_username,))
            new_instance_id = cursor.fetchone()[0]
            
            st.session_state["instance_id"] = new_instance_id
            st.session_state["username"] = new_username
            st.success("New tracker created!")
            st.rerun()
        else:
            st.warning("Please enter a username and select a game.")

else:
    # Checklist Page
    instance_id = st.session_state["instance_id"]
    
    cursor.execute("""
        SELECT d.id, c.name, d.checked
        FROM checkbox_data d
        JOIN checkbox c ON c.id = d.checkbox_id 
        WHERE d.instance_id = ?
    """, (instance_id,))
    tasks = cursor.fetchall()

    st.subheader("Checklist")
    checked_state = {}

    for task_id, task_name, checked in tasks:
        checked_state[task_id] = st.checkbox(task_name, value=bool(checked))

    if st.button("Save Checklist"):
        for task_id, checked in checked_state.items():
            cursor.execute("""
                UPDATE checkbox_data
                SET checked = ?
                WHERE id = ?
            """, (checked, task_id))
        conn.commit()
        st.success("Checklist updated!")

conn.close()
