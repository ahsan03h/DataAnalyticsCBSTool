import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime, timedelta
import numpy as np
from io import BytesIO

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

# Status categories
STATUS_MAPPING = {
    "Accepted": "Other Party",
    "Rejected": "Our End",
    "Reopen": "Other Party",
    "Regression Test": "Our End",
    "Open": "Check Handler",  # Need to check handler
    "Canceled": "Resolved",
    "Closed": "Resolved"
}

def get_last_four_digits(defect_no):
    """Extract last 4 digits from defect number"""
    return str(defect_no)[-4:] if pd.notna(defect_no) else ""

def load_and_process_data(uploaded_file):
    """Load and process the uploaded Excel file"""
    try:
        # Read Excel file
        df = pd.read_excel(uploaded_file, sheet_name=0)
        
        # Add last 4 digits column
        df['Defect_ID'] = df['Defect No.'].apply(get_last_four_digits)
        
        # Convert datetime columns
        df['Creation Time'] = pd.to_datetime(df['Creation Time'], errors='coerce')
        df['Status Time'] = pd.to_datetime(df['Status Time'], errors='coerce')
        
        # Filter for team members only
        team_df = df[df['Submitted By'].isin(TEAM_MEMBERS)].copy()
        
        # Determine ownership for "Open" status
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

def create_summary_metrics(team_df):
    """Create summary metrics for the dashboard"""
    col1, col2, col3, col4, col5 = st.columns(5)
    
    with col1:
        total_bugs = len(team_df)
        st.metric("Total Team Bugs", total_bugs)
    
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

def display_bug_table(df, title="Bugs"):
    """Display a formatted bug table"""
    if len(df) > 0:
        st.subheader(f"{title} ({len(df)} bugs)")
        
        # Select and reorder columns for display
        display_columns = ['Defect_ID', 'Submitted By', 'Status', 'Handler', 
                          'Creation Time', 'Status Time', 'Brief Description']
        
        # Filter columns that exist in the dataframe
        display_columns = [col for col in display_columns if col in df.columns]
        
        # Create a copy for display
        display_df = df[display_columns].copy()
        
        # Format datetime columns
        if 'Creation Time' in display_df.columns:
            display_df['Creation Time'] = display_df['Creation Time'].dt.strftime('%Y-%m-%d %H:%M')
        if 'Status Time' in display_df.columns:
            display_df['Status Time'] = display_df['Status Time'].dt.strftime('%Y-%m-%d %H:%M')
        
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
        
        # Status distribution chart
        status_counts = member_df['Status'].value_counts()
        fig = px.pie(
            values=status_counts.values, 
            names=status_counts.index,
            title=f"Bug Status Distribution for {member.split()[0]}"
        )
        st.plotly_chart(fig, use_container_width=True)
        
        # Bug list
        display_bug_table(member_df, f"All Bugs for {member.split()[0]}")
    else:
        st.info(f"No bugs found for {member}")

def create_team_analytics(team_df):
    """Create team-wide analytics"""
    
    # Team member comparison
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
    
    # Status distribution across team
    st.subheader("Overall Status Distribution")
    status_dist = team_df['Status'].value_counts()
    
    fig2 = px.pie(
        values=status_dist.values,
        names=status_dist.index,
        title="Team Bug Status Distribution",
        hole=0.4
    )
    st.plotly_chart(fig2, use_container_width=True)
    
    # Ownership distribution
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
    
    # Timeline analysis
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
    
    # Today's resolved bugs
    today_resolved = get_today_resolved(team_df)
    
    # Calculate metrics
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
    
    # Detailed breakdown by member
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
        
        # Download button for report
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

# Main app
def main():
    st.title("🐛 Bug Management Dashboard")
    st.markdown("---")
    
    # Sidebar for file upload
    with st.sidebar:
        st.header("📁 Upload Data")
        uploaded_file = st.file_uploader(
            "Choose Excel file", 
            type=['xlsx', 'xls'],
            help="Upload the bug tracking Excel file from the portal"
        )
        
        if uploaded_file is not None:
            st.success("File uploaded successfully!")
            st.info(f"File: {uploaded_file.name}")
    
    if uploaded_file is not None:
        # Load and process data
        all_df, team_df = load_and_process_data(uploaded_file)
        
        if team_df is not None and len(team_df) > 0:
            # Display summary metrics
            create_summary_metrics(team_df)
            st.markdown("---")
            
            # Create tabs
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
            
            # Tab 1: Regression Testing
            with tabs[0]:
                regression_df = team_df[team_df['Status'] == 'Regression Test']
                display_bug_table(regression_df, "Bugs in Regression Testing")
            
            # Tab 2: Open (Our End)
            with tabs[1]:
                open_our_df = team_df[(team_df['Status'] == 'Open') & (team_df['Ownership'] == 'Our End')]
                display_bug_table(open_our_df, "Open Bugs (Our End)")
            
            # Tab 3: Rejected
            with tabs[2]:
                rejected_df = team_df[team_df['Status'] == 'Rejected']
                display_bug_table(rejected_df, "Rejected Bugs")
            
            # Tab 4: Closed & Canceled
            with tabs[3]:
                resolved_df = team_df[team_df['Status'].isin(['Closed', 'Canceled'])]
                display_bug_table(resolved_df, "Resolved Bugs (Closed & Canceled)")
            
            # Tab 5: Individual Team Members
            with tabs[4]:
                st.subheader("Bugs by Individual Team Member")
                
                selected_member = st.selectbox(
                    "Select Team Member",
                    options=TEAM_MEMBERS,
                    format_func=lambda x: x.split()[0]
                )
                
                if selected_member:
                    member_df = team_df[team_df['Submitted By'] == selected_member]
                    
                    # Show member's bugs grouped by status
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
            
            # Tab 6: Pending (Other Party)
            with tabs[5]:
                other_party_df = team_df[team_df['Ownership'] == 'Other Party']
                display_bug_table(other_party_df, "Bugs Pending on Other Party")
            
            # Tab 7: Team Analytics
            with tabs[6]:
                create_team_analytics(team_df)
            
            # Tab 8: Individual Analytics
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
            
            # Tab 9: Today's Resolved
            with tabs[8]:
                st.subheader("Bugs Resolved Today")
                today_resolved = get_today_resolved(team_df)
                
                if len(today_resolved) > 0:
                    st.success(f"🎉 {len(today_resolved)} bugs resolved today!")
                    display_bug_table(today_resolved, "Today's Resolved Bugs")
                else:
                    st.info("No bugs resolved today yet")
            
            # Tab 10: Daily Report
            with tabs[9]:
                generate_daily_report(team_df)
        
        else:
            st.warning("No data found for team members in the uploaded file.")
    
    else:
        # Welcome message when no file is uploaded
        st.info("👆 Please upload an Excel file from the bug portal to get started")
        
        st.markdown("""
        ### 📌 Features of this Dashboard:
        
        1. **Bug Tracking by Status**: Monitor bugs in different states (Regression Testing, Open, Rejected, etc.)
        2. **Team Member Analysis**: Track individual team member's bug status
        3. **Ownership Identification**: Automatically determine if bugs are pending on your team or other parties
        4. **Daily Reporting**: Generate comprehensive reports for management
        5. **Real-time Analytics**: Visual insights into bug distribution and trends
        6. **Today's Progress**: Track bugs resolved today
        
        ### 👥 Team Members Tracked:
        """)
        
        for i, member in enumerate(TEAM_MEMBERS, 1):
            st.write(f"{i}. {member.split()[0]}")

if __name__ == "__main__":
    main()