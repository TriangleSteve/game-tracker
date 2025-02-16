import streamlit as st
import sqlite3

# Database connection
DB_PATH = "your_sqlitecloud_connection_string_here"

def get_connection():
    return sqlite3.connect(DB_PATH, check_same_thread=False)

# Page 1: Checklist
def checklist_page():
    st.title("Game Checklist")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Select game
    cursor.execute("SELECT id, name FROM game")
    games = cursor.fetchall()
    game_dict = {g[1]: g[0] for g in games}
    game_name = st.selectbox("Select a game", list(game_dict.keys()))
    game_id = game_dict[game_name] if game_name else None
    
    # Select instance
    cursor.execute("SELECT id, username FROM instance WHERE game_id = ?", (game_id,))
    instances = cursor.fetchall()
    instance_dict = {i[1]: i[0] for i in instances}
    instance_name = st.selectbox("Select an instance", list(instance_dict.keys()))
    instance_id = instance_dict[instance_name] if instance_name else None
    
    if game_id and instance_id:
        cursor.execute("""
            SELECT c.id, c.name, d.checked 
            FROM checkbox c 
            LEFT JOIN checkbox_data d ON c.id = d.checkbox_id AND d.instance_id = ?
            WHERE c.game_id = ?
        """, (instance_id, game_id))
        tasks = cursor.fetchall()
        
        st.subheader("Checklist")
        checked_state = {}
        for task_id, task_name, checked in tasks:
            checked_state[task_id] = st.checkbox(task_name, value=bool(checked))
        
        if st.button("Save Checklist"):
            for task_id, checked in checked_state.items():
                cursor.execute("""
                    INSERT INTO checkbox_data (checkbox_id, instance_id, checked) 
                    VALUES (?, ?, ?) 
                    ON CONFLICT(checkbox_id, instance_id) DO UPDATE SET checked = ?
                """, (task_id, instance_id, checked, checked))
            conn.commit()
            st.success("Checklist updated!")
    
    conn.close()

# Page 2: Task Management
def task_management_page():
    st.title("Manage Game Checklist Items")
    
    conn = get_connection()
    cursor = conn.cursor()
    
    # Select game
    cursor.execute("SELECT id, name FROM game")
    games = cursor.fetchall()
    game_dict = {g[1]: g[0] for g in games}
    game_name = st.selectbox("Select a game", list(game_dict.keys()))
    game_id = game_dict[game_name] if game_name else None
    
    if game_id:
        # Fetch tasks
        cursor.execute("SELECT id, name, region, category, details FROM checkbox WHERE game_id = ?", (game_id,))
        tasks = cursor.fetchall()
        
        st.subheader("Existing Tasks")
        for task in tasks:
            task_id, task_name, region, category, details = task
            st.write(f"**{task_name}** (Region: {region}, Category: {category})")
            if st.button(f"Delete {task_name}"):
                cursor.execute("DELETE FROM checkbox WHERE id = ?", (task_id,))
                conn.commit()
                st.experimental_rerun()
        
        # Add new task
        st.subheader("Add New Task")
        new_task_name = st.text_input("Task Name")
        new_region = st.text_input("Region")
        new_category = st.text_input("Category")
        new_details = st.text_area("Details")
        
        if st.button("Add Task"):
            cursor.execute("""
                INSERT INTO checkbox (game_id, name, region, category, details) 
                VALUES (?, ?, ?, ?, ?)
            """, (game_id, new_task_name, new_region, new_category, new_details))
            conn.commit()
            st.success("Task added!")
            st.experimental_rerun()
    
    conn.close()

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Checklist", "Manage Tasks"])

if page == "Checklist":
    checklist_page()
elif page == "Manage Tasks":
    task_management_page()
