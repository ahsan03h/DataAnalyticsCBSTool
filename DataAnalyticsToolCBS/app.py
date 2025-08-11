import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import numpy as np
from io import BytesIO
import openpyxl
from collections import Counter
import re

# Page configuration
st.set_page_config(
    page_title="Test Analytics Dashboard",
    page_icon="🔍",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better UI
st.markdown("""
    <style>
    .main {
        padding: 0rem 1rem;
    }
    .stMetric {
        background-color: #f0f2f6;
        padding: 15px;
        border-radius: 10px;
        box-shadow: 0 2px 4px rgba(0,0,0,0.1);
    }
    .metric-container {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        padding: 20px;
        border-radius: 15px;
        color: white;
        margin-bottom: 20px;
    }
    h1 {
        color: #1e293b;
        font-weight: 700;
    }
    h2 {
        color: #334155;
        font-weight: 600;
        border-bottom: 2px solid #e2e8f0;
        padding-bottom: 10px;
    }
    .stTabs [data-baseweb="tab-list"] {
        gap: 8px;
    }
    .stTabs [data-baseweb="tab"] {
        background-color: #f1f5f9;
        border-radius: 8px;
        padding: 8px 16px;
        font-weight: 500;
    }
    .stTabs [aria-selected="true"] {
        background-color: #4f46e5;
        color: white;
    }
    .success-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #10b981;
        color: white;
        margin: 1rem 0;
    }
    .warning-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #f59e0b;
        color: white;
        margin: 1rem 0;
    }
    .error-box {
        padding: 1rem;
        border-radius: 0.5rem;
        background-color: #ef4444;
        color: white;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# Initialize session state
if 'data' not in st.session_state:
    st.session_state.data = None
if 'file_uploaded' not in st.session_state:
    st.session_state.file_uploaded = False

def validate_excel_structure(df):
    """Validate if the uploaded Excel has the required columns"""
    required_columns = ['TC #', 'Stream', 'Domain', 'Offer ID', 'Test Scenario', 
                        'Expected Result', 'Actual Result', 'Status', 'Comments', 
                        'Tester Name', 'Test MSISDN', 'Test Date and Time']
    
    missing_columns = [col for col in required_columns if col not in df.columns]
    
    if missing_columns:
        return False, missing_columns
    return True, []

def load_data(file):
    """Load and process the Excel file"""
    try:
        df = pd.read_excel(file)
        
        # Validate structure
        is_valid, missing_cols = validate_excel_structure(df)
        if not is_valid:
            st.error(f"❌ Invalid file structure. Missing columns: {', '.join(missing_cols)}")
            st.info("Please upload a file with the following columns: TC #, Stream, Domain, Offer ID, Test Scenario, Expected Result, Actual Result, Status, Comments, Tester Name, Test MSISDN, Test Date and Time")
            return None
        
        # Convert date column to datetime
        if 'Test Date and Time' in df.columns:
            try:
                # Handle both datetime objects and Excel date numbers
                df['Test Date and Time'] = pd.to_datetime(df['Test Date and Time'], errors='coerce')
                # For Excel date numbers (if any)
                mask = df['Test Date and Time'].isna()
                if mask.any():
                    df.loc[mask, 'Test Date and Time'] = pd.to_datetime('1899-12-30') + pd.to_timedelta(df.loc[mask, 'Test Date and Time'], unit='D')
            except:
                df['Test Date and Time'] = pd.to_datetime(df['Test Date and Time'], errors='coerce')
        
        return df
    except Exception as e:
        st.error(f"Error loading file: {str(e)}")
        return None

def create_status_pie_chart(df):
    """Create pie chart for test status distribution"""
    status_counts = df['Status'].value_counts()
    
    colors = {
        'Pass': '#10b981',
        'Fail': '#ef4444', 
        'Blocked': '#f59e0b',
        'Pending': '#6366f1'
    }
    
    fig = px.pie(
        values=status_counts.values,
        names=status_counts.index,
        title='Test Status Distribution',
        color=status_counts.index,
        color_discrete_map=colors,
        hole=0.4
    )
    
    fig.update_traces(
        textposition='inside',
        textinfo='percent+label',
        hovertemplate='<b>%{label}</b><br>Count: %{value}<br>Percentage: %{percent}<extra></extra>'
    )
    
    fig.update_layout(
        showlegend=True,
        height=400,
        font=dict(size=14)
    )
    
    return fig

def create_tester_bug_chart(df):
    """Create bar chart for testers by number of bugs found"""
    bug_df = df[df['Status'].isin(['Fail', 'Blocked'])]
    tester_bugs = bug_df.groupby('Tester Name').size().reset_index(name='Bug Count')
    tester_bugs = tester_bugs.sort_values('Bug Count', ascending=True)
    
    fig = px.bar(
        tester_bugs,
        x='Bug Count',
        y='Tester Name',
        orientation='h',
        title='Testers by Number of Issues Found',
        color='Bug Count',
        color_continuous_scale='Reds',
        text='Bug Count'
    )
    
    fig.update_traces(texttemplate='%{text}', textposition='outside')
    fig.update_layout(
        showlegend=False,
        height=400,
        xaxis_title='Number of Issues',
        yaxis_title='Tester Name'
    )
    
    return fig

def create_offer_status_chart(df):
    """Create stacked bar chart for offers with test case results"""
    offer_status = df.groupby(['Offer ID', 'Status']).size().unstack(fill_value=0)
    offer_status = offer_status.reset_index()
    
    # Get top 15 offers by total test cases
    offer_status['Total'] = offer_status.sum(axis=1, numeric_only=True)
    offer_status = offer_status.nlargest(15, 'Total').drop('Total', axis=1)
    
    fig = go.Figure()
    
    colors = {
        'Pass': '#10b981',
        'Fail': '#ef4444',
        'Blocked': '#f59e0b', 
        'Pending': '#6366f1'
    }
    
    for status in ['Pass', 'Fail', 'Blocked', 'Pending']:
        if status in offer_status.columns:
            fig.add_trace(go.Bar(
                name=status,
                x=offer_status['Offer ID'].astype(str),
                y=offer_status[status],
                marker_color=colors.get(status, '#94a3b8'),
                text=offer_status[status],
                textposition='inside',
                texttemplate='%{text}'
            ))
    
    fig.update_layout(
        barmode='stack',
        title='Top 15 Offers - Test Case Results Distribution',
        xaxis_title='Offer ID',
        yaxis_title='Number of Test Cases',
        height=500,
        showlegend=True,
        hovermode='x unified'
    )
    
    return fig

def display_statistics_page(df):
    """Display the Statistics page"""
    st.title("📊 Testing Statistics Dashboard")
    
    # Calculate metrics
    total_tests = len(df)
    total_offers = df['Offer ID'].nunique()
    total_testers = df['Tester Name'].nunique()
    
    status_counts = df['Status'].value_counts()
    passed = status_counts.get('Pass', 0)
    failed = status_counts.get('Fail', 0)
    blocked = status_counts.get('Blocked', 0)
    pending = status_counts.get('Pending', 0)
    
    pass_rate = (passed/total_tests*100)
    fail_rate = (failed/total_tests*100)
    blocked_rate = (blocked/total_tests*100)
    pending_rate = (pending/total_tests*100)
    issues_total = failed + blocked
    issues_rate = (issues_total/total_tests*100)
    
    # Custom HTML metrics
    st.markdown("""
    <style>
    .metric-row {
        display: flex;
        gap: 20px;
        margin-bottom: 30px;
    }
    .metric-card {
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }
    .metric-label {
        color: #94a3b8;
        font-size: 14px;
        font-weight: 500;
        margin-bottom: 8px;
    }
    .metric-value {
        color: #f1f5f9;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 8px;
    }
    .metric-delta {
        font-size: 14px;
        font-weight: 500;
        padding: 4px 8px;
        border-radius: 6px;
        display: inline-block;
    }
    .delta-positive {
        background-color: rgba(34, 197, 94, 0.2);
        color: #4ade80;
    }
    .delta-negative {
        background-color: rgba(239, 68, 68, 0.2);
        color: #f87171;
    }
    .delta-neutral {
        background-color: rgba(251, 146, 60, 0.2);
        color: #fb923c;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # First row of metrics
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-label">Total Test Cases</div>
            <div class="metric-value">{total_tests:,}</div>
            <div class="metric-delta delta-positive">↑ {passed} passed ({pass_rate:.1f}%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Offers</div>
            <div class="metric-value">{total_offers:,}</div>
            <div class="metric-delta delta-negative">↓ {failed} failed ({fail_rate:.1f}%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Testers</div>
            <div class="metric-value">{total_testers:,}</div>
            <div class="metric-delta delta-neutral">⚠ {blocked} blocked ({blocked_rate:.1f}%)</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Passed Tests</div>
            <div class="metric-value">{passed:,}</div>
            <div class="metric-delta delta-positive">✓ {pass_rate:.1f}%</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Failed Tests</div>
            <div class="metric-value">{failed:,}</div>
            <div class="metric-delta delta-negative">✗ {fail_rate:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Second row of metrics
    st.markdown(f"""
    <div class="metric-row">
        <div class="metric-card">
            <div class="metric-label">Pass Rate</div>
            <div class="metric-value">{pass_rate:.1f}%</div>
            <div class="metric-delta delta-positive">↑ {passed} passed</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Fail Rate</div>
            <div class="metric-value">{fail_rate:.1f}%</div>
            <div class="metric-delta delta-negative">↓ {failed} failed</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Blocked Rate</div>
            <div class="metric-value">{blocked_rate:.1f}%</div>
            <div class="metric-delta delta-neutral">⚠ {blocked} blocked</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Pending Rate</div>
            <div class="metric-value">{pending_rate:.1f}%</div>
            <div class="metric-delta delta-neutral">⏳ {pending} pending</div>
        </div>
        <div class="metric-card">
            <div class="metric-label">Total Issues</div>
            <div class="metric-value">{issues_total:,}</div>
            <div class="metric-delta delta-negative">↓ {issues_rate:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Charts
    col1, col2 = st.columns(2)
    
    with col1:
        fig_pie = create_status_pie_chart(df)
        st.plotly_chart(fig_pie, use_container_width=True)
    
    with col2:
        fig_tester = create_tester_bug_chart(df)
        st.plotly_chart(fig_tester, use_container_width=True)
    
    # Offer status chart
    st.markdown("---")
    fig_offer = create_offer_status_chart(df)
    st.plotly_chart(fig_offer, use_container_width=True)
    
    # Additional Statistics
    st.markdown("---")
    st.subheader("🎯 Detailed Statistics by Category")
    
    tab1, tab2, tab3 = st.tabs(["By Stream", "By Domain", "By Date"])
    
    with tab1:
        stream_stats = df.groupby(['Stream', 'Status']).size().unstack(fill_value=0)
        st.dataframe(stream_stats, use_container_width=True)
    
    with tab2:
        domain_stats = df.groupby(['Domain', 'Status']).size().unstack(fill_value=0)
        st.dataframe(domain_stats, use_container_width=True)
    
    with tab3:
        df['Date'] = pd.to_datetime(df['Test Date and Time']).dt.date
        date_stats = df.groupby(['Date', 'Status']).size().unstack(fill_value=0)
        st.dataframe(date_stats, use_container_width=True)

def display_issues_page(df):
    """Display the Issues page"""
    st.title("🐛 Issues Tracker")
    
    # Filter for issues (Failed, Blocked, Pending)
    issues_df = df[df['Status'].isin(['Fail', 'Blocked', 'Pending'])].copy()
    
    if issues_df.empty:
        st.success("🎉 No issues found! All tests have passed.")
        return
    
    # Add date column
    issues_df['Date'] = pd.to_datetime(issues_df['Test Date and Time']).dt.date
    
    # Date filter
    st.subheader("📅 Filter by Date")
    col1, col2 = st.columns(2)
    
    with col1:
        min_date = issues_df['Date'].min()
        max_date = issues_df['Date'].max()
        selected_date = st.date_input(
            "Select Date",
            value=max_date,
            min_value=min_date,
            max_value=max_date
        )
    
    with col2:
        status_filter = st.multiselect(
            "Filter by Status",
            options=['Fail', 'Blocked', 'Pending'],
            default=['Fail', 'Blocked', 'Pending']
        )
    
    # Filter data
    filtered_issues = issues_df[
        (issues_df['Date'] == selected_date) & 
        (issues_df['Status'].isin(status_filter))
    ]
    
    # Display metrics using custom HTML
    total_issues = len(filtered_issues)
    failed_count = len(filtered_issues[filtered_issues['Status'] == 'Fail'])
    blocked_count = len(filtered_issues[filtered_issues['Status'] == 'Blocked'])
    pending_count = len(filtered_issues[filtered_issues['Status'] == 'Pending'])
    
    st.markdown(f"""
    <style>
    .issues-metrics {{
        display: flex;
        gap: 20px;
        margin: 20px 0;
    }}
    .issue-metric-card {{
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        text-align: center;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    .issue-metric-label {{
        color: #94a3b8;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
    }}
    .issue-metric-value {{
        color: #f1f5f9;
        font-size: 36px;
        font-weight: 700;
    }}
    .failed-card {{
        background: linear-gradient(135deg, #7f1d1d 0%, #991b1b 100%);
    }}
    .blocked-card {{
        background: linear-gradient(135deg, #78350f 0%, #92400e 100%);
    }}
    .pending-card {{
        background: linear-gradient(135deg, #4c1d95 0%, #5b21b6 100%);
    }}
    </style>
    
    <div class="issues-metrics">
        <div class="issue-metric-card">
            <div class="issue-metric-label">Total Issues</div>
            <div class="issue-metric-value">{total_issues}</div>
        </div>
        <div class="issue-metric-card failed-card">
            <div class="issue-metric-label">Failed</div>
            <div class="issue-metric-value">{failed_count}</div>
        </div>
        <div class="issue-metric-card blocked-card">
            <div class="issue-metric-label">Blocked</div>
            <div class="issue-metric-value">{blocked_count}</div>
        </div>
        <div class="issue-metric-card pending-card">
            <div class="issue-metric-label">Pending</div>
            <div class="issue-metric-value">{pending_count}</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Display issues table
    st.subheader(f"📋 Issues for {selected_date}")
    
    if not filtered_issues.empty:
        # Reorder columns as requested: Offer ID, Tester Name, Test Scenario, Status, Comments, Date
        display_df = filtered_issues[['Offer ID', 'Tester Name', 'Test Scenario', 'Status', 'Comments', 'Date']].copy()
        
        # Truncate long text for display
        display_df['Test Scenario'] = display_df['Test Scenario'].apply(lambda x: x[:50] + '...' if len(str(x)) > 50 else x)
        # Truncate long text for display
        display_df['Test Scenario'] = display_df['Test Scenario'].apply(lambda x: x[:50] + '...' if len(str(x)) > 50 else x)
        display_df['Comments'] = display_df['Comments'].fillna('').apply(lambda x: x[:40] + '...' if len(str(x)) > 40 else x)
        display_df = display_df.reset_index(drop=True)
        
        # Create a styled dataframe with better visibility
        def style_status(val):
            if val == 'Fail':
                return 'background-color: #dc2626; color: white; font-weight: bold'
            elif val == 'Blocked':
                return 'background-color: #ea580c; color: white; font-weight: bold'
            elif val == 'Pending':
                return 'background-color: #7c3aed; color: white; font-weight: bold'
            return ''
        
        # Apply styling to the dataframe
        styled_df = display_df.style.applymap(style_status, subset=['Status']).set_properties(**{
            'background-color': '#1e293b',
            'color': 'white',
            'border': '1px solid #334155'
        }).set_table_styles([
            {'selector': 'thead', 'props': [('background-color', '#334155'), ('color', 'white')]},
            {'selector': 'tbody tr:hover', 'props': [('background-color', '#334155')]}
        ])
        
        # Display with custom CSS for better visibility
        st.markdown("""
        <style>
        /* Override default table styling for better visibility */
        .dataframe {
            font-size: 14px !important;
        }
        .dataframe thead tr th {
            background-color: #334155 !important;
            color: white !important;
            font-weight: bold !important;
            text-align: left !important;
            padding: 10px !important;
        }
        .dataframe tbody tr {
            background-color: #1e293b !important;
            color: white !important;
        }
        .dataframe tbody tr:nth-child(even) {
            background-color: #0f172a !important;
        }
        .dataframe tbody tr:hover {
            background-color: #334155 !important;
        }
        .dataframe tbody td {
            padding: 8px !important;
            border: 1px solid #475569 !important;
        }
        </style>
        """, unsafe_allow_html=True)
        
        st.dataframe(display_df, use_container_width=True, height=400)
        
        # Download button
        st.subheader("📥 Export Issues")
        
        # Create Excel file with better formatting
        output = BytesIO()
        with pd.ExcelWriter(output, engine='openpyxl') as writer:
            # Include only the specified columns: Offer ID, Tester Name, Test Scenario, Status, Comments, Date
            export_df = filtered_issues[['Offer ID', 'Tester Name', 'Test Scenario', 'Status', 
                                        'Comments', 'Date']].reset_index(drop=True)
            export_df.to_excel(writer, sheet_name=f'Issues_{selected_date}', index=False)
            
            # Get the workbook and worksheet
            workbook = writer.book
            worksheet = writer.sheets[f'Issues_{selected_date}']
            
            # Add formatting
            from openpyxl.styles import Font, PatternFill, Alignment
            
            # Header formatting
            header_font = Font(bold=True, color="FFFFFF")
            header_fill = PatternFill(start_color="334155", end_color="334155", fill_type="solid")
            header_alignment = Alignment(horizontal="center", vertical="center")
            
            for cell in worksheet[1]:
                cell.font = header_font
                cell.fill = header_fill
                cell.alignment = header_alignment
            
            # Auto-adjust column widths
            for column in worksheet.columns:
                max_length = 0
                column_letter = column[0].column_letter
                for cell in column:
                    try:
                        if len(str(cell.value)) > max_length:
                            max_length = len(str(cell.value))
                    except:
                        pass
                adjusted_width = min(max_length + 2, 50)
                worksheet.column_dimensions[column_letter].width = adjusted_width
        
        output.seek(0)
        
        st.download_button(
            label=f"📥 Download Issues for {selected_date} (Excel)",
            data=output,
            file_name=f"issues_{selected_date}.xlsx",
            mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
    else:
        st.info("No issues found for the selected date and filters.")
    
    # Overall issues summary
    st.markdown("---")
    st.subheader("📊 Issues Summary by Date")
    
    issues_by_date = issues_df.groupby(['Date', 'Status']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    colors = {'Fail': '#ef4444', 'Blocked': '#f59e0b', 'Pending': '#6366f1'}
    
    for status in ['Fail', 'Blocked', 'Pending']:
        if status in issues_by_date.columns:
            fig.add_trace(go.Scatter(
                x=issues_by_date.index,
                y=issues_by_date[status],
                mode='lines+markers',
                name=status,
                line=dict(color=colors.get(status), width=2),
                marker=dict(size=8)
            ))
    
    fig.update_layout(
        title='Issues Trend Over Time',
        xaxis_title='Date',
        yaxis_title='Number of Issues',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)

def display_comparison_page(df):
    """Display the Comparison page for conflicting test results"""
    st.title("🔄 Test Result Comparison")
    st.markdown("Identifying test cases with conflicting results from different testers")
    
    # Find test cases with different results
    grouped = df.groupby(['Offer ID', 'TC #', 'Test Scenario'])
    
    conflicts = []
    
    for (offer_id, tc_num, scenario), group in grouped:
        if len(group['Tester Name'].unique()) > 1:
            statuses = group[['Tester Name', 'Status', 'Actual Result']].values
            unique_statuses = group['Status'].unique()
            
            if len(unique_statuses) > 1:
                for i, row1 in enumerate(statuses):
                    for row2 in statuses[i+1:]:
                        if row1[1] != row2[1]:  # Different status
                            conflicts.append({
                                'Offer ID': offer_id,
                                'TC #': tc_num,
                                'Test Scenario': scenario[:50] + '...' if len(scenario) > 50 else scenario,
                                'Tester 1': row1[0],
                                'Status 1': row1[1],
                                'Result 1': row1[2],
                                'Tester 2': row2[0],
                                'Status 2': row2[1],
                                'Result 2': row2[2]
                            })
    
    if conflicts:
        conflicts_df = pd.DataFrame(conflicts)
        
        # Display metrics with custom HTML
        total_conflicts = len(conflicts_df)
        affected_offers = conflicts_df['Offer ID'].nunique()
        affected_test_cases = conflicts_df['TC #'].nunique()
        
        st.markdown(f"""
        <style>
        .comparison-metrics {{
            display: flex;
            gap: 20px;
            margin: 20px 0 30px 0;
        }}
        .comparison-card {{
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 12px;
            padding: 25px;
            flex: 1;
            text-align: center;
            border: 1px solid #475569;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            transition: transform 0.2s;
        }}
        .comparison-card:hover {{
            transform: translateY(-5px);
            box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
        }}
        .comparison-label {{
            color: #94a3b8;
            font-size: 14px;
            font-weight: 600;
            margin-bottom: 10px;
            text-transform: uppercase;
            letter-spacing: 1px;
        }}
        .comparison-value {{
            color: #f1f5f9;
            font-size: 36px;
            font-weight: 700;
        }}
        .conflicts-card {{
            background: linear-gradient(135deg, #dc2626 0%, #ef4444 100%);
        }}
        </style>
        
        <div class="comparison-metrics">
            <div class="comparison-card conflicts-card">
                <div class="comparison-label">Total Conflicts</div>
                <div class="comparison-value">{total_conflicts}</div>
            </div>
            <div class="comparison-card">
                <div class="comparison-label">Affected Offers</div>
                <div class="comparison-value">{affected_offers}</div>
            </div>
            <div class="comparison-card">
                <div class="comparison-label">Affected Test Cases</div>
                <div class="comparison-value">{affected_test_cases}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        # Filter options
        st.subheader("🔍 Filter Conflicts")
        col1, col2 = st.columns(2)
        
        with col1:
            selected_offer = st.selectbox(
                "Filter by Offer ID",
                options=['All'] + sorted(conflicts_df['Offer ID'].unique().tolist()),
                index=0
            )
        
        with col2:
            selected_tester = st.selectbox(
                "Filter by Tester",
                options=['All'] + sorted(list(set(conflicts_df['Tester 1'].unique().tolist() + 
                                                 conflicts_df['Tester 2'].unique().tolist()))),
                index=0
            )
        
        # Apply filters
        filtered_conflicts = conflicts_df.copy()
        
        if selected_offer != 'All':
            filtered_conflicts = filtered_conflicts[filtered_conflicts['Offer ID'] == selected_offer]
        
        if selected_tester != 'All':
            filtered_conflicts = filtered_conflicts[
                (filtered_conflicts['Tester 1'] == selected_tester) | 
                (filtered_conflicts['Tester 2'] == selected_tester)
            ]
        
        # Display conflicts
        st.subheader("⚠️ Conflicting Test Results")
        
        for idx, conflict in filtered_conflicts.iterrows():
            with st.expander(f"Conflict #{idx+1}: TC {conflict['TC #']} - Offer {conflict['Offer ID']}"):
                st.markdown(f"**Test Scenario:** {conflict['Test Scenario']}")
                
                col1, col2 = st.columns(2)
                
                with col1:
                    if conflict['Status 1'] == 'Pass':
                        st.success(f"✅ **{conflict['Tester 1']}**: {conflict['Status 1']}")
                    elif conflict['Status 1'] == 'Fail':
                        st.error(f"❌ **{conflict['Tester 1']}**: {conflict['Status 1']}")
                    else:
                        st.warning(f"⚠️ **{conflict['Tester 1']}**: {conflict['Status 1']}")
                    st.write(f"Result: {conflict['Result 1']}")
                
                with col2:
                    if conflict['Status 2'] == 'Pass':
                        st.success(f"✅ **{conflict['Tester 2']}**: {conflict['Status 2']}")
                    elif conflict['Status 2'] == 'Fail':
                        st.error(f"❌ **{conflict['Tester 2']}**: {conflict['Status 2']}")
                    else:
                        st.warning(f"⚠️ **{conflict['Tester 2']}**: {conflict['Status 2']}")
                    st.write(f"Result: {conflict['Result 2']}")
        
        # Summary chart
        st.markdown("---")
        st.subheader("📈 Conflict Analysis")
        
        # Testers involved in conflicts
        tester_conflicts = pd.concat([
            conflicts_df['Tester 1'].value_counts(),
            conflicts_df['Tester 2'].value_counts()
        ]).groupby(level=0).sum().sort_values(ascending=False)
        
        fig = px.bar(
            x=tester_conflicts.values,
            y=tester_conflicts.index,
            orientation='h',
            title='Testers Involved in Conflicts',
            labels={'x': 'Number of Conflicts', 'y': 'Tester Name'},
            color=tester_conflicts.values,
            color_continuous_scale='Reds'
        )
        
        st.plotly_chart(fig, use_container_width=True)
        
    else:
        st.success("✅ No conflicting test results found! All testers agree on test outcomes.")

def extract_issue_patterns(comment):
    """Extract common patterns from comments"""
    if pd.isna(comment) or comment == 'As Expected':
        return []
    
    comment_lower = str(comment).lower()
    
    patterns = []
    
    # Common issue keywords
    keywords = {
        'balance': ['balance', 'deduction', 'charge', 'tariff'],
        'api': ['api', 'interface', 'endpoint'],
        'gui': ['gui', 'display', 'screen', 'interface'],
        'network': ['network', 'connection', 'timeout', 'latency'],
        'validation': ['validation', 'verify', 'check', 'confirm'],
        'data': ['data', 'information', 'record'],
        'error': ['error', 'exception', 'fail', 'crash'],
        'performance': ['slow', 'performance', 'delay', 'lag'],
        'configuration': ['config', 'setting', 'parameter'],
        'authentication': ['auth', 'login', 'permission', 'access']
    }
    
    for category, words in keywords.items():
        for word in words:
            if word in comment_lower:
                patterns.append(category)
                break
    
    return patterns

def display_summary_page(df):
    """Display the Summary page with bug analysis"""
    st.title("📝 Test Summary & Analysis")
    
    # Overall summary with custom HTML
    total_tests = len(df)
    pass_rate = (df['Status'] == 'Pass').sum() / total_tests * 100
    fail_rate = (df['Status'] == 'Fail').sum() / total_tests * 100
    test_coverage = df['Offer ID'].nunique()
    team_size = df['Tester Name'].nunique()
    
    st.subheader("🎯 Executive Summary")
    
    st.markdown(f"""
    <style>
    .summary-metrics {{
        display: flex;
        gap: 20px;
        margin: 20px 0 30px 0;
    }}
    .summary-card {{
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 25px;
        flex: 1;
        text-align: center;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
    }}
    .summary-label {{
        color: #94a3b8;
        font-size: 14px;
        font-weight: 600;
        margin-bottom: 10px;
        text-transform: uppercase;
    }}
    .summary-value {{
        color: #f1f5f9;
        font-size: 32px;
        font-weight: 700;
        margin-bottom: 5px;
    }}
    .summary-status {{
        font-size: 14px;
        font-weight: 600;
        padding: 4px 10px;
        border-radius: 20px;
        display: inline-block;
        margin-top: 5px;
    }}
    .status-good {{
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
    }}
    .status-warning {{
        background: rgba(251, 146, 60, 0.2);
        color: #fb923c;
    }}
    .status-bad {{
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
    }}
    </style>
    
    <div class="summary-metrics">
        <div class="summary-card">
            <div class="summary-label">Overall Pass Rate</div>
            <div class="summary-value">{pass_rate:.1f}%</div>
            <div class="summary-status {'status-good' if pass_rate >= 80 else 'status-warning' if pass_rate >= 60 else 'status-bad'}">
                {'✅ Excellent' if pass_rate >= 80 else '⚠️ Needs Attention' if pass_rate >= 60 else '❌ Critical'}
            </div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Test Coverage</div>
            <div class="summary-value">{test_coverage}</div>
            <div class="summary-status status-good">offers tested</div>
        </div>
        <div class="summary-card">
            <div class="summary-label">Testing Team Size</div>
            <div class="summary-value">{team_size}</div>
            <div class="summary-status status-good">active testers</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Bug analysis by offer
    st.subheader("🐛 Issue Analysis by Offer")
    
    failed_tests = df[df['Status'].isin(['Fail', 'Blocked'])]
    
    if not failed_tests.empty:
        offer_issues = {}
        
        for offer_id in failed_tests['Offer ID'].unique():
            offer_data = failed_tests[failed_tests['Offer ID'] == offer_id]
            
            # Extract patterns from comments
            all_patterns = []
            for comment in offer_data['Actual Result']:
                patterns = extract_issue_patterns(comment)
                all_patterns.extend(patterns)
            
            # Count pattern frequencies
            pattern_counts = Counter(all_patterns)
            
            # Get most common test scenarios that failed
            failed_scenarios = offer_data['Test Scenario'].value_counts().head(3)
            
            offer_issues[offer_id] = {
                'total_issues': len(offer_data),
                'fail_count': (offer_data['Status'] == 'Fail').sum(),
                'blocked_count': (offer_data['Status'] == 'Blocked').sum(),
                'patterns': pattern_counts,
                'top_failed_scenarios': failed_scenarios
            }
        
        # Custom HTML for offer analysis cards
        st.markdown("""
        <style>
        .offer-analysis-card {
            background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
            border-radius: 12px;
            padding: 20px;
            margin-bottom: 20px;
            border: 1px solid #475569;
            box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        }
        .offer-header {
            color: #f1f5f9;
            font-size: 18px;
            font-weight: 700;
            margin-bottom: 15px;
            padding-bottom: 10px;
            border-bottom: 2px solid #475569;
        }
        .offer-metrics {
            display: flex;
            gap: 15px;
            margin-bottom: 15px;
        }
        .offer-metric {
            background: rgba(30, 41, 59, 0.5);
            border-radius: 8px;
            padding: 10px 15px;
            flex: 1;
            text-align: center;
        }
        .offer-metric-label {
            color: #94a3b8;
            font-size: 11px;
            text-transform: uppercase;
            margin-bottom: 5px;
        }
        .offer-metric-value {
            color: #f1f5f9;
            font-size: 24px;
            font-weight: 700;
        }
        .section-title {
            color: #cbd5e1;
            font-size: 14px;
            font-weight: 600;
            margin: 15px 0 10px 0;
        }
        .issue-item {
            color: #e2e8f0;
            font-size: 13px;
            margin: 5px 0;
            padding-left: 15px;
            position: relative;
        }
        .issue-item:before {
            content: "•";
            position: absolute;
            left: 0;
            color: #7c3aed;
        }
        .recommendation-item {
            color: #4ade80;
            font-size: 13px;
            margin: 5px 0;
            padding-left: 15px;
            position: relative;
        }
        .recommendation-item:before {
            content: "•";
            position: absolute;
            left: 0;
            color: #4ade80;
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Display analysis for each offer
        for offer_id, analysis in sorted(offer_issues.items(), 
                                        key=lambda x: x[1]['total_issues'], 
                                        reverse=True)[:10]:  # Top 10 problematic offers
            
            with st.expander(f"Offer {offer_id} - {analysis['total_issues']} issues"):
                # Create custom HTML content
                metrics_html = f"""
                <div class="offer-metrics">
                    <div class="offer-metric">
                        <div class="offer-metric-label">Total Issues</div>
                        <div class="offer-metric-value">{analysis['total_issues']}</div>
                    </div>
                    <div class="offer-metric">
                        <div class="offer-metric-label">Failed</div>
                        <div class="offer-metric-value" style="color: #f87171;">{analysis['fail_count']}</div>
                    </div>
                    <div class="offer-metric">
                        <div class="offer-metric-label">Blocked</div>
                        <div class="offer-metric-value" style="color: #fb923c;">{analysis['blocked_count']}</div>
                    </div>
                </div>
                """
                st.markdown(metrics_html, unsafe_allow_html=True)
                
                if analysis['patterns']:
                    patterns_html = "<div class='section-title'>🔍 Common Issue Categories:</div>"
                    for category, count in analysis['patterns'].most_common(3):
                        patterns_html += f"<div class='issue-item'>{category.capitalize()}: {count} occurrences</div>"
                    st.markdown(patterns_html, unsafe_allow_html=True)
                
                if not analysis['top_failed_scenarios'].empty:
                    scenarios_html = "<div class='section-title'>📋 Most Problematic Test Scenarios:</div>"
                    for scenario, count in analysis['top_failed_scenarios'].items():
                        scenarios_html += f"<div class='issue-item'>{scenario[:60]}... ({count} failures)</div>"
                    st.markdown(scenarios_html, unsafe_allow_html=True)
                
                # Provide recommendations
                recommendations_html = "<div class='section-title'>💡 Recommendations:</div>"
                if 'balance' in analysis['patterns']:
                    recommendations_html += "<div class='recommendation-item'>Review balance deduction logic and tariff calculations</div>"
                if 'api' in analysis['patterns']:
                    recommendations_html += "<div class='recommendation-item'>Check API endpoints and response handling</div>"
                if 'gui' in analysis['patterns']:
                    recommendations_html += "<div class='recommendation-item'>Verify UI components and display logic</div>"
                if 'network' in analysis['patterns']:
                    recommendations_html += "<div class='recommendation-item'>Investigate network connectivity and timeout issues</div>"
                if 'validation' in analysis['patterns']:
                    recommendations_html += "<div class='recommendation-item'>Review validation rules and data integrity checks</div>"
                st.markdown(recommendations_html, unsafe_allow_html=True)
    else:
        st.success("🎉 No issues found across all offers!")
    
    # Tester performance summary
    st.markdown("---")
    st.subheader("👥 Tester Performance Summary")
    
    tester_stats = df.groupby('Tester Name').agg({
        'TC #': 'count',
        'Status': lambda x: (x == 'Pass').sum()
    }).rename(columns={'TC #': 'Total Tests', 'Status': 'Passed Tests'})
    
    tester_stats['Pass Rate (%)'] = (tester_stats['Passed Tests'] / tester_stats['Total Tests'] * 100).round(1)
    tester_stats = tester_stats.sort_values('Pass Rate (%)', ascending=False)
    
    # Create a performance chart
    fig = go.Figure()
    
    fig.add_trace(go.Bar(
        x=tester_stats.index,
        y=tester_stats['Total Tests'],
        name='Total Tests',
        marker_color='lightblue',
        yaxis='y',
        offsetgroup=1
    ))
    
    fig.add_trace(go.Bar(
        x=tester_stats.index,
        y=tester_stats['Passed Tests'],
        name='Passed Tests',
        marker_color='green',
        yaxis='y',
        offsetgroup=2
    ))
    
    fig.add_trace(go.Scatter(
        x=tester_stats.index,
        y=tester_stats['Pass Rate (%)'],
        name='Pass Rate (%)',
        yaxis='y2',
        mode='lines+markers',
        marker=dict(color='red', size=10),
        line=dict(color='red', width=2)
    ))
    
    fig.update_layout(
        title='Tester Performance Overview',
        xaxis=dict(title='Tester Name'),
        yaxis=dict(title='Number of Tests', side='left'),
        yaxis2=dict(title='Pass Rate (%)', overlaying='y', side='right', range=[0, 100]),
        hovermode='x unified',
        barmode='group',
        height=500
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Display tester statistics table
    st.dataframe(tester_stats.style.background_gradient(subset=['Pass Rate (%)'], cmap='RdYlGn'), 
                 use_container_width=True)
    
    # Test coverage summary
    st.markdown("---")
    st.subheader("📊 Test Coverage Analysis")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # Stream coverage
        stream_coverage = df.groupby('Stream')['Status'].value_counts().unstack(fill_value=0)
        fig_stream = px.bar(
            stream_coverage.T,
            title='Test Coverage by Stream',
            labels={'value': 'Count', 'index': 'Status'},
            color_discrete_map={'Pass': '#10b981', 'Fail': '#ef4444', 'Blocked': '#f59e0b', 'Pending': '#6366f1'}
        )
        st.plotly_chart(fig_stream, use_container_width=True)
    
    with col2:
        # Domain coverage
        domain_coverage = df.groupby('Domain')['Status'].value_counts().unstack(fill_value=0)
        top_domains = domain_coverage.sum(axis=1).nlargest(10).index
        domain_coverage_top = domain_coverage.loc[top_domains]
        
        fig_domain = px.bar(
            domain_coverage_top.T,
            title='Test Coverage by Top 10 Domains',
            labels={'value': 'Count', 'index': 'Status'},
            color_discrete_map={'Pass': '#10b981', 'Fail': '#ef4444', 'Blocked': '#f59e0b', 'Pending': '#6366f1'}
        )
        st.plotly_chart(fig_domain, use_container_width=True)

def display_tester_statistics(df):
    """Display individual tester statistics"""
    st.title("👤 Individual Tester Statistics")
    
    selected_tester = st.selectbox(
        "Select a Tester",
        options=sorted(df['Tester Name'].unique())
    )
    
    tester_data = df[df['Tester Name'] == selected_tester]
    
    # Calculate metrics
    total_tests = len(tester_data)
    passed = (tester_data['Status'] == 'Pass').sum()
    failed = (tester_data['Status'] == 'Fail').sum()
    blocked = (tester_data['Status'] == 'Blocked').sum()
    pending = (tester_data['Status'] == 'Pending').sum()
    pass_rate = (passed/total_tests*100) if total_tests > 0 else 0
    fail_rate = (failed/total_tests*100) if total_tests > 0 else 0
    blocked_rate = (blocked/total_tests*100) if total_tests > 0 else 0
    pending_rate = (pending/total_tests*100) if total_tests > 0 else 0
    
    # Display metrics with custom HTML
    st.markdown(f"""
    <style>
    .tester-metrics {{
        display: flex;
        gap: 20px;
        margin: 20px 0 30px 0;
    }}
    .tester-card {{
        background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
        border-radius: 12px;
        padding: 20px;
        flex: 1;
        text-align: center;
        border: 1px solid #475569;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        min-width: 150px;
    }}
    .tester-label {{
        color: #94a3b8;
        font-size: 13px;
        font-weight: 600;
        margin-bottom: 8px;
        text-transform: uppercase;
    }}
    .tester-value {{
        color: #f1f5f9;
        font-size: 28px;
        font-weight: 700;
        margin-bottom: 5px;
    }}
    .tester-percent {{
        font-size: 14px;
        padding: 3px 8px;
        border-radius: 15px;
        display: inline-block;
        font-weight: 600;
    }}
    .percent-pass {{
        background: rgba(34, 197, 94, 0.2);
        color: #4ade80;
    }}
    .percent-fail {{
        background: rgba(239, 68, 68, 0.2);
        color: #f87171;
    }}
    .percent-blocked {{
        background: rgba(251, 146, 60, 0.2);
        color: #fb923c;
    }}
    .percent-pending {{
        background: rgba(168, 85, 247, 0.2);
        color: #c084fc;
    }}
    .tester-name-card {{
        background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
        margin-bottom: 20px;
        padding: 25px;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 6px 12px rgba(79, 70, 229, 0.3);
    }}
    .tester-name {{
        color: white;
        font-size: 24px;
        font-weight: 700;
        margin: 0;
    }}
    </style>
    
    <div class="tester-name-card">
        <div class="tester-name">📊 {selected_tester}'s Performance</div>
    </div>
    
    <div class="tester-metrics">
        <div class="tester-card">
            <div class="tester-label">Total Tests</div>
            <div class="tester-value">{total_tests}</div>
        </div>
        <div class="tester-card">
            <div class="tester-label">Passed</div>
            <div class="tester-value">{passed}</div>
            <div class="tester-percent percent-pass">{pass_rate:.1f}%</div>
        </div>
        <div class="tester-card">
            <div class="tester-label">Failed</div>
            <div class="tester-value">{failed}</div>
            <div class="tester-percent percent-fail">{fail_rate:.1f}%</div>
        </div>
        <div class="tester-card">
            <div class="tester-label">Blocked</div>
            <div class="tester-value">{blocked}</div>
            <div class="tester-percent percent-blocked">{blocked_rate:.1f}%</div>
        </div>
        <div class="tester-card">
            <div class="tester-label">Pending</div>
            <div class="tester-value">{pending}</div>
            <div class="tester-percent percent-pending">{pending_rate:.1f}%</div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("---")
    
    # Performance over time
    tester_data['Date'] = pd.to_datetime(tester_data['Test Date and Time']).dt.date
    daily_performance = tester_data.groupby(['Date', 'Status']).size().unstack(fill_value=0)
    
    fig = go.Figure()
    colors = {'Pass': '#10b981', 'Fail': '#ef4444', 'Blocked': '#f59e0b', 'Pending': '#6366f1'}
    
    for status in daily_performance.columns:
        fig.add_trace(go.Scatter(
            x=daily_performance.index,
            y=daily_performance[status],
            mode='lines+markers',
            name=status,
            line=dict(color=colors.get(status), width=2),
            stackgroup='one'
        ))
    
    fig.update_layout(
        title=f'{selected_tester} - Daily Test Performance',
        xaxis_title='Date',
        yaxis_title='Number of Tests',
        height=400,
        hovermode='x unified'
    )
    
    st.plotly_chart(fig, use_container_width=True)
    
    # Test coverage by offer
    st.subheader(f"📦 {selected_tester}'s Test Coverage by Offer")
    offer_coverage = tester_data.groupby(['Offer ID', 'Status']).size().unstack(fill_value=0)
    st.dataframe(offer_coverage, use_container_width=True)
    
    # Recent test activities
    st.subheader(f"📝 Recent Test Activities")
    recent_tests = tester_data.nlargest(10, 'Test Date and Time')[
        ['Test Date and Time', 'Offer ID', 'Test Scenario', 'Status', 'Actual Result']
    ]
    st.dataframe(recent_tests, use_container_width=True)

def main():
    # Sidebar
    with st.sidebar:
        st.markdown("""
        <div style='text-align: center; padding: 10px; background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); border-radius: 10px; margin-bottom: 20px;'>
            <h2 style='color: white; margin: 0; font-size: 1.5rem;'>Data Analytics Tool for Price Plans and Offers</h2>
            <p style='color: #e0e7ff; margin: 5px 0 0 0; font-size: 0.9rem; font-style: italic;'>Sensitivity: Internal</p>
        </div>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        # File upload
        st.subheader("📁 Upload Excel File")
        uploaded_file = st.file_uploader("Choose an Excel file", type=['xlsx', 'xls'])
        
        if uploaded_file is not None:
            with st.spinner('Loading data...'):
                data = load_data(uploaded_file)
                if data is not None:
                    st.session_state.data = data
                    st.session_state.file_uploaded = True
                    st.success(f"✅ Loaded {len(data)} test records")
        
        st.markdown("---")
        
        # Navigation
        if st.session_state.file_uploaded:
            st.subheader("📍 Navigation")
            page = st.radio(
                "Select Page",
                ["🏠 Home", "📊 Statistics", "🐛 Issues", "🔄 Comparison", "📝 Summary", "👤 Tester Stats"],
                label_visibility="collapsed"
            )
        else:
            page = "🏠 Home"
        
        st.markdown("---")
        
        # Quick Stats Panel instead of animations
        if st.session_state.file_uploaded and st.session_state.data is not None:
            df_stats = st.session_state.data
            total_tests = len(df_stats)
            pass_percent = (df_stats['Status'] == 'Pass').sum() / total_tests * 100 if total_tests > 0 else 0
            today_tests = len(df_stats[pd.to_datetime(df_stats['Test Date and Time']).dt.date == datetime.now().date()])
            
            st.markdown(f"""
            <style>
            .sidebar-stats {{
                background: linear-gradient(135deg, #4f46e5 0%, #7c3aed 100%);
                border-radius: 15px;
                padding: 15px;
                margin: 15px 0;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
            }}
            .stat-row {{
                display: flex;
                justify-content: space-between;
                align-items: center;
                margin: 8px 0;
                padding: 5px 0;
                border-bottom: 1px solid rgba(255, 255, 255, 0.1);
            }}
            .stat-label {{
                color: rgba(255, 255, 255, 0.9);
                font-size: 12px;
                font-weight: 500;
            }}
            .stat-value {{
                color: white;
                font-size: 14px;
                font-weight: 700;
            }}
            .quick-actions {{
                background: rgba(30, 41, 59, 0.8);
                border-radius: 12px;
                padding: 12px;
                margin: 15px 0;
            }}
            .action-title {{
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 10px;
                text-align: center;
            }}
            .tip-box {{
                background: linear-gradient(135deg, #065f46 0%, #047857 100%);
                border-radius: 10px;
                padding: 12px;
                margin: 10px 0;
            }}
            .tip-text {{
                color: white;
                font-size: 12px;
                line-height: 1.4;
                text-align: center;
            }}
            </style>
            
            <div class="sidebar-stats">
                <div class="stat-row">
                    <span class="stat-label">📊 Total Tests</span>
                    <span class="stat-value">{total_tests:,}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">✅ Pass Rate</span>
                    <span class="stat-value">{pass_percent:.1f}%</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">📅 Today's Tests</span>
                    <span class="stat-value">{today_tests}</span>
                </div>
                <div class="stat-row">
                    <span class="stat-label">👥 Active Testers</span>
                    <span class="stat-value">{df_stats['Tester Name'].nunique()}</span>
                </div>
            </div>
            
            <div class="quick-actions">
                <div class="action-title">⚡ Quick Tips</div>
                <div class="tip-box">
                    <div class="tip-text">
                        {'💡 Check the Comparison page to find conflicting test results!' if pass_percent < 80 else '🎯 Great pass rate! Review the Summary for insights.'}
                    </div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        else:
            # When no file is uploaded, show helpful info
            st.markdown("""
            <style>
            .help-panel {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 15px;
                padding: 20px;
                margin: 15px 0;
            }}
            .help-title {{
                color: #f1f5f9;
                font-size: 14px;
                font-weight: 700;
                margin-bottom: 15px;
                text-align: center;
            }}
            .help-item {{
                color: #cbd5e1;
                font-size: 12px;
                margin: 8px 0;
                padding-left: 20px;
                position: relative;
            }}
            .help-item:before {{
                content: "→";
                position: absolute;
                left: 0;
                color: #7c3aed;
            }}
            .status-legend {{
                background: rgba(30, 41, 59, 0.8);
                border-radius: 12px;
                padding: 15px;
                margin: 15px 0;
            }}
            .legend-title {{
                color: #e2e8f0;
                font-size: 13px;
                font-weight: 600;
                margin-bottom: 10px;
                text-align: center;
            }}
            .legend-item {{
                display: flex;
                align-items: center;
                margin: 8px 0;
            }}
            .legend-color {{
                width: 20px;
                height: 20px;
                border-radius: 5px;
                margin-right: 10px;
            }}
            .legend-text {{
                color: #cbd5e1;
                font-size: 12px;
            }}
            </style>
            
            <div class="help-panel">
                <div class="help-title">📋 Required Excel Columns</div>
                <div class="help-item">TC # (Test Case Number)</div>
                <div class="help-item">Offer ID</div>
                <div class="help-item">Test Scenario</div>
                <div class="help-item">Status (Pass/Fail/Blocked/Pending)</div>
                <div class="help-item">Comments</div>
                <div class="help-item">Tester Name</div>
                <div class="help-item">Test Date and Time</div>
            </div>
            
            <div class="status-legend">
                <div class="legend-title">🎨 Status Color Guide</div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #10b981;"></div>
                    <div class="legend-text">Pass - Test Successful</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #ef4444;"></div>
                    <div class="legend-text">Fail - Issues Found</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #f59e0b;"></div>
                    <div class="legend-text">Blocked - Cannot Test</div>
                </div>
                <div class="legend-item">
                    <div class="legend-color" style="background: #7c3aed;"></div>
                    <div class="legend-text">Pending - In Progress</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        st.caption("Created By: Muhammad Ahsan")
        st.caption("Version 1.0.0")
    
    # Main content
    if page == "🏠 Home" or not st.session_state.file_uploaded:
        # Title with better visibility
        st.markdown("""
        <h1 style='color: #f1f5f9; font-size: 2.5rem; font-weight: 700; 
                   text-shadow: 2px 2px 4px rgba(0,0,0,0.3);'>
            🚀 Ready to Turn Your Test Data into Insights?
        </h1>
        """, unsafe_allow_html=True)
        st.markdown("---")
        
        if not st.session_state.file_uploaded:
            # Welcome message with fun theme
            st.markdown("""
            <div style='background: linear-gradient(135deg, #FF6B6B 0%, #4ECDC4 100%); 
                        padding: 2.5rem; border-radius: 20px; color: white; text-align: center;
                        box-shadow: 0 10px 30px rgba(0,0,0,0.2);'>
                <h1 style='color: white; font-size: 2.5rem; margin-bottom: 1rem;'>
                    🎯 Let's Find Those Bugs Together!
                </h1>
                <p style='font-size: 1.3rem; margin-bottom: 0.5rem;'>
                    Your testing team worked hard... Now let's see what they found! 🔍
                </p>
                <p style='font-size: 1.1rem; opacity: 0.95;'>
                    Drop your Excel file and watch the magic happen ✨
                </p>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Features with fun descriptions
            st.subheader("🎮 What Can This Tool Do For You?")
            
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); 
                           padding: 1.5rem; border-radius: 15px; height: 220px; color: white;
                           box-shadow: 0 5px 15px rgba(102, 126, 234, 0.4);'>
                    <h3 style='color: white; margin-bottom: 0.5rem;'>📊 Stats That Matter</h3>
                    <p style='font-size: 0.95rem;'>See who's the bug-hunting champion and which offers need some love!</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col2:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%); 
                           padding: 1.5rem; border-radius: 15px; height: 220px; color: white;
                           box-shadow: 0 5px 15px rgba(245, 87, 108, 0.4);'>
                    <h3 style='color: white; margin-bottom: 0.5rem;'>🐛 Bug Detective</h3>
                    <p style='font-size: 0.95rem;'>Track down those pesky bugs and export them before they escape!</p>
                </div>
                """, unsafe_allow_html=True)
            
            with col3:
                st.markdown("""
                <div style='background: linear-gradient(135deg, #4facfe 0%, #00f2fe 100%); 
                           padding: 1.5rem; border-radius: 15px; height: 220px; color: white;
                           box-shadow: 0 5px 15px rgba(79, 172, 254, 0.4);'>
                    <h3 style='color: white; margin-bottom: 0.5rem;'>🔄 Spot the Difference</h3>
                    <p style='font-size: 0.95rem;'>Find out when testers disagree - it's like a testing debate club!</p>
                </div>
                """, unsafe_allow_html=True)
            
            st.markdown("---")
            
            # Instructions with fun tone
            st.subheader("🎯 How to Get Started")
            st.markdown("""
            <div style='background-color: #1e293b; padding: 1.5rem; border-radius: 15px; color: white;'>
                <ol style='font-size: 1.05rem; line-height: 2;'>
                    <li><strong>📤 Upload Your File:</strong> Hit that upload button in the sidebar (it's waiting for you!)</li>
                    <li><strong>✅ File Check:</strong> Make sure your Excel has all the magic columns we need</li>
                    <li><strong>🎨 Pick Your View:</strong> Statistics, Issues, Comparisons - it's like Netflix for test data!</li>
                    <li><strong>💾 Export & Share:</strong> Download the details and impress your team</li>
                </ol>
            </div>
            """, unsafe_allow_html=True)
            
            # Pro tip
            st.markdown("---")
            st.success("💡 **Pro Tip:** Your Excel should have columns like TC #, Offer ID, Tester Name, Status, and more. We'll let you know if something's missing!")
            
            # Fun footer
            st.markdown("""
            <div style='text-align: center; margin-top: 2rem; padding: 1rem;'>
                <p style='color: #64748b; font-size: 1.1rem;'>
                    <i>Remember: Behind every bug found is a tester who deserves coffee ☕</i>
                </p>
            </div>
            """, unsafe_allow_html=True)
        else:
            # Display summary when file is loaded
            df = st.session_state.data
            st.success(f"✅ Data loaded successfully!")
            
            # Quick overview with custom HTML cards
            st.subheader("📊 Quick Overview")
            
            total_tests = len(df)
            total_offers = df['Offer ID'].nunique()
            total_testers = df['Tester Name'].nunique()
            pass_rate = (df['Status'] == 'Pass').sum() / len(df) * 100
            
            st.markdown(f"""
            <style>
            .overview-container {{
                display: flex;
                gap: 20px;
                margin: 20px 0;
            }}
            .overview-card {{
                background: linear-gradient(135deg, #1e293b 0%, #334155 100%);
                border-radius: 12px;
                padding: 25px;
                flex: 1;
                text-align: center;
                border: 1px solid #475569;
                box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
                transition: transform 0.2s;
            }}
            .overview-card:hover {{
                transform: translateY(-5px);
                box-shadow: 0 6px 12px rgba(0, 0, 0, 0.4);
            }}
            .overview-label {{
                color: #94a3b8;
                font-size: 14px;
                font-weight: 600;
                margin-bottom: 10px;
                text-transform: uppercase;
                letter-spacing: 1px;
            }}
            .overview-value {{
                color: #f1f5f9;
                font-size: 32px;
                font-weight: 700;
            }}
            .pass-rate {{
                background: linear-gradient(135deg, #065f46 0%, #047857 100%);
            }}
            </style>
            
            <div class="overview-container">
                <div class="overview-card">
                    <div class="overview-label">Total Tests</div>
                    <div class="overview-value">{total_tests:,}</div>
                </div>
                <div class="overview-card">
                    <div class="overview-label">Total Offers</div>
                    <div class="overview-value">{total_offers:,}</div>
                </div>
                <div class="overview-card">
                    <div class="overview-label">Total Testers</div>
                    <div class="overview-value">{total_testers:,}</div>
                </div>
                <div class="overview-card pass-rate">
                    <div class="overview-label">Pass Rate</div>
                    <div class="overview-value">{pass_rate:.1f}%</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown("---")
            st.info("👈 Use the sidebar navigation to explore different analytics pages")
    
    elif page == "📊 Statistics" and st.session_state.file_uploaded:
        display_statistics_page(st.session_state.data)
    
    elif page == "🐛 Issues" and st.session_state.file_uploaded:
        display_issues_page(st.session_state.data)
    
    elif page == "🔄 Comparison" and st.session_state.file_uploaded:
        display_comparison_page(st.session_state.data)
    
    elif page == "📝 Summary" and st.session_state.file_uploaded:
        display_summary_page(st.session_state.data)
    
    elif page == "👤 Tester Stats" and st.session_state.file_uploaded:
        display_tester_statistics(st.session_state.data)

if __name__ == "__main__":
    main()