# 💰 Expense App Desktop

A powerful and user-friendly desktop application for managing your personal finances. Automatically scan bank statements, categorize transactions, and gain insights into your spending habits.

## ✨ Features

- **📂 Automated Scanning**: Watches a specific directory for new CSV bank statements.
- **📄 CSV Parsing**: Extracts transaction data (Date, Description, Amount) from CSV files.
- **🏷️ Smart Categorization**: Uses global rules and learned mappings to automatically categorize expenses.
- **🖊️ Manual Overrides**: Easily correct categories and add new mappings directly from the UI.
- **📊 Interactive Dashboard**:
    - **Transactions**: View and manage recent transactions.
    - **Category Editor**: Manage auto-categorization rules and learned mappings.
    - **Statistics**: Visualize monthly and yearly spending with interactive charts.
- **🐧 Ubuntu Integration**: Includes setup guides for automatic startup on Ubuntu.

## 🛠️ Tech Stack

- **Python 3.x**
- **Streamlit**: For the interactive web interface.
- **Pandas**: For data manipulation and CSV parsing.
- **watchdog**: For real-time directory monitoring.

## 🚀 Getting Started

### Prerequisites

Ensure you have Python 3.x installed. You can check your version with:
```bash
python3 --version
```

### Installation

1. **Clone the repository** (if applicable) or navigate to the project folder.
2. **Create a virtual environment**:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

### Usage

1. **Start the application**:
   ```bash
   streamlit run app.py
   ```
2. **Scan for CSVs**: Place your bank statement CSVs in the monitored directory (defaulting to the project root or as specified in `scanner.py`).
3. **Upload Manually**: Use the file uploader in the "Transactions" tab to process CSVs directly.
4. **Categorize**: Review transaction categories and use the dropdowns to train the app for better accuracy.

## 📁 Project Structure

- `app.py`: Main Streamlit application and UI logic.
- `scanner.py`: Logic for watching and scanning directories for new CSV files.
- `parser.py`: Extracts transaction data from CSV files.
- `categorizer.py`: Manages rules and logic for transaction categorization.
- `rules.json`: Stores global categorization rules and learned mappings.
- `STARTUP_SETUP.md`: Detailed guide for Ubuntu startup integration.

## 🔧 Ubuntu Startup Setup

To have the app open automatically when you log in to Ubuntu, refer to the [Ubuntu Startup Setup Guide](file:///home/ren/Documents/antigravity_projects/expense_app_desktop/STARTUP_SETUP.md).

---
*Created by Antigravity for a seamless expense tracking experience.*
