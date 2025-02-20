import sqlitecloud
import streamlit as st
import pandas as pd

def get_connection():
    return sqlitecloud.connect(st.secrets["sqlite_cloud"]["url"])

def upsert_checklist_items():
    # Configuration
    CSV_FILE = "checkbox.csv"
    TABLE_NAME = "checkbox"

    df = pd.read_csv(CSV_FILE)
    conn = get_connection()

    # Upsert function
    for _, row in df.iterrows():
        conn.execute(f'''
        INSERT INTO {TABLE_NAME} (id, name, region, category, details, x, y, game_id, required, sort_order)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
        ON CONFLICT(id) DO UPDATE SET
            name=excluded.name,
            region=excluded.region,
            category=excluded.category,
            details=excluded.details,
            x=excluded.x,
            y=excluded.y,
            game_id=excluded.game_id,
            required=excluded.required,
            sort_order=excluded.sort_order;
        ''', tuple(row))

    # Commit and close
    conn.commit()
    conn.close()

    print("Data upserted successfully!")

if __name__ == '__main__':
    upsert_checklist_items()