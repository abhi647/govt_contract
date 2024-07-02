import sqlite3
import pandas as pd
import streamlit as st
from openai import OpenAI
import os
from PyPDF2 import PdfFileReader
import docx

# Create a directory for storing uploaded company profiles if it doesn't exist
if not os.path.exists("company_profiles"):
    os.makedirs("company_profiles")

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

# Function to perform semantic search using OpenAI
def semantic_search(query, openai_api_key):
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a helpful assistant."},
            {"role": "user", "content": f"Find information related to: {query}"}
        ],
        temperature=0
    )
    return response.choices[0].message.content

# Save uploaded company profile
def save_company_profile(uploaded_file):
    file_path = os.path.join("company_profiles", uploaded_file.name)
    with open(file_path, "wb") as f:
        f.write(uploaded_file.getbuffer())
    return file_path

# Extract text from different file types
def extract_text_from_file(file_path):
    ext = os.path.splitext(file_path)[-1].lower()
    if ext == ".txt":
        with open(file_path, "r") as f:
            return f.read()
    elif ext == ".pdf":
        pdf = PdfFileReader(file_path)
        text = ""
        for page in range(pdf.getNumPages()):
            text += pdf.getPage(page).extract_text()
        return text
    elif ext == ".docx":
        doc = docx.Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        return text
    else:
        return ""

# Extract competencies using OpenAI
def extract_competencies(company_profile_text, openai_api_key):
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "Extract the core competencies and relevant keywords from the following company profile text:"},
            {"role": "user", "content": company_profile_text}
        ],
        temperature=0
    )
    return response.choices[0].message.content.split(',')

# Match contracts based on company profile
def get_recommended_contracts(company_profile_text, openai_api_key):
    competencies = extract_competencies(company_profile_text, openai_api_key)
    competency_query = " OR ".join([f"requirement LIKE '%{comp.strip()}%'" for comp in competencies])
    query = f"SELECT * FROM data WHERE {competency_query}"
    return pd.read_sql_query(query, conn)

# Generate SQL query using OpenAI
def generate_sql_query(prompt, openai_api_key):
    client = OpenAI(api_key=openai_api_key)
    response = client.chat.completions.create(
        model="gpt-4",
        messages=[
            {"role": "system", "content": "You are a SQL query generator."},
            {"role": "user", "content": f"Generate a SQL query for: {prompt}"}
        ],
        temperature=0
    )
    return response.choices[0].message.content.strip()

# Streamlit interface
st.set_page_config(page_title="ContractScout", layout="wide")

# Sidebar with logo and company profile upload
with st.sidebar:
    st.image("logo.png", use_column_width=True)
    st.title("ContractScout")
    st.subheader("Navigating Opportunities with Precision")

    st.header("Company Profile")
    uploaded_file = st.file_uploader("Upload Company Profile", type=["txt", "pdf", "docx"])
    if uploaded_file is not None:
        file_path = save_company_profile(uploaded_file)
        st.success("Profile uploaded successfully!")
        company_profile_text = extract_text_from_file(file_path)
        openai_api_key = st.text_input("OpenAI API Key", key="profile_api_key", type="password")

# Main layout with tabs
tab1, tab2, tab3 = st.tabs(["Search", "Recommended Contracts", "Chat"])

with tab1:
    st.subheader("Search and Filters")
    col1, col2, col3, col4, col5 = st.columns(5)
    with col1:
        search_query = st.text_input("Search by Title")
    with col2:
        category_filter = st.selectbox("Category", ["All", "8(a)", "Small Business"])
    with col3:
        state_filter = st.text_input("State")
    with col4:
        naics_filter = st.text_input("NAICS Code")
    with col5:
        dollar_range_filter = st.selectbox("Dollar Range", ["All", "$0 to $250K", "$250K to $500K", "$500K to $1M", "Above $1M"])

    # Create query based on filters
    query = "SELECT * FROM data WHERE 1=1"
    if search_query:
        query += f" AND requirements_title LIKE '%{search_query}%'"
    if category_filter != "All":
        query += f" AND small_business_program='{category_filter}'"
    if state_filter:
        query += f" AND place_of_performance_state LIKE '%{state_filter}%'"
    if naics_filter:
        query += f" AND naics LIKE '%{naics_filter}%'"
    if dollar_range_filter != "All":
        query += f" AND dollar_range='{dollar_range_filter}'"

    # Fetch data and display
    data = pd.read_sql_query(query, conn)
    st.subheader("Search Results")
    st.dataframe(data, height=600)

with tab2:
    st.subheader("Recommended Contracts")
    if uploaded_file is not None and openai_api_key:
        recommended_contracts = get_recommended_contracts(company_profile_text, openai_api_key)
        st.dataframe(recommended_contracts, height=600)
    else:
        st.info("Upload a company profile and provide OpenAI API key to see recommended contracts.")

with tab3:
    st.subheader("💬 Chatbot")
    st.caption("🚀 A Streamlit chatbot powered by OpenAI")

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

        # Generate SQL query using OpenAI
        sql_query = generate_sql_query(prompt, openai_api_key)

        # Fetch data based on generated SQL query
        db_result = query_database(sql_query)

        if isinstance(db_result, pd.DataFrame) and not db_result.empty:
            summary = db_result.to_string(index=False)
        else:
            summary = "No matching data found."

        response_content = f"Generated SQL Query:\n{sql_query}\n\nResults:\n{summary}"

        st.session_state.messages.append({"role": "assistant", "content": response_content})
        st.chat_message("assistant").write(response_content)

# Close the database connection
conn.close()