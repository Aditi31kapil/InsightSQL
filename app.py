import streamlit as st
import speech_recognition as sr
from deep_translator import GoogleTranslator
import plotly.express as px
import pandas as pd
import time
import os

# Custom Imports
# Ensure these functions exist in your local db_utils.py and llm_api.py files
from db_utils import get_schema_context, run_query, get_all_tables, get_table_data, set_db_path
from llm_api import get_sql_from_llm, get_plot_code_from_llm, get_summary_from_llm

# --- PAGE CONFIG ---
st.set_page_config(page_title="InsightSQL", layout="wide", page_icon="🌍")

# --- SESSION STATE ---
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "👋 Hello! Please upload your **SQLite Database** and **Schema File** in the sidebar to get started."}
    ]

# --- SIDEBAR: DATA UPLOAD ---
with st.sidebar:
    st.header("📂 Data Source")
    st.caption("Upload your files to analyze.")
    
    # 1. Upload SQLite File
    db_file = st.file_uploader("Upload Database (.sqlite)", type=["sqlite", "db"])
    
    # MADE OPTIONAL
    schema_file = st.file_uploader("Upload Schema (.sql) [Optional]", type=["sql"])
    
    if db_file:
        with open("uploaded_db.sqlite", "wb") as f: f.write(db_file.getbuffer())
        set_db_path("uploaded_db.sqlite")
        
        if schema_file:
            with open("uploaded_schema.sql", "wb") as f: f.write(schema_file.getbuffer())
            st.success("✅ DB & Schema Loaded!")
        else:
            # Clean up old schema if user switched to 'One File' mode
            if os.path.exists("uploaded_schema.sql"): os.remove("uploaded_schema.sql")
            st.success("✅ DB Loaded! (Schema auto-extracted)")

    st.header("2. Input Method")
    input_method = st.radio("Choose Input:", ["Text Input", "Voice (Microphone)"])
    
    # --- SIDEBAR TABLE VIEWER ---
    # Check existence on disk so it persists even if file_uploader state resets slightly
    if os.path.exists("uploaded_db.sqlite"):
        st.divider()
        st.header("3. Table Inspector")
        all_tables_sidebar = get_all_tables()
        
        if all_tables_sidebar:
            selected_table_sb = st.selectbox("Select Table to View:", all_tables_sidebar)
            if selected_table_sb:
                st.caption(f"Previewing: {selected_table_sb}")
                df_preview_sb = get_table_data(selected_table_sb, limit=5)
                st.dataframe(df_preview_sb, use_container_width=True)
        else:
            st.info("No tables found in database.")

# --- HELPER FUNCTIONS ---

def record_voice():
    """Handles microphone recording with extended timing."""
    r = sr.Recognizer()
    with sr.Microphone() as source:
        status_placeholder = st.empty()
        status_placeholder.info("🎤 Adjusting for noise...")
        r.adjust_for_ambient_noise(source, duration=1)
        r.pause_threshold = 2.0 
        status_placeholder.info("🎤 Listening... (Max 30s)")
        try:
            audio = r.listen(source, timeout=10, phrase_time_limit=30)
            status_placeholder.success("Processing...")
            time.sleep(0.5)
            status_placeholder.empty()
            return r.recognize_google(audio)
        except Exception as e:
            status_placeholder.error(f"Error: {e}")
        return None

def process_query(user_input):
    """Main Analysis Pipeline"""
    
    # Check if files are ready
    if not os.path.exists("uploaded_db.sqlite"):
        return {"role": "assistant", "content": "🚨 Please upload a Database file (.sqlite) first!"}

    # 1. Translate
    with st.status("🧠 AI Analyst Thinking...", expanded=True) as status:
        status.write("🌐 Translating...")
        translated_text = GoogleTranslator(source='auto', target='en').translate(user_input)
        
        # 2. Context & SQL
        status.write("📖 Reading Schema & Generating SQL...")
        
        # Determine which schema source to use
        schema_path = "uploaded_schema.sql" if os.path.exists("uploaded_schema.sql") else None
        full_context = get_schema_context(schema_path)
        
        generated_sql = get_sql_from_llm(full_context, translated_text, st.session_state.messages)
        
        response_payload = {
            "role": "assistant", 
            "content": "", 
            "translated_query": translated_text,
            "sql": generated_sql
        }

        # 3. Execution
        if "SELECT" in generated_sql.upper():
            status.write("⚡ Executing Query...")
            df_result, error = run_query(generated_sql)
            
            if error:
                response_payload["content"] = f"❌ SQL Error: {error}"
                status.update(label="Failed", state="error")
            else:
                response_payload["data"] = df_result
                
                # 4. Chart
                if not df_result.empty and len(df_result) > 1:
                    status.write("📊 Checking for visualizations...")
                    try:
                        cols = list(df_result.columns)
                        plot_code = get_plot_code_from_llm(translated_text, cols)
                        if "NONE" not in plot_code and "fig" in plot_code:
                            local_vars = {"df_result": df_result, "px": px}
                            exec(plot_code, globals(), local_vars)
                            fig = local_vars.get('fig')
                            if fig:
                                response_payload["chart"] = fig
                    except Exception:
                        pass # Chart failure shouldn't crash app

                # 5. Summary
                status.write("📝 Writing Analysis...")
                if not df_result.empty:
                    data_snippet = df_result.head(10).to_string()
                    summary = get_summary_from_llm(translated_text, data_snippet)
                    response_payload["content"] = summary
                else:
                    response_payload["content"] = "Query executed successfully but returned 0 results."
                
                status.update(label="Complete!", state="complete", expanded=False)
        else:
            response_payload["content"] = "Could not generate a valid SQL query. Please try rephrasing."
            status.update(label="Invalid Query", state="error")
            
        return response_payload

# --- MAIN INTERFACE ---

st.title("🌍 Multilingual AI SQL Analyst")

# 1. Chat History
for msg in st.session_state.messages:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if "translated_query" in msg: st.caption(f"Translated: *'{msg['translated_query']}'*")
        if "sql" in msg:
            with st.expander("View SQL"): st.code(msg["sql"], language="sql")
        if "data" in msg:
            with st.expander("View Data"): st.dataframe(msg["data"])
        if "chart" in msg: st.plotly_chart(msg["chart"], use_container_width=True)

# 2. Input
user_input = None
if input_method == "Text Input":
    user_input = st.chat_input("Ask a question...")
elif input_method == "Voice (Microphone)":
    with st.container():
        col1, _ = st.columns([1, 8])
        with col1:
            if st.button("🎤 Record"):
                user_input = record_voice()

# 3. Process
if user_input:
    st.session_state.messages.append({"role": "user", "content": user_input})
    with st.chat_message("user"): st.markdown(user_input)

    with st.chat_message("assistant"):
        response_data = process_query(user_input)
        st.markdown(response_data["content"])
        # Render dynamic elements immediately
        if "sql" in response_data:
             with st.expander("View SQL"): st.code(response_data["sql"], language="sql")
        if "data" in response_data:
             with st.expander("View Data"): st.dataframe(response_data["data"])
        if "chart" in response_data: st.plotly_chart(response_data["chart"], use_container_width=True)
            
    st.session_state.messages.append(response_data)