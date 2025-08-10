<<<<<<< HEAD
# DataAnalyticsCBSTool
Tool to help testers perform data analytics on data collected in excel.
=======
# Test Analytics Dashboard 🔍

A comprehensive Streamlit application for analyzing software test execution data from Excel files.

## Features 🚀

### 1. **Statistics Page** 📊

- Overall test metrics and KPIs
- Pass/Fail/Blocked/Pending percentages
- Interactive pie chart for status distribution
- Bar chart showing testers by number of bugs found
- Stacked bar chart for offers with test case results
- Detailed statistics by Stream, Domain, and Date

### 2. **Issues Page** 🐛

- Filter issues by date and status
- Color-coded issue table
- Export daily issues to Excel
- Issues trend chart over time
- Real-time issue tracking

### 3. **Comparison Page** 🔄

- Identifies conflicting test results between testers
- Side-by-side comparison of different outcomes
- Filter by Offer ID or Tester
- Conflict analysis visualization
- Highlights test cases needing review

### 4. **Summary Page** 📝

- Executive summary with key metrics
- Issue analysis by offer with pattern detection
- Automated recommendations based on issue patterns
- Tester performance overview
- Test coverage analysis by Stream and Domain

### 5. **Tester Statistics Page** 👤

- Individual tester performance metrics
- Daily performance trends
- Test coverage by offer
- Recent test activities log

## Installation 🛠️

1. **Clone or download this repository**

2. **Install Python (3.8 or higher)**

3. **Install required packages:**

```bash
pip install -r requirements.txt
```

## Usage 📖

1. **Run the application:**

```bash
streamlit run app.py
```

2. **Open your browser** and navigate to `http://localhost:8501`

3. **Upload your Excel file** using the sidebar uploader

4. **Navigate through different pages** using the sidebar menu

## Excel File Requirements 📋

Your Excel file must contain the following columns:

- `TC #` - Test case number
- `Stream` - Test stream category
- `Domain` - Test domain
- `Offer ID` - Offer identifier
- `Test Scenario` - Description of the test scenario
- `Expected Result` - Expected outcome
- `Actual Result` - Actual outcome (can include comments for failed tests)
- `Status` - Test status (Pass/Fail/Blocked/Pending)
- `Tester Name` - Name of the tester
- `Test MSISDN` - Test phone number
- `Test Date and Time` - Timestamp of the test

## Features Highlights ✨

### Interactive UI

- Modern, colorful interface with gradients and animations
- Responsive design that works on different screen sizes
- Color-coded status indicators
- Expandable sections for detailed information

### Data Visualization

- Multiple chart types (pie, bar, line, stacked bar)
- Interactive Plotly charts with hover information
- Trend analysis over time
- Performance metrics visualization

### Export Capabilities

- Download filtered issues as Excel files
- Export data for specific dates
- Formatted Excel outputs with proper styling

### Smart Analysis

- Automatic pattern detection in failure comments
- Conflict detection between testers
- Performance ranking and comparisons
- Automated recommendations based on issue patterns

## Color Scheme 🎨

- **Pass**: Green (#10b981)
- **Fail**: Red (#ef4444)
- **Blocked**: Orange (#f59e0b)
- **Pending**: Purple (#6366f1)

## Tips 💡

1. **For best results**, ensure your Excel file has clean data with consistent formatting
2. **Date columns** should be in a standard format (YYYY-MM-DD or datetime)
3. **Use filters** on the Issues and Comparison pages to focus on specific problems
4. **Export functionality** allows you to share specific issue reports with team members
5. **The Summary page** provides high-level insights for management reporting

## Troubleshooting 🔧

**File won't upload:**

- Check that your file is in .xlsx or .xls format
- Ensure all required columns are present
- Verify the file isn't corrupted

**Charts not displaying:**

- Refresh the page
- Check that your data contains valid values
- Ensure dates are properly formatted

**Performance issues:**

- For large files (>10,000 rows), initial loading may take time
- Consider filtering data before uploading
- Close other browser tabs to free up memory

## Support 📧

For issues or questions, please ensure your Excel file matches the required format and contains all necessary columns.

## Version

Current Version: 1.0.0

---

Made with ❤️ using Streamlit
>>>>>>> b3a65a3 (second commit)
