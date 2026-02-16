import streamlit as st
import pandas as pd
import os
from scanner import Scanner
from parser import Parser
from categorizer import Categorizer

# Page configuration
st.set_page_config(page_title="Expense App Desktop", layout="wide", page_icon="💰")

# Initialize services
scanner = Scanner()
parser = Parser()
categorizer = Categorizer()

# UI Styling
st.markdown("""
    <style>
    .main {
        background-color: #f8f9fa;
    }
    .stButton>button {
        width: 100%;
        border-radius: 5px;
        height: 3em;
        background-color: #007bff;
        color: white;
    }
    .stTable {
        background-color: white;
        border-radius: 10px;
        padding: 10px;
    }
    </style>
    """, unsafe_allow_html=True)

st.title("💰 Expense App Desktop")
st.write(f"Scanning directory: `{scanner.watch_path}`")

# Sidebar for controls
with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Scan for new PDFs"):
        st.rerun()
    
    if st.button("🛑 Shutdown App"):
        st.warning("Shutting down the server. Attempting to close tab...")
        st.markdown("""
            <script>
                setTimeout(function() {
                    window.close();
                }, 1000);
            </script>
            """, unsafe_allow_html=True)
        # Use a slight delay to allow the JS to initiate
        import time
        time.sleep(1.5)
        os._exit(0)

# Main content
tab1, tab2, tab3 = st.tabs(["📊 Transactions", "⚙️ Category Editor", "📈 Statistics"])

with tab1:
    uploaded_files = st.file_uploader("Upload bank statements (PDF)", type="pdf", accept_multiple_files=True)
    
    pdfs = scanner.scan_for_pdfs()
    all_transactions = []
    
    # Process scanned PDFs
    for pdf in pdfs:
        transactions = parser.parse_bank_statement(pdf)
        for tx in transactions:
            tx['file'] = os.path.basename(pdf)
            tx['source'] = 'Scanned'
            tx['category'] = categorizer.suggest_category(tx['description'])
            all_transactions.append(tx)
            
    # Process uploaded PDFs
    if uploaded_files:
        for uploaded_file in uploaded_files:
            transactions = parser.parse_bank_statement(uploaded_file)
            for tx in transactions:
                tx['file'] = uploaded_file.name
                tx['source'] = 'Uploaded'
                tx['category'] = categorizer.suggest_category(tx['description'])
                all_transactions.append(tx)

    if not all_transactions:
        st.info("No bank statements found. Scan the folder or upload a PDF manually.")
    else:
        df = pd.DataFrame(all_transactions)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", len(df))
        col2.metric("Total Spent", f"{df[df['amount'] < 0]['amount'].sum():.2f} €")
        col3.metric("Categorized", df[df['category'] != 'Sonstiges'].shape[0])

        st.divider()

        # Transaction Table with Category Assignment
        st.subheader("Recent Transactions")
        
        for i, row in df.iterrows():
            with st.expander(f"{row['date']} - {row['description'][:50]}... ({row['amount']:.2f} €)"):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.write(f"**Full Description:** {row['description']}")
                    st.write(f"**Source:** {row['source']} ({row['file']})")
                
                with col_right:
                    current_cat = row['category']
                    categories = ["Sonstiges", "Supermarkt", "Amazon", "Versicherung", "Computerspiele", "Trading", "Haus", "Custom..."]
                    index = categories.index(current_cat) if current_cat in categories else 0
                    
                    new_cat = st.selectbox(
                        "Category",
                        options=categories,
                        index=index,
                        key=f"cat_{row['id']}_{i}"
                    )
                    
                    if new_cat == "Custom...":
                        custom_cat = st.text_input("Enter custom category", key=f"custom_{row['id']}_{i}")
                        if st.button("Apply Custom", key=f"btn_custom_{row['id']}_{i}"):
                            keyword = categorizer.extract_keyword(row['description'])
                            categorizer.add_mapping(keyword, custom_cat)
                            st.success(f"Added mapping: {keyword} -> {custom_cat}")
                            st.rerun()
                    elif new_cat != current_cat:
                        keyword = categorizer.extract_keyword(row['description'])
                        categorizer.add_mapping(keyword, new_cat)
                        st.success(f"Updated category for '{keyword}' to {new_cat}")
                        st.rerun()

with tab2:
    st.header("⚙️ Category Management")
    
    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Learned Mappings")
        st.write("These are keyword-to-category mappings learned from your manual assignments.")
        
        if not categorizer.mappings:
            st.info("No learned mappings yet. Assign categories in the Transactions tab to see them here.")
        else:
            for keyword, category in list(categorizer.mappings.items()):
                col1, col2, col3 = st.columns([2, 2, 1])
                col1.write(f"`{keyword}`")
                col2.write(f"**{category}**")
                if col3.button("🗑️", key=f"del_map_{keyword}"):
                    categorizer.delete_mapping(keyword)
                    st.success(f"Deleted mapping for {keyword}")
                    st.rerun()

    with col_b:
        st.subheader("Global Rules")
        st.write("These are the default rules used for initial categorization.")
        
        for i, rule in enumerate(categorizer.rules):
            with st.expander(f"Category: {rule['category']}"):
                current_keywords = ", ".join(rule['keywords'])
                new_keywords_str = st.text_input("Keywords (comma separated)", value=current_keywords, key=f"edit_rule_kw_{i}")
                
                col1, col2 = st.columns(2)
                if col1.button("💾 Save Keywords", key=f"save_rule_kw_{i}"):
                    new_keywords = [k.strip().lower() for k in new_keywords_str.split(",") if k.strip()]
                    categorizer.update_rule_keywords(rule['category'], new_keywords)
                    st.success(f"Updated keywords for {rule['category']}")
                    st.rerun()
                
                if col2.button("🗑️ Delete Rule", key=f"del_rule_{rule['category']}"):
                    categorizer.delete_rule(rule['category'])
                    st.success(f"Deleted rule for {rule['category']}")
                    st.rerun()
        
        st.divider()
        st.subheader("Add New Rule")
        with st.form("new_rule_form"):
            new_rule_cat = st.text_input("Category Name")
            new_rule_keywords = st.text_input("Keywords (comma separated)")
            if st.form_submit_button("Add Global Rule"):
                if new_rule_cat and new_rule_keywords:
                    keywords = [k.strip().lower() for k in new_rule_keywords.split(",")]
                    categorizer.add_rule(keywords, new_rule_cat)
                    st.success(f"Added rule for {new_rule_cat}")
                    st.rerun()
                else:
                    st.error("Please provide both category and keywords.")

with tab3:
    st.header("📈 Expense Statistics")
    
    if all_transactions:
        df_stats = pd.DataFrame(all_transactions)
        # Convert date to datetime. Handle German format DD.MM.YYYY
        df_stats['date'] = pd.to_datetime(df_stats['date'], format='%d.%m.%Y', dayfirst=True)
        
        # We only care about expenses (negative amounts)
        expenses_df = df_stats[df_stats['amount'] < 0].copy()
        expenses_df['amount'] = expenses_df['amount'].abs() # Work with positive numbers for easier reading
        
        expenses_df['Year'] = expenses_df['date'].dt.year
        expenses_df['Month'] = expenses_df['date'].dt.strftime('%Y-%m')
        
        # Yearly Summary
        st.subheader("📅 Yearly Summary")
        yearly_summary = expenses_df.groupby(['Year', 'category'])['amount'].sum().reset_index()
        yearly_pivot = yearly_summary.pivot(index='Year', columns='category', values='amount').fillna(0)
        st.dataframe(yearly_pivot.style.format("{:.2f} €"), use_container_width=True)
        
        # Yearly Chart
        st.bar_chart(yearly_pivot)
        
        st.download_button(
            label="📥 Download Yearly Summary CSV",
            data=yearly_pivot.to_csv().encode('utf-8'),
            file_name=f"yearly_summary.csv",
            mime="text/csv",
        )
        
        st.divider()
        
        # Monthly Summary
        st.subheader("📆 Monthly Summary")
        available_months = sorted(expenses_df['Month'].unique(), reverse=True)
        selected_month = st.selectbox("Select Month", options=available_months)
        
        if selected_month:
            month_df = expenses_df[expenses_df['Month'] == selected_month]
            monthly_summary = month_df.groupby('category')['amount'].sum().reset_index()
            
            col_chart, col_table = st.columns([2, 1])
            
            with col_chart:
                st.bar_chart(monthly_summary.set_index('category'))
            
            with col_table:
                st.table(monthly_summary.style.format({"amount": "{:.2f} €"}))
                st.metric("Total Monthly Expense", f"{monthly_summary['amount'].sum():.2f} €")
                
                st.download_button(
                    label="📥 Download Monthly CSV",
                    data=monthly_summary.to_csv(index=False).encode('utf-8'),
                    file_name=f"summary_{selected_month}.csv",
                    mime="text/csv",
                )
    else:
        st.info("No transaction data available to generate statistics.")

# Startup section (informational)
st.divider()
st.caption("To set this app to open on Ubuntu startup, check the documentation provided in the setup guide.")
