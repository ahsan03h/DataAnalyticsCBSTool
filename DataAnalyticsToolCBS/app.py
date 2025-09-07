import streamlit as st
import pandas as pd
import plotly.express as px
from datetime import datetime
import hashlib
from io import BytesIO

# Page config
st.set_page_config(
    page_title="Bug Management Dashboard",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for polished UI
st.markdown("""
    <style>
    body {
        background-color: #f8fafc;
    }
    .main-title {
        text-align: center;
        font-size: 3rem;
        font-weight: bold;
        background: linear-gradient(135deg, #00B9E8 0%, #0066CC 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    .project-title {
        text-align: center;
        font-size: 1.5rem;
        font-weight: 500;
        margin-bottom: 2rem;
        color: #333;
    }
    .metric-card {
        background: white;
        padding: 20px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0,0,0,0.05);
        transition: all 0.3s ease;
    }
    .metric-card:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 20px rgba(0,0,0,0.1);
    }
    .login-container {
        max-width: 380px;
        margin: auto;
        padding: 2rem;
        border-radius: 15px;
        background: white;
        box-shadow: 0 8px 25px rgba(0,0,0,0.1);
        margin-top: 2rem;
    }
    .login-header {
        text-align: center;
        font-size: 1.5rem;
        font-weight: bold;
        margin-bottom: 1.5rem;
        color: #0066CC;
    }
    .stTextInput > div > div > input {
        border-radius: 10px;
        padding: 12px;
        border: 1px solid #ddd;
    }
    .role-badge {
        background: linear-gradient(135deg, #00B9E8 0%, #0066CC 100%);
        color: white;
        padding: 6px 14px;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: bold;
        display: inline-block;
    }
    .footer {
        text-align: center;
        color: #666;
        font-size: 0.9rem;
        margin-top: 3rem;
    }
    </style>
""", unsafe_allow_html=True)

# -------------------------------
# USERS (same as before, omitted here for brevity)
# -------------------------------

# Authentication
def authenticate(username, password):
    if username in USERS:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if USERS[username]["password"] == hashed_password:
            return True, USERS[username]
    return False, None

# Login Page
def login_page():
    st.markdown("<h1 class='main-title'>🐛 Bug Management System</h1>", unsafe_allow_html=True)
    st.markdown("<div class='project-title'>Project Phoenix - Powered by Telenor</div>", unsafe_allow_html=True)

    # Telenor logo
    st.image("https://upload.wikimedia.org/wikipedia/commons/4/4e/Telenor_Logo.svg", width=120)

    with st.container():
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("<div class='login-header'>Sign In</div>", unsafe_allow_html=True)

        with st.form("login_form", clear_on_submit=False):
            username = st.text_input("👤 Username", placeholder="Enter your username")
            password = st.text_input("🔒 Password", type="password", placeholder="Enter your password")

            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("🚀 Login", use_container_width=True)
            with col2:
                demo = st.form_submit_button("👁️ Guest Access", use_container_width=True)

            if submit:
                if username and password:
                    is_valid, user_info = authenticate(username, password)
                    if is_valid:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user_info["role"]
                        st.session_state.name = user_info["name"]
                        st.session_state.team_member = user_info["team_member"]
                        st.success(f"Welcome, {user_info['name']}! 🎉")
                        st.balloons()
                        st.rerun()
                    else:
                        st.error("❌ Invalid username or password")
                else:
                    st.warning("⚠️ Please enter both username and password")

            if demo:
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.session_state.role = "viewer"
                st.session_state.name = "Demo User"
                st.session_state.team_member = None
                st.rerun()

        st.markdown("</div>", unsafe_allow_html=True)

    st.markdown("<div class='footer'>© 2025 Project Phoenix - Bug Management System</div>", unsafe_allow_html=True)

# -------------------------------
# Main Dashboard (header redesign)
# -------------------------------
def main_dashboard():
    col1, col2, col3 = st.columns([6, 2, 1])
    with col1:
        st.markdown("<h1 class='main-title'>🐛 Bug Management Dashboard</h1>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"👤 **{st.session_state.name}**")
        st.markdown(f"<span class='role-badge'>{st.session_state.role.title()}</span>", unsafe_allow_html=True)
    with col3:
        if st.button("Logout", type="secondary"):
            logout()
    st.markdown("---")

    # Sidebar branding
    with st.sidebar:
        st.image("https://upload.wikimedia.org/wikipedia/commons/4/4e/Telenor_Logo.svg", width=150)
        st.header("📁 Dashboard Controls")

        if st.session_state.role in ['manager', 'admin']:
            st.success(f"Manager Access: {st.session_state.name}")
        else:
            st.info(f"Welcome: {st.session_state.name}")

    # ... (rest of your dashboard functions remain same, but now wrapped in cleaner UI)

# -------------------------------
# Main app
# -------------------------------
def main():
    if "authenticated" not in st.session_state:
        st.session_state.authenticated = False
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()
