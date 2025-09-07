import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO
import hashlib

# Set page configuration
st.set_page_config(
    page_title="Bug Management Dashboard",
    page_icon="🐛",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .metric-card {
        background-color: #f0f2f6;
        padding: 20px;
        border-radius: 10px;
        margin: 10px 0;
    }
    .status-badge {
        padding: 5px 10px;
        border-radius: 5px;
        color: white;
        font-weight: bold;
    }
    .regression-badge { background-color: #ff9800; }
    .open-badge { background-color: #f44336; }
    .rejected-badge { background-color: #e91e63; }
    .closed-badge { background-color: #4caf50; }
    .pending-badge { background-color: #2196f3; }
    .login-container {
        max-width: 400px;
        margin: auto;
        padding: 2rem;
        background-color: #f0f2f6;
        border-radius: 10px;
        margin-top: 5rem;
    }
    </style>
""", unsafe_allow_html=True)

# Team members list
TEAM_MEMBERS = [
    "2laibamuqadas 2laibamuqadas",
    "2toobashahid 2toobashahid",
    "abdumr076 abdumr076",
    "ahsan03h ahsan03h",
    "2sehrish 2sehrish",
    "qasim.shah1947 qasim.shah1947",
    "abdullah_masood abdullah_masood",
    "talha_munir29 talha_munir29",
    "waqasbinshabeer waqasbinshabeer",
    "azan25 azan25"
]

# User credentials and roles (in production, use environment variables or secure storage)
USERS = {
    "admin": {
        "password": hashlib.sha256("admin123".encode()).hexdigest(),
        "role": "manager",
        "name": "Admin User",
        "team_member": None
    },
    "manager": {
        "password": hashlib.sha256("manager123".encode()).hexdigest(),
        "role": "manager",
        "name": "Team Manager",
        "team_member": None
    },
    "laiba": {
        "password": hashlib.sha256("laiba123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Laiba Muqadas",
        "team_member": "2laibamuqadas 2laibamuqadas"
    },
    "tooba": {
        "password": hashlib.sha256("tooba123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Tooba Shahid",
        "team_member": "2toobashahid 2toobashahid"
    },
    "abdul": {
        "password": hashlib.sha256("abdul123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Abdul MR",
        "team_member": "abdumr076 abdumr076"
    },
    "ahsan": {
        "password": hashlib.sha256("ahsan123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Ahsan",
        "team_member": "ahsan03h ahsan03h"
    },
    "sehrish": {
        "password": hashlib.sha256("sehrish123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Sehrish",
        "team_member": "2sehrish 2sehrish"
    },
    "qasim": {
        "password": hashlib.sha256("qasim123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Qasim Shah",
        "team_member": "qasim.shah1947 qasim.shah1947"
    },
    "abdullah": {
        "password": hashlib.sha256("abdullah123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Abdullah Masood",
        "team_member": "abdullah_masood abdullah_masood"
    },
    "talha": {
        "password": hashlib.sha256("talha123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Talha Munir",
        "team_member": "talha_munir29 talha_munir29"
    },
    "waqas": {
        "password": hashlib.sha256("waqas123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Waqas Bin Shabeer",
        "team_member": "waqasbinshabeer waqasbinshabeer"
    },
    "azan": {
        "password": hashlib.sha256("azan123".encode()).hexdigest(),
        "role": "team_member",
        "name": "Azan",
        "team_member": "azan25 azan25"
    },
    "viewer": {
        "password": hashlib.sha256("view123".encode()).hexdigest(),
        "role": "viewer",
        "name": "Guest Viewer",
        "team_member": None
    }
}

# Status categories
STATUS_MAPPING = {
    "Accepted": "Other Party",
    "Rejected": "Our End",
    "Reopen": "Other Party",
    "Regression Test": "Our End",
    "Open": "Check Handler",
    "Canceled": "Resolved",
    "Closed": "Resolved"
}

# Initialize session state
def init_session_state():
    if 'authenticated' not in st.session_state:
        st.session_state.authenticated = False
    if 'username' not in st.session_state:
        st.session_state.username = None
    if 'role' not in st.session_state:
        st.session_state.role = None
    if 'name' not in st.session_state:
        st.session_state.name = None
    if 'team_member' not in st.session_state:
        st.session_state.team_member = None
    if 'data' not in st.session_state:
        st.session_state.data = None
    if 'team_data' not in st.session_state:
        st.session_state.team_data = None

def authenticate(username, password):
    """Authenticate user credentials"""
    if username in USERS:
        hashed_password = hashlib.sha256(password.encode()).hexdigest()
        if USERS[username]["password"] == hashed_password:
            return True, USERS[username]
    return False, None

def login_page():
    """Display login page"""
    st.markdown("<h1 style='text-align: center;'>🐛 Bug Management System</h1>", unsafe_allow_html=True)
    
    with st.container():
        st.markdown("<div class='login-container'>", unsafe_allow_html=True)
        st.markdown("### Login")
        
        with st.form("login_form"):
            username = st.text_input("Username")
            password = st.text_input("Password", type="password")
            col1, col2 = st.columns(2)
            with col1:
                submit = st.form_submit_button("Login", use_container_width=True, type="primary")
            with col2:
                demo = st.form_submit_button("Demo Mode", use_container_width=True)
            
            if submit:
                if username and password:
                    is_valid, user_info = authenticate(username, password)
                    if is_valid:
                        st.session_state.authenticated = True
                        st.session_state.username = username
                        st.session_state.role = user_info["role"]
                        st.session_state.name = user_info["name"]
                        st.session_state.team_member = user_info["team_member"]
                        st.success(f"Welcome, {user_info['name']}!")
                        st.rerun()
                    else:
                        st.error("Invalid username or password")
                else:
                    st.warning("Please enter both username and password")
            
            if demo:
                st.session_state.authenticated = True
                st.session_state.username = "demo"
                st.session_state.role = "viewer"
                st.session_state.name = "Demo User"
                st.session_state.team_member = None
                st.rerun()
        
        st.markdown("</div>", unsafe_allow_html=True)
    
    # Display available users for demo
    with st.expander("📋 Demo Credentials"):
        st.markdown("""
        **Manager Access:**
        - Username: `manager` | Password: `manager123`
        - Username: `admin` | Password: `admin123`
        
        **Team Member Access:**
        - Username: `laiba` | Password: `laiba123`
        - Username: `tooba` | Password: `tooba123`
        - Username: `abdul` | Password: `abdul123`
        - (and others - each team member has their username)
        
        **Viewer Access:**
        - Username: `viewer` | Password: `view123`
        
        **Demo Mode:**
        - Click "Demo Mode" for read-only access
        """)

def logout():
    """Logout user"""
    for key in ['authenticated', 'username', 'role', 'name', 'team_member', 'data', 'team_data']:
        if key in st.session_state:
            del st.session_state[key]
    st.rerun()

def get_last_four_digits(defect_no):
    """Extract last 4 digits from defect number"""
    return str(defect_no)[-4:] if pd.notna(defect_no) else ""

def load_and_process_data(uploaded_file):
    """Load and process the uploaded Excel file"""
    try:
        df = pd.read_excel(uploaded_file, sheet_name=0)
        df['Defect_ID'] = df['Defect No.'].apply(get_last_four_digits)
        df['Creation Time'] = pd.to_datetime(df['Creation Time'], errors='coerce')
        df['Status Time'] = pd.to_datetime(df['Status Time'], errors='coerce')
        
        team_df = df[df['Submitted By'].isin(TEAM_MEMBERS)].copy()
        
        team_df['Ownership'] = team_df.apply(
            lambda row: 'Our End' if (row['Status'] == 'Open' and row['Handler'] == row['Submitted By']) 
            else ('Other Party' if row['Status'] == 'Open' 
            else STATUS_MAPPING.get(row['Status'], 'Unknown')), axis=1
        )
        
        return df, team_df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None, None

def get_today_resolved(df):
    """Get bugs resolved today"""
    today = pd.Timestamp.now().normalize()
    today_resolved = df[
        (df['Status Time'] >= today) & 
        (df['Status'].isin(['Closed', 'Canceled']))
    ]
    return today_resolved

def create_summary_metrics(team_df, user_role, team_member):
    """Create summary metrics based on user role"""
    if user_role == "team_member" and team_member:
        # Filter for specific team member
        team_df = team_df[team_df['Submitted By'] == team_member]
        st.info(f"Showing data for: {team_member.split()[0]}")
    
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_bugs = len(team_df)
        st.metric("Total Bugs", total_bugs)
    
    with col2:
        regression = len(team_df[team_df['Status'] == 'Regression Test'])
        st.metric("Regression Testing", regression, delta=f"{regression/total_bugs*100:.1f}%" if total_bugs > 0 else "0%")
    
    with col3:
        open_our_end = len(team_df[(team_df['Status'] == 'Open') & (team_df['Ownership'] == 'Our End')])
        st.metric("Open (Our End)", open_our_end)
    
    with col4:
        rejected = len(team_df[team_df['Status'] == 'Rejected'])
        st.metric("Rejected", rejected)
    
    with col5:
        resolved = len(team_df[team_df['Status'].isin(['Closed', 'Canceled'])])
        st.metric("Resolved", resolved, delta=f"{resolved/total_bugs*100:.1f}%" if total_bugs > 0 else "0%")

def display_bug_table(df, title="Bugs", can_edit=False):
    """Display a formatted bug table"""
    if len(df) > 0:
        st.subheader(f"{title} ({len(df)} bugs)")
        
        display_columns = ['Defect_ID', 'Submitted By', 'Status', 'Handler', 
                          'Creation Time', 'Status Time', 'Brief Description']
        
        display_columns = [col for col in display_columns if col in df.columns]
        display_df = df[display_columns].copy()
        
        if 'Creation Time' in display_df.columns:
            display_df['Creation Time'] = display_df['Creation Time'].dt.strftime('%Y-%m-%d %H:%M')
        if 'Status Time' in display_df.columns:
            display_df['Status Time'] = display_df['Status Time'].dt.strftime('%Y-%m-%d %H:%M')
        
        if can_edit and st.session_state.role in ['manager', 'admin']:
            st.data_editor(display_df, use_container_width=True, height=400)
        else:
            st.dataframe(display_df, use_container_width=True, height=400)
    else:
        st.info(f"No bugs found in {title}")

def create_individual_analysis(team_df, member):
    """Create analysis for individual team member"""
    member_df = team_df[team_df['Submitted By'] == member]
    
    if len(member_df) > 0:
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric("Total Bugs", len(member_df))
        
        with col2:
            pending = len(member_df[member_df['Ownership'] == 'Our End'])
            st.metric("Pending (Our End)", pending)
        
        with col3:
            resolved = len(member_df[member_df['Status'].isin(['Closed', 'Canceled'])])
            st.metric("Resolved", resolved)
        
        status_counts = member_df['Status'].value_counts()
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title=f"Bug Status Distribution for {member.split()[0]}"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        display_bug_table(member_df, f"All Bugs for {member.split()[0]}")
    else:
        st.info(f"No bugs found for {member}")

def create_team_analytics(team_df):
    """Create team-wide analytics"""
    st.subheader("Team Member Bug Distribution")
    member_counts = team_df['Submitted By'].value_counts()
    
    fig1 = px.bar(
        x=member_counts.values,
        y=[name.split()[0] for name in member_counts.index],
        orientation='h',
        title="Bugs by Team Member",
        labels={'x': 'Number of Bugs', 'y': 'Team Member'}
    )
    st.plotly_chart(fig1, use_container_width=True)
    
    st.subheader("Overall Status Distribution")
    status_dist = team_df['Status'].value_counts()
    
    fig2 = px.pie(
        values=status_dist.values,
        names=status_dist.index,
        title="Team Bug Status Distribution",
        hole=0.4
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    st.subheader("Bug Ownership Distribution")
    ownership_dist = team_df['Ownership'].value_counts()
    
    fig3 = px.bar(
        x=ownership_dist.index,
        y=ownership_dist.values,
        title="Bugs by Ownership",
        labels={'x': 'Ownership', 'y': 'Number of Bugs'},
        color=ownership_dist.index,
        color_discrete_map={
            'Our End': '#ff4444',
            'Other Party': '#44ff44',
            'Resolved': '#4444ff'
        }
    )
    st.plotly_chart(fig3, use_container_width=True)
    
    st.subheader("Bug Creation Timeline")
    team_df_timeline = team_df.copy()
    team_df_timeline['Date'] = team_df_timeline['Creation Time'].dt.date
    timeline_counts = team_df_timeline.groupby('Date').size().reset_index(name='Count')
    
    fig4 = px.line(
        timeline_counts,
        x='Date',
        y='Count',
        title="Bugs Created Over Time",
        markers=True
    )
    st.plotly_chart(fig4, use_container_width=True)

def generate_daily_report(team_df):
    """Generate daily report for manager"""
    today = pd.Timestamp.now().normalize()
    
    st.subheader("📊 Daily Report Summary")
    
    today_resolved = get_today_resolved(team_df)
    
    total_pending_start = len(team_df[team_df['Ownership'] == 'Our End'])
    resolved_today = len(today_resolved)
    still_pending = total_pending_start - resolved_today
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("Pending at Day Start", total_pending_start)
    
    with col2:
        st.metric("Resolved Today", resolved_today, delta=f"-{resolved_today}")
    
    with col3:
        st.metric("Still Pending", still_pending)
    
    with col4:
        resolution_rate = (resolved_today / total_pending_start * 100) if total_pending_start > 0 else 0
        st.metric("Resolution Rate", f"{resolution_rate:.1f}%")
    
    st.subheader("Member-wise Resolution Summary")
    
    member_summary = []
    for member in TEAM_MEMBERS:
        member_df = team_df[team_df['Submitted By'] == member]
        member_resolved = today_resolved[today_resolved['Submitted By'] == member]
        
        if len(member_df) > 0:
            member_summary.append({
                'Team Member': member.split()[0],
                'Total Bugs': len(member_df),
                'Pending (Our End)': len(member_df[member_df['Ownership'] == 'Our End']),
                'Resolved Today': len(member_resolved),
                'Still Open': len(member_df[member_df['Status'] == 'Open']),
                'Regression Test': len(member_df[member_df['Status'] == 'Regression Test'])
            })
    
    if member_summary:
        summary_df = pd.DataFrame(member_summary)
        st.dataframe(summary_df, use_container_width=True)
        
        if st.session_state.role in ['manager', 'admin']:
            report_buffer = BytesIO()
            with pd.ExcelWriter(report_buffer, engine='openpyxl') as writer:
                summary_df.to_excel(writer, sheet_name='Daily Summary', index=False)
                today_resolved.to_excel(writer, sheet_name='Resolved Today', index=False)
            
            report_buffer.seek(0)
            st.download_button(
                label="📥 Download Daily Report",
                data=report_buffer,
                file_name=f"daily_bug_report_{datetime.now().strftime('%Y%m%d')}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

def main_dashboard():
    """Main dashboard after login"""
    # Header with user info and logout
    col1, col2, col3 = st.columns([6, 2, 1])
    with col1:
        st.title("🐛 Bug Management Dashboard")
    with col2:
        st.markdown(f"**👤 {st.session_state.name}**")
        st.caption(f"Role: {st.session_state.role.title()}")
    with col3:
        if st.button("Logout", type="secondary"):
            logout()
    
    st.markdown("---")
    
    # Sidebar for file upload (only for managers and admin)
    with st.sidebar:
        st.header("📁 Dashboard Controls")
        
        # Show user info in sidebar
        st.info(f"""
        **Current User:** {st.session_state.name}  
        **Role:** {st.session_state.role.title()}  
        **Access Level:** {'Full' if st.session_state.role in ['manager', 'admin'] else 'Limited'}
        """)
        
        if st.session_state.role in ['manager', 'admin', 'team_member']:
            uploaded_file = st.file_uploader(
                "Choose Excel file", 
                type=['xlsx', 'xls'],
                help="Upload the bug tracking Excel file from the portal"
            )
            
            if uploaded_file is not None:
                st.success("File uploaded successfully!")
                st.info(f"File: {uploaded_file.name}")
                
                # Process the file
                all_df, team_df = load_and_process_data(uploaded_file)
                st.session_state.data = all_df
                st.session_state.team_data = team_df
        else:
            st.warning("File upload is disabled for viewers")
            uploaded_file = None
    
    # Main content area
    if st.session_state.team_data is not None:
        team_df = st.session_state.team_data
        
        # Filter data based on user role
        if st.session_state.role == "team_member" and st.session_state.team_member:
            # Team members see only their own data by default
            personal_df = team_df[team_df['Submitted By'] == st.session_state.team_member]
            create_summary_metrics(personal_df, st.session_state.role, st.session_state.team_member)
        else:
            create_summary_metrics(team_df, st.session_state.role, None)
        
        st.markdown("---")
        
        # Define tabs based on user role
        if st.session_state.role in ['manager', 'admin']:
            # Managers see all tabs
            tabs = st.tabs([
                "📋 Regression Testing",
                "🔴 Open (Our End)",
                "❌ Rejected",
                "✅ Closed & Canceled",
                "👤 Individual Members",
                "🔄 Pending (Other Party)",
                "📊 Team Analytics",
                "📈 Individual Analytics",
                "📅 Today's Resolved",
                "📑 Daily Report"
            ])
            
            with tabs[0]:
                regression_df = team_df[team_df['Status'] == 'Regression Test']
                display_bug_table(regression_df, "Bugs in Regression Testing", can_edit=True)
            
            with tabs[1]:
                open_our_df = team_df[(team_df['Status'] == 'Open') & (team_df['Ownership'] == 'Our End')]
                display_bug_table(open_our_df, "Open Bugs (Our End)", can_edit=True)
            
            with tabs[2]:
                rejected_df = team_df[team_df['Status'] == 'Rejected']
                display_bug_table(rejected_df, "Rejected Bugs", can_edit=True)
            
            with tabs[3]:
                resolved_df = team_df[team_df['Status'].isin(['Closed', 'Canceled'])]
                display_bug_table(resolved_df, "Resolved Bugs (Closed & Canceled)")
            
            with tabs[4]:
                st.subheader("Bugs by Individual Team Member")
                selected_member = st.selectbox(
                    "Select Team Member",
                    options=TEAM_MEMBERS,
                    format_func=lambda x: x.split()[0]
                )
                
                if selected_member:
                    member_df = team_df[team_df['Submitted By'] == selected_member]
                    st.markdown(f"### {selected_member.split()[0]}'s Bugs")
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.markdown("**Pending on Our End:**")
                        pending_our = member_df[member_df['Ownership'] == 'Our End']
                        if len(pending_our) > 0:
                            for _, bug in pending_our.iterrows():
                                st.write(f"• {bug['Defect_ID']} - {bug['Status']}")
                        else:
                            st.write("No pending bugs")
                    
                    with col2:
                        st.markdown("**Other Status:**")
                        other_status = member_df[member_df['Ownership'] != 'Our End']
                        if len(other_status) > 0:
                            for _, bug in other_status.iterrows():
                                st.write(f"• {bug['Defect_ID']} - {bug['Status']}")
                        else:
                            st.write("No bugs")
                    
                    display_bug_table(member_df, f"All Bugs for {selected_member.split()[0]}")
            
            with tabs[5]:
                other_party_df = team_df[team_df['Ownership'] == 'Other Party']
                display_bug_table(other_party_df, "Bugs Pending on Other Party")
            
            with tabs[6]:
                create_team_analytics(team_df)
            
            with tabs[7]:
                st.subheader("Individual Team Member Analytics")
                selected_member_analytics = st.selectbox(
                    "Select Team Member for Analytics",
                    options=TEAM_MEMBERS,
                    format_func=lambda x: x.split()[0],
                    key="analytics_member"
                )
                
                if selected_member_analytics:
                    create_individual_analysis(team_df, selected_member_analytics)
            
            with tabs[8]:
                st.subheader("Bugs Resolved Today")
                today_resolved = get_today_resolved(team_df)
                
                if len(today_resolved) > 0:
                    st.success(f"🎉 {len(today_resolved)} bugs resolved today!")
                    display_bug_table(today_resolved, "Today's Resolved Bugs")
                else:
                    st.info("No bugs resolved today yet")
            
            with tabs[9]:
                generate_daily_report(team_df)
        
        elif st.session_state.role == "team_member":
            # Team members see limited tabs
            tabs = st.tabs([
                "📋 My Bugs",
                "🔴 My Open Bugs",
                "✅ My Resolved",
                "📊 My Analytics",
                "👥 Team Overview"
            ])
            
            member_df = team_df[team_df['Submitted By'] == st.session_state.team_member]
            
            with tabs[0]:
                display_bug_table(member_df, "My Bugs")
            
            with tabs[1]:
                my_open = member_df[member_df['Status'] == 'Open']
                display_bug_table(my_open, "My Open Bugs")
            
            with tabs[2]:
                my_resolved = member_df[member_df['Status'].isin(['Closed', 'Canceled'])]
                display_bug_table(my_resolved, "My Resolved Bugs")
            
            with tabs[3]:
                create_individual_analysis(team_df, st.session_state.team_member)
            
            with tabs[4]:
                st.subheader("Team Overview")
                member_counts = team_df['Submitted By'].value_counts()
                
                fig = px.bar(
                    x=member_counts.values,
                    y=[name.split()[0] for name in member_counts.index],
                    orientation='h',
                    title="Team Bug Distribution",
                    labels={'x': 'Number of Bugs', 'y': 'Team Member'}
                )
                st.plotly_chart(fig, use_container_width=True)
        
        else:  # Viewer role
            tabs = st.tabs([
                "📊 Team Overview",
                "📈 Status Distribution"
            ])
            
            with tabs[0]:
                st.subheader("Team Bug Overview")
                member_counts = team_df['Submitted By'].value_counts()
                
                fig = px.bar(
                    x=member_counts.values,
                    y=[name.split()[0] for name in member_counts.index],
                    orientation='h',
                    title="Bugs by Team Member",
                    labels={'x': 'Number of Bugs', 'y': 'Team Member'}
                )
                st.plotly_chart(fig, use_container_width=True)
            
            with tabs[1]:
                st.subheader("Bug Status Distribution")
                status_dist = team_df['Status'].value_counts()
                
                fig = px.pie(
                    values=status_dist.values,
                    names=status_dist.index,
                    title="Overall Status Distribution",
                    hole=0.4
                )
                st.plotly_chart(fig, use_container_width=True)
    
    else:
        st.info("👆 Please upload an Excel file from the bug portal to get started")
        
        if st.session_state.role == "viewer":
            st.warning("As a viewer, you need a manager or team member to upload data first.")
        
        st.markdown("""
        ### 📌 Features Available Based on Your Role:
        """)
        
        if st.session_state.role in ['manager', 'admin']:
            st.markdown("""
            **Manager/Admin Access:**
            - ✅ Full access to all team data
            - ✅ Can upload and edit bug data
            - ✅ Generate and download daily reports
            - ✅ View all team analytics
            - ✅ Access individual member data
            """)
        elif st.session_state.role == "team_member":
            st.markdown("""
            **Team Member Access:**
            - ✅ View and manage your own bugs
            - ✅ Upload bug data files
            - ✅ View your personal analytics
            - ✅ See team overview statistics
            - ❌ Cannot edit other members' data
            - ❌ Cannot generate manager reports
            """)
        else:  # Viewer
            st.markdown("""
            **Viewer Access:**
            - ✅ View team overview and statistics
            - ✅ Read-only access to dashboards
            - ❌ Cannot upload files
            - ❌ Cannot edit any data
            - ❌ Cannot download reports
            """)
        
        st.markdown("""
        ### 👥 Team Members Tracked:
        """)
        
        for i, member in enumerate(TEAM_MEMBERS, 1):
            st.write(f"{i}. {member.split()[0]}")

# Main app
def main():
    init_session_state()
    
    if not st.session_state.authenticated:
        login_page()
    else:
        main_dashboard()

if __name__ == "__main__":
    main()