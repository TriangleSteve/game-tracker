import sqlitecloud
import streamlit as st

def get_connection():
    return sqlitecloud.connect(st.secrets["sqlite_cloud"]["url"])
