import streamlit as st
from pathlib import Path
from langchain.agents import create_sql_agent
from langchain.sql_database import SQLDatabase
from langchain.agents.agent_types import AgentType
from langchain.callbacks import StreamlitCallbackHandler
from langchain.agents.agent_toolkits import SQLDatabaseToolkit
from sqlalchemy import create_engine
import sqlite3
from langchain_groq import ChatGroq

# Streamlit page config with updated name and icon
st.set_page_config(
    page_title="SQL APEX",
    page_icon="🐻‍❄️",
    layout="centered"
)

# Custom Title and description with CSS and hover effects
st.markdown(
    """
    <style>
    .container {
        background-image: url("https://cdn.pixabay.com/animation/2023/06/26/03/02/03-02-03-917_512.gif");
        background-size: cover;
        margin: 0;
        padding: 50px;
        border-radius: 5px;
        border: 1px solid #ddd;
        position: relative;
        overflow: hidden;
    }

    .container::before {
        content: "";
        position: absolute;
        top: 0;
        left: 0;
        width: 0;
        height: 100%;
        background-color: #F1D4E5;
        transition: width 0.5s ease;
        z-index: 0;
    }

    .container:hover::before {
        width: 100%;
    }

    .container h4,
    .container p {
        position: relative;
        z-index: 1;
        color: #fff;
        transition: color 0.5s ease;
    }

    .container:hover h4,
    .container:hover p {
        color: #000;
    }
    </style>

    <div class="container">
        <h4>🐻‍❄️ SQL APEX </h4>
        <p>Interact with your SQL databases using advanced AI-powered tools.</p>
    </div>
    """,
    unsafe_allow_html=True,
)


# Sidebar settings for database connection and API key
st.sidebar.title("Settings")

radio_opt = ["Use SQLite 3 Database - Student.db", "Connect to your MySQL Database"]
selected_opt = st.sidebar.radio(label="Choose the DB to chat with", options=radio_opt)

# MySQL connection input fields
if radio_opt.index(selected_opt) == 1:
    db_uri = "USE_MYSQL"
    mysql_host = st.sidebar.text_input("Provide MySQL Host", value="localhost")
    mysql_port = st.sidebar.text_input("MySQL Port", value="3306")
    mysql_user = st.sidebar.text_input("MySQL User", value="root")
    mysql_password = st.sidebar.text_input("MySQL Password", value="Shriv@st@v@096", type="password")
    mysql_db = st.sidebar.text_input("MySQL Database")
else:
    db_uri = "USE_LOCALDB"

# API Key input
api_key = st.sidebar.text_input(label="Groq API Key", type="password")

# Basic validations
if not db_uri:
    st.info("Please select a database.")
    st.stop()

if not api_key:
    st.warning("Please provide the Groq API key")
    st.stop()
else:
    st.info("Hello! how can I help you")
# LLM setup using Groq
llm = ChatGroq(groq_api_key=api_key, model_name="Llama3-8b-8192", streaming=True)

# Function to configure the database connection
@st.cache_resource(ttl="2h")
def configure_db(db_uri, mysql_host=None, mysql_port=None, mysql_user=None, mysql_password=None, mysql_db=None):
    if db_uri == "USE_LOCALDB":
        dbfilepath = (Path(__file__).parent / "student.db").absolute()
        creator = lambda: sqlite3.connect(f"file:{dbfilepath}?mode=ro", uri=True)
        return SQLDatabase(create_engine("sqlite:///", creator=creator))
    elif db_uri == "USE_MYSQL":
        if not (mysql_host and mysql_port and mysql_user and mysql_password and mysql_db):
            st.error("Please provide all MySQL connection details.")
            st.stop()

        # Properly encode special characters in the password
        encoded_password = mysql_password.replace("@", "%40")
        connection_uri = f"mysql+mysqlconnector://{mysql_user}:{encoded_password}@{mysql_host}:{mysql_port}/{mysql_db}"
        return SQLDatabase(create_engine(connection_uri))

# Initialize the database based on the selected option
db = configure_db(db_uri, mysql_host, mysql_port, mysql_user, mysql_password, mysql_db) if db_uri == "USE_MYSQL" else configure_db(db_uri)

# Toolkit setup
toolkit = SQLDatabaseToolkit(db=db, llm=llm)

# Create the SQL agent
agent = create_sql_agent(
    llm=llm,
    toolkit=toolkit,
    verbose=True,
    agent_type=AgentType.ZERO_SHOT_REACT_DESCRIPTION
)

# Initialize chat messages in session state
if "messages" not in st.session_state or st.sidebar.button("Clear message history"):
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

# Chat history block in the sidebar
st.sidebar.subheader("Chat History")
with st.sidebar.expander("View chat history"):
    for msg in st.session_state.messages:
        if msg["role"] == "assistant":
            st.markdown(f"**Assistant**: {msg['content']}")
        else:
            st.markdown(f"**User**: {msg['content']}")

# User query input
user_query = st.chat_input(placeholder="Ask anything from the database")

# Process the user query
if user_query:
    st.session_state.messages.append({"role": "user", "content": user_query})
    st.chat_message("user").write(user_query)

    with st.chat_message("assistant"):
        streamlit_callback = StreamlitCallbackHandler(st.container())
        try:
            response = agent.run(user_query, callbacks=[streamlit_callback])
        except Exception as e:
            response = f"An error occurred: {str(e)}"

        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write(response)
