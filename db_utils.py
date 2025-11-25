import sqlite3
import pandas as pd
import os

# Default to a temp file, but allows dynamic changes
DB_FILE = "uploaded_db.sqlite"

def set_db_path(path):
    """Updates the global database path."""
    global DB_FILE
    DB_FILE = path

def get_db_connection():
    """Establishes a connection to the SQLite database."""
    try:
        if not os.path.exists(DB_FILE):
            return None
        conn = sqlite3.connect(DB_FILE)
        return conn
    except sqlite3.Error as e:
        print(f"Error connecting to database: {e}")
        return None

def get_all_tables():
    """Returns a list of all table names in the database."""
    conn = get_db_connection()
    if not conn:
        return []
    cursor = conn.cursor()
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = [row[0] for row in cursor.fetchall()]
    conn.close()
    return tables

def get_table_data(table_name, limit=5):
    """Fetches the first few rows of a table for preview."""
    conn = get_db_connection()
    if not conn:
        return pd.DataFrame()
    try:
        df = pd.read_sql_query(f"SELECT * FROM `{table_name}` LIMIT {limit}", conn)
        conn.close()
        return df
    except Exception as e:
        conn.close()
        return pd.DataFrame()

def get_schema_context(schema_file_path=None):
    """
    Builds a rich context for the LLM.
    
    Logic:
    1. If 'schema_file_path' is provided, use that for structure.
    2. If NOT provided, EXTRACT the schema structure from the DB itself (sqlite_master).
    3. ALWAYS add Row Counts and Sample Data (3 rows) for better context.
    """
    conn = get_db_connection()
    if not conn:
        return "Error: Database file not found or invalid."
    
    cursor = conn.cursor()
    
    # --- 1. Base Structure (Extraction Logic) ---
    base_schema = ""
    
    # Option A: User uploaded a .sql file (Use it if available)
    if schema_file_path and os.path.exists(schema_file_path):
        try:
            with open(schema_file_path, "r") as f:
                base_schema = f.read()
            base_schema = "### USER PROVIDED SCHEMA DEFINITION:\n" + base_schema
        except Exception as e:
            base_schema = f"Error reading schema file: {e}"
            
    # Option B: Extract from DB (The "One File" Workflow)
    else:
        cursor.execute("SELECT sql FROM sqlite_master WHERE type='table';")
        create_statements = cursor.fetchall()
        extracted_schema = "\n".join([row[0] for row in create_statements if row[0]])
        base_schema = "### EXTRACTED SCHEMA FROM DB:\n" + extracted_schema
    
    # --- 2. Add Real-Time Stats (Row Counts & Samples) ---
    stats_context = "\n\n### REAL-TIME TABLE STATISTICS & SAMPLES:\n"
    
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table';")
    tables = cursor.fetchall()
    
    for table in tables:
        table_name = table[0]
        
        # Row Count
        try:
            cursor.execute(f"SELECT COUNT(*) FROM `{table_name}`;")
            row_count = cursor.fetchone()[0]
        except:
            row_count = "Unknown"

        # Sample Data
        try:
            df_sample = pd.read_sql_query(f"SELECT * FROM `{table_name}` LIMIT 3", conn)
            sample_str = df_sample.to_string(index=False)
        except:
            sample_str = "No sample data available."

        stats_context += f"""
Table: {table_name}
Total Rows: {row_count}
Sample Data:
{sample_str}
----------------------------------
"""
    
    conn.close()
    
    return f"{base_schema}\n{stats_context}"
        
def run_query(sql_query):
    """Executes the generated SQL query and returns the results as a DataFrame."""
    conn = get_db_connection()
    if not conn:
        return None, "Database connection failed."
    
    try:
        # Basic sanitization
        if not sql_query.strip().upper().startswith("SELECT"):
             conn.close()
             return None, "Safety Error: Only SELECT queries are allowed."
        
        df = pd.read_sql_query(sql_query, conn)
        conn.close()
        return df, None
    except Exception as e:
        conn.close()
        return None, str(e)