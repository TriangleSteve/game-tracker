import streamlit as st
import sqlitecloud

# SQLite Cloud connection
def get_connection():
    return sqlitecloud.connect(st.secrets["sqlite_cloud"]["url"])

# Page 1: Home
def home_page():
    st.title("Game Checklist Tracker")

    conn = get_connection()
    cursor = conn.cursor()

    # User login
    username = st.text_input("Enter your username", key="username_input")
    
    if username:
        # Fetch games and instances for the user
        cursor.execute("""
            SELECT i.id, g.name, i.game, i.last_updated 
            FROM instance i 
            JOIN game g ON i.game = g.id 
            WHERE i.username = ?
        """, (username,))
        instances = cursor.fetchall()

        if instances:
            st.subheader("Your Game Instances")
            instance_dict = {f"{g_name} (Last updated: {last_updated})": inst_id for inst_id, g_name, g_id, last_updated in instances}
            selected_instance = st.selectbox("Select an instance", list(instance_dict.keys()))
            if st.button("Load Checklist"):
                st.session_state["instance_id"] = instance_dict[selected_instance]
                st.session_state["username"] = username
                st.experimental_rerun()
        else:
            st.write("No game instances found for this user.")

    # New instance creation
    st.subheader("Start a New Tracker")
    new_username = st.text_input("Enter username for new tracker", key="new_username")
    cursor.execute("SELECT id, name FROM game")
    games = cursor.fetchall()
    game_dict = {g[1]: g[0] for g in games}
    new_game_name = st.selectbox("Select a game", list(game_dict.keys()), key="new_game_select")

    if st.button("Create New Tracker"):
        if new_username and new_game_name:
            new_game_id = game_dict[new_game_name]
            cursor.execute("INSERT INTO instance (game, username) VALUES (?, ?)", (new_game_id, new_username))
            conn.commit()
            cursor.execute("SELECT last_insert_rowid()")
            new_instance_id = cursor.fetchone()[0]

            st.session_state["instance_id"] = new_instance_id
            st.session_state["username"] = new_username
            st.success("New tracker created!")
            st.experimental_rerun()
        else:
            st.warning("Please enter a username and select a game.")

    conn.close()

# Page 2: Checklist
def checklist_page():
    st.title("Game Checklist")

    if "instance_id" not in st.session_state:
        st.warning("Please select an instance from the Home page.")
        return

    instance_id = st.session_state["instance_id"]
    conn = get_connection()
    cursor = conn.cursor()

    # Fetch game info
    cursor.execute("SELECT game FROM instance WHERE id = ?", (instance_id,))
    game_id = cursor.fetchone()[0]

    # Fetch checklist items
    cursor.execute("""
        SELECT c.id, c.name, d.value
        FROM checkbox c
        LEFT JOIN data d ON c.id = d.checkbox_id AND d.instance_id = ?
        WHERE c.game = ?
    """, (instance_id, game_id))
    tasks = cursor.fetchall()

    st.subheader("Checklist")
    checked_state = {}

    for task_id, task_name, checked in tasks:
        checked_state[task_id] = st.checkbox(task_name, value=bool(checked))

    if st.button("Save Checklist"):
        for task_id, checked in checked_state.items():
            cursor.execute("""
                INSERT INTO data (checkbox_id, instance_id, game_id, value)
                VALUES (?, ?, ?, ?)
                ON CONFLICT(checkbox_id, instance_id) DO UPDATE SET value = ?
            """, (task_id, instance_id, game_id, checked, checked))
        conn.commit()
        st.success("Checklist updated!")

    conn.close()

# Page 3: Task Management
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
        cursor.execute("SELECT id, name, region, category, details FROM checkbox WHERE game = ?", (game_id,))
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
                INSERT INTO checkbox (game, name, region, category, details) 
                VALUES (?, ?, ?, ?, ?)
            """, (game_id, new_task_name, new_region, new_category, new_details))
            conn.commit()
            st.success("Task added!")
            st.experimental_rerun()

    conn.close()

# Navigation
st.sidebar.title("Navigation")
page = st.sidebar.radio("Go to", ["Home", "Checklist", "Manage Tasks"])

if page == "Home":
    home_page()
elif page == "Checklist":
    checklist_page()
elif page == "Manage Tasks":
    task_management_page()
