import sqlite3
import pandas as pd
import streamlit as st
from openai import OpenAI

# Connect to SQLite database
conn = sqlite3.connect('data.db')

# Function to fetch data from the database based on a natural language query
def query_database(sql_query):
    c = conn.cursor()
    try:
        c.execute(sql_query)
        results = c.fetchall()
        colnames = [description[0] for description in c.description]
        df = pd.DataFrame(results, columns=colnames)
        return df
    except Exception as e:
        return str(e)

# Streamlit interface
st.set_page_config(page_title="Data Portal", layout="wide")
st.title("Data Portal with Enhanced UI")

# Search and filter section
st.sidebar.header("Search and Filters")
search_query = st.sidebar.text_input("Search by Title")
category_filter = st.sidebar.selectbox("Category", ["All", "8(a)", "Small Business"])
state_filter = st.sidebar.text_input("State")

# Create query based on filters
query = "SELECT * FROM data WHERE 1=1"
if search_query:
    query += f" AND requirements_title LIKE '%{search_query}%'"
if category_filter != "All":
    query += f" AND small_business_program='{category_filter}'"
if state_filter:
    query += f" AND place_of_performance_state LIKE '%{state_filter}%'"

# Fetch data and display
data = pd.read_sql_query(query, conn)

# Tabs for viewing data and chatbot
tab1, tab2 = st.tabs(["Data Table", "Chatbot"])

with tab1:
    st.subheader("Data Viewer")
    st.dataframe(data)

with tab2:
    st.subheader("💬 Chatbot")
    st.caption("🚀 A Streamlit chatbot powered by OpenAI")

    with st.sidebar:
        openai_api_key = st.text_input("OpenAI API Key", key="chatbot_api_key", type="password")
        st.markdown("[Get an OpenAI API key](https://platform.openai.com/account/api-keys)")
        st.markdown("[View the source code](https://github.com/streamlit/llm-examples/blob/main/Chatbot.py)")
        st.markdown("[![Open in GitHub Codespaces](https://github.com/codespaces/badge.svg)](https://codespaces.new/streamlit/llm-examples?quickstart=1)")

    if "messages" not in st.session_state:
        st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

    for msg in st.session_state.messages:
        st.chat_message(msg["role"]).write(msg["content"])

    if prompt := st.chat_input():
        if not openai_api_key:
            st.info("Please add your OpenAI API key to continue.")
            st.stop()

        client = OpenAI(api_key=openai_api_key)
        st.session_state.messages.append({"role": "user", "content": prompt})
        st.chat_message("user").write(prompt)

        # Query database based on user input
        response = client.chat.completions.create(
            model="gpt-4",
            messages=st.session_state.messages,
            temperature=0
        )
        msg = response.choices[0].message.content

        # Generate SQL query based on the user's prompt using OpenAI response
        try:
            sql_query = f"SELECT * FROM data WHERE requirements_title LIKE '%{prompt}%' OR organization LIKE '%{prompt}%'"
            db_result = query_database(sql_query)

            if isinstance(db_result, pd.DataFrame) and not db_result.empty:
                summary = db_result.to_string(index=False)
            else:
                summary = "No matching data found."

            response_content = f"{msg}\n\n{summary}"
        except Exception as e:
            response_content = f"Error: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.chat_message("assistant").write(response_content)

# Close the database connection
conn.close()
