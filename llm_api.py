import requests
import json
import re
import os
from dotenv import load_dotenv
load_dotenv()
# REPLACE WITH YOUR ACTUAL KEY
# OPENROUTER_API_KEY =  os.getenv("OPEN_ROUTER_API_KEY")
# YOUR_SITE_URL = "http://localhost:8501"
# YOUR_SITE_NAME = "Ecommerce SQL Bot"
API_KEY = os.getenv("GROQ_API_KEY")

# 2. We use Groq's OpenAI-compatible endpoint
API_URL = "https://api.groq.com/openai/v1/chat/completions"

# 3. Model Name (Groq hosts Llama 3.3 70B for free)
MODEL_NAME = "llama-3.3-70b-versatile" 
# ==========================================

def call_llm(messages, temperature=0.1):
    """Helper function to call Groq API."""
    headers = {
        "Authorization": f"Bearer {API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "model": MODEL_NAME,
        "messages": messages,
        "temperature": temperature,
        "max_tokens": 1024
    }
    try:
        response = requests.post(API_URL, headers=headers, data=json.dumps(payload))
        
        # Error Handling
        if response.status_code != 200:
            return f"Error {response.status_code}: {response.text}"
            
        return response.json()['choices'][0]['message']['content']
    except Exception as e:
        return f"Request Failed: {str(e)}"

def get_sql_from_llm(schema_context, user_question, chat_history=None):
    """
    Generates SQL using Chain-of-Thought (Schema Linking).
    """
    system_prompt = f"""
    You are an expert Data Scientist. 
    
    ### Database Schema:
    {schema_context}
    
    ### TASK:
    1. **Analyze the Request:** Understand what the user wants (e.g., "most products" usually means count of orders).
    2. **Schema Linking:** Explicitly list which tables and columns are needed.
       - Example: "User asked for 'customers'. I need `Customers` table."
       - Example: "User asked for 'products bought'. I need to count `customer_id` in `Orders` table."
    3. **Generate SQL:** Write the SQLite query inside ```sql ... ``` tags.

    ### CRITICAL RULES:
    1. **Limits:** Choose the `LIMIT` dynamically based on the user's request. Do not default to `LIMIT 1` for ranking queries (like "most" or "top") unless explicitly asked; prefer showing a few extra results (e.g., `LIMIT 5`) to handle potential ties.
    2. **Ambiguity:** If "quantity" is not in `Order_Items`, count the rows in `Orders` or `Order_Items`.
    3. **Counts:** To find "most products" or "most orders", always use `COUNT(customer_id)` in the `Orders` table.
    4. **ID Handling:** Never sum IDs.
    
    ### OUTPUT FORMAT:
    Reasoning:
    - Intent: [Explain user intent]
    - Columns: [List table.column mappings]
    
    SQL:
    ```sql
    SELECT ...
    ```
    """
    
    messages = [{"role": "system", "content": system_prompt}]
    
    # Inject History (Last 4 turns)
    if chat_history:
        for msg in chat_history[-4:]:
            role = "user" if msg["role"] == "user" else "assistant"
            content = msg.get("translated_query", msg["content"]) 
            if role == "assistant" and "sql" in msg:
                content += f"\n(Context: Previous SQL generated: {msg['sql']})"
            messages.append({"role": role, "content": content})

    messages.append({"role": "user", "content": user_question})
    
    content = call_llm(messages)
    
    # --- SMART PARSING ---
    # The model now outputs text + SQL. We must extract ONLY the SQL block.
    match = re.search(r'```sql\s*(.*?)\s*```', content, re.DOTALL | re.IGNORECASE)
    if match:
        clean_sql = match.group(1).strip()
        print(f"DEBUG: Reasoning extracted:\n{content}") # Helpful for debugging in terminal
        return clean_sql
    else:
        # Fallback if model forgets tags (rare with Llama 3)
        return re.sub(r'```sql|```', '', content, flags=re.IGNORECASE).strip()

def get_plot_code_from_llm(user_question, columns):
    """Generates Python/Plotly code to visualize data."""
    system_prompt = """
    You are a Python Data Expert. Write code using Plotly Express (px) to visualize the provided data.
    1. Assume the data is in a dataframe named 'df_result'.
    2. Assign the figure to a variable named 'fig'.
    3. Return ONLY the python code. No markdown, no explanations.
    4. If the data is not suitable for a chart, return "NONE".
    """
    user_prompt = f"Question: {user_question}\nColumns: {columns}\nWrite the Plotly code."
    
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    content = call_llm(messages)
    return re.sub(r'```python|```', '', content, flags=re.IGNORECASE).strip()

def get_summary_from_llm(user_question, data_snippet):
    """Explains the data findings."""
    system_prompt = """
    You are a helpful analyst. 
    1. The data provided below is the RESULT of a SQL query executed to answer the user's question.
    2. Assume this data is complete and accurate.
    3. Summarize the answer directly.
    """
    user_prompt = f"User Question: {user_question}\nQuery Result Data:\n{data_snippet}"
    
    messages = [{"role": "system", "content": system_prompt}, {"role": "user", "content": user_prompt}]
    return call_llm(messages)