import streamlit as st
import pandas as pd
import os
import plotly.express as px
import hashlib
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

st.write(f"Scanning directory: `{scanner.watch_path}`")
st.caption("Place your bank statements as **CSV files** in this folder.")

# Sidebar for controls
with st.sidebar:
    st.header("Actions")
    if st.button("🔄 Scan for new CSVs"):
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
    uploaded_files = st.file_uploader("Upload bank statements (CSV)", type="csv", accept_multiple_files=True)
    
# Cached parsing of bank statements
@st.cache_data
def get_raw_transactions(scanned_files_hash):
    """
    Reads and parses all bank statements. 
    Invalidates only if files are added or changed.
    """
    scanned_csvs = scanner.scan_for_csvs()
    raw_tx = []
    for csv_file in scanned_csvs:
        transactions = parser.parse_bank_statement(csv_file)
        for tx in transactions:
            tx['file'] = os.path.basename(csv_file)
            tx['source'] = 'Scanned'
            raw_tx.append(tx)
    return raw_tx

# Cached categorization
@st.cache_data
def get_categorized_transactions(raw_transactions, rules_mtime):
    """
    Applies categorization rules to raw transactions.
    Invalidates if rules change or raw data changes.
    """
    import copy
    categorized_tx = copy.deepcopy(raw_transactions)
    for tx in categorized_tx:
        tx['category'] = categorizer.suggest_category(tx['description'])
    return categorized_tx

# Get cache invalidation keys
scanned_csvs = scanner.scan_for_csvs()
files_hash = hashlib.md5("".join(sorted(scanned_csvs)).encode()).hexdigest()
rules_mtime = os.path.getmtime(categorizer.rules_path) if os.path.exists(categorizer.rules_path) else 0

# Process Data
raw_tx = get_raw_transactions(files_hash)
all_transactions = get_categorized_transactions(raw_tx, rules_mtime)

# Process uploaded CSVs (Keep these separate for now as uploader state is session-dependent)
if uploaded_files:
    for uploaded_file in uploaded_files:
        transactions = parser.parse_bank_statement(uploaded_file)
        for tx in transactions:
            tx['file'] = uploaded_file.name
            tx['source'] = 'Uploaded'
            tx['category'] = categorizer.suggest_category(tx['description'])
            all_transactions.append(tx)

    if not all_transactions:
        st.info("No bank statements found. Scan the folder or upload a CSV manually.")
    else:
        df = pd.DataFrame(all_transactions)
        
        # Display summary
        col1, col2, col3 = st.columns(3)
        col1.metric("Total Transactions", len(df))
        with col2:
            total_spent = abs(df[df['amount'] < 0]['amount'].sum())
            st.markdown(f"""
                <div style='display: flex; flex-direction: column;'>
                    <div style='font-size: 0.8rem; color: rgba(250, 250, 250, 0.6);'>Total Spent</div>
                    <div style='font-size: 1.8rem; font-weight: 600; color: #ff4b4b; padding-top: 5px;'>{total_spent:.2f} €</div>
                </div>
            """, unsafe_allow_html=True)
        col3.metric("Categorized", df[df['category'] != 'Sonstiges'].shape[0])

        st.divider()

        # --- Filtering Logic ---
        st.subheader("Filter transactions")
        available_categories = ["All"] + categorizer.get_all_categories()
        selected_category = st.selectbox("Filter by Category", options=available_categories, index=0)
        
        if selected_category != "All":
            df = df[df['category'] == selected_category]

        # Sort by date for better display
        df['date'] = pd.to_datetime(df['date'], dayfirst=True, format='mixed')
        df = df.sort_values(by='date', ascending=False)
        
        # --- Pagination Logic ---
        items_per_page = 50
        total_pages = (len(df) - 1) // items_per_page + 1
        
        if total_pages > 1:
            page = st.number_input("Page", min_value=1, max_value=total_pages, step=1, value=1)
        else:
            page = 1
            
        start_idx = (page - 1) * items_per_page
        end_idx = min(start_idx + items_per_page, len(df))
        
        st.write(f"Showing transactions {start_idx + 1} to {end_idx} of {len(df)}")
        
        display_df = df.iloc[start_idx:end_idx]
        
        # Get sorted categories
        all_cats = categorizer.get_all_categories()
        if "Sonstiges" in all_cats:
            all_cats.remove("Sonstiges")
        categories = sorted(all_cats) + ["Sonstiges", "Custom..."]

        for i, row in display_df.iterrows():
            with st.expander(f"{row['date'].strftime('%Y-%m-%d')} - {row['description'][:50]}... ({row['amount']:.2f} €)", expanded=True):
                col_left, col_right = st.columns([2, 1])
                
                with col_left:
                    st.write(f"**Full Description:** {row['description']}")
                    st.write(f"**Source:** {row['source']} ({row['file']})")
                
                with col_right:
                    current_cat = row['category']
                    index = categories.index(current_cat) if current_cat in categories else categories.index("Sonstiges")
                    
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
    
    # Emergency Restore Button
    if st.button("⏪ Restore Latest Backup", help="Fixes rule corruption by undoing the last change."):
        success, message = categorizer.restore_latest_backup()
        if success:
            st.success(message)
            st.rerun()
        else:
            st.error(message)

    col_a, col_b = st.columns(2)
    
    with col_a:
        st.subheader("Learned Mappings")
        st.write("These are keyword-to-category mappings learned from your manual assignments.")
        
        if not categorizer.mappings:
            st.info("No learned mappings yet. Assign categories in the Transactions tab to see them here.")
        else:
            # Sort mappings alphabetically by keyword
            sorted_mappings = dict(sorted(categorizer.mappings.items()))
            for keyword, category in sorted_mappings.items():
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
        
        # Sort rules alphabetically by category
        sorted_rules = sorted(categorizer.rules, key=lambda x: x['category'])
        for i, rule in enumerate(sorted_rules):
            cat_key = rule['category']
            with st.expander(f"Category: {cat_key}"):
                current_keywords = ", ".join(rule['keywords'])
                new_keywords_str = st.text_input("Keywords (comma separated)", value=current_keywords, key=f"edit_rule_kw_{cat_key}")
                
                col1, col2 = st.columns(2)
                if col1.button("💾 Save Keywords", key=f"save_rule_kw_{cat_key}"):
                    new_keywords = [k.strip().lower() for k in new_keywords_str.split(",") if k.strip()]
                    categorizer.update_rule_keywords(cat_key, new_keywords)
                    st.success(f"Updated keywords for {cat_key}")
                    st.rerun()
                
                if col2.button("🗑️ Delete Rule", key=f"del_rule_{cat_key}"):
                    categorizer.delete_rule(cat_key)
                    st.success(f"Deleted rule for {cat_key}")
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
        
        st.divider()
        st.subheader("🏷️ Rename Category")
        all_existing_cats = categorizer.get_all_categories()
        cat_to_rename = st.selectbox("Select Category to Rename", options=all_existing_cats)
        new_cat_name = st.text_input("New Name", key="rename_input")
        
        if st.button("Apply Rename"):
            if new_cat_name:
                if categorizer.rename_category(cat_to_rename, new_cat_name):
                    st.success(f"Renamed '{cat_to_rename}' to '{new_cat_name}'")
                    st.rerun()
                else:
                    st.error("Rename failed. Ensure names are different.")
            else:
                st.warning("Please enter a new name.")

with tab3:
    st.header("📈 Expense Statistics")
    
    if all_transactions:
        df_stats = pd.DataFrame(all_transactions)
        df_stats['date'] = pd.to_datetime(df_stats['date'], dayfirst=True, format='mixed')
        
        # --- Interactive Category Filter ---
        st.subheader("🔍 Filter Categories")
        available_stats_cats = sorted(df_stats['category'].unique())
        
        # Session state to manage multiselect
        if 'stats_filter' not in st.session_state:
            st.session_state.stats_filter = available_stats_cats
            
        col_f1, col_f2 = st.columns([3, 1])
        with col_f1:
            selected_stats_cats = st.multiselect(
                "Select categories to include in charts",
                options=available_stats_cats,
                key='stats_filter'
            )
        with col_f2:
            st.write(" ") # Visual alignment
            if st.button("✅ Select All"):
                st.session_state.stats_filter = available_stats_cats
                st.rerun()
        
        # Filter the data
        df_stats = df_stats[df_stats['category'].isin(selected_stats_cats)]
        
        if df_stats.empty:
            st.warning("No categories selected. Please select at least one category to reflect in charts.")
        else:
            # We only care about expenses (negative amounts)
            expenses_df = df_stats[df_stats['amount'] < 0].copy()
            expenses_df['amount'] = expenses_df['amount'].abs() # Work with positive numbers for easier reading
            
            expenses_df['Year'] = expenses_df['date'].dt.year
            expenses_df['Month'] = expenses_df['date'].dt.strftime('%Y-%m')
            
            # Yearly Summary
            st.subheader("📅 Yearly Summary")
            yearly_summary = expenses_df.groupby(['Year', 'category'])['amount'].sum().reset_index()
            # Yearly Pivot for comparison
            yearly_pivot = yearly_summary.pivot(index='category', columns='Year', values='amount').fillna(0).reset_index()

            # --- Average Monthly Expense Calculation ---
            num_months = expenses_df['Month'].nunique()
            total_by_category = expenses_df.groupby('category')['amount'].sum().reset_index()
            
            if num_months > 0:
                avg_monthly_expenses = total_by_category.copy()
                avg_monthly_expenses['average_per_month'] = avg_monthly_expenses['amount'] / num_months
                avg_monthly_expenses = avg_monthly_expenses.sort_values(by='average_per_month', ascending=False)
                
                st.subheader("📊 Average Monthly Expense per Category")
                st.caption(f"Calculated over {num_months} unique months in the selected period.")
                
                # Display as a clean dataframe
                display_avg_df = avg_monthly_expenses[['category', 'average_per_month']].copy()
                display_avg_df.columns = ['Category', 'Avg. Monthly Expense (€)']
                st.dataframe(
                    display_avg_df.style.format({'Avg. Monthly Expense (€)': "{:.2f}"}),
                    use_container_width=True,
                    hide_index=True
                )
            else:
                st.info("Insufficient data to calculate monthly averages (no expense months found).")
            
            # Yearly Pie Chart (Category distribution across all years)
            st.subheader("🥧 Overall Category Distribution")
            if not total_by_category.empty:
                fig_yearly = px.pie(total_by_category, values='amount', names='category', 
                                     title='Expenses by Category (All Time - Selected Filter)',
                                     hole=0.4,
                                     color_discrete_sequence=px.colors.qualitative.Pastel)
                fig_yearly.update_traces(textinfo='percent+label')
                st.plotly_chart(fig_yearly, width='stretch')
            else:
                st.info("No expense data to display in pie chart.")
            
            # Prepare Excel Export (Multi-sheet)
            import io
            excel_data = io.BytesIO()
            with pd.ExcelWriter(excel_data, engine='openpyxl') as writer:
                # Monthly sheets
                for month in sorted(expenses_df['Month'].unique()):
                    month_df = expenses_df[expenses_df['Month'] == month]
                    month_summary = month_df.groupby('category')['amount'].sum().reset_index()
                    # Sort by amount descending
                    month_summary = month_summary.sort_values('amount', ascending=False)
                    # Add Total row
                    total_row = pd.DataFrame([{'category': 'TOTAL', 'amount': month_summary['amount'].sum()}])
                    month_summary = pd.concat([month_summary, total_row], ignore_index=True)
                    month_summary.to_excel(writer, sheet_name=month, index=False)
                
                # Monthly Totals Sheet
                monthly_totals = expenses_df.groupby('Month')['amount'].sum().reset_index()
                # Sort by amount descending
                monthly_totals = monthly_totals.sort_values('amount', ascending=False)
                # Add Grand Total
                grand_monthly_total = pd.DataFrame([{'Month': 'GRAND TOTAL', 'amount': monthly_totals['amount'].sum()}])
                monthly_totals_final = pd.concat([monthly_totals, grand_monthly_total], ignore_index=True)
                monthly_totals_final.to_excel(writer, sheet_name="Monthly Totals", index=False)
                
                # Average Monthly Expenses Sheet
                avg_export_df = avg_monthly_expenses[['category', 'average_per_month']].copy()
                # Sort by amount descending
                avg_export_df = avg_export_df.sort_values('average_per_month', ascending=False)
                avg_export_df.to_excel(writer, sheet_name="Average Monthly Expenses", index=False)

                # Yearly Comparison (Pivot) Sheet
                # Note: Pivot sheets are complex to sort by "amount" across multiple years, 
                # but we'll sort categories by their total sum across all years for consistency.
                pivot_sums = yearly_pivot.select_dtypes(include=['number']).sum(axis=1)
                yearly_pivot['Total_Sum'] = pivot_sums
                yearly_pivot_sorted = yearly_pivot.sort_values('Total_Sum', ascending=False).drop(columns=['Total_Sum'])
                
                # Add Total row for each year column
                pivot_totals = yearly_pivot_sorted.select_dtypes(include=['number']).sum()
                total_pivot_row = pd.DataFrame(pivot_totals).T
                total_pivot_row['category'] = 'TOTAL'
                yearly_pivot_final = pd.concat([yearly_pivot_sorted, total_pivot_row], ignore_index=True)
                yearly_pivot_final.to_excel(writer, sheet_name="Yearly Comparison", index=False)
                
                # Yearly Summary Sheet (Grouped by Year, Sort by amount descending within year)
                yearly_summary_sorted = yearly_summary.sort_values(['Year', 'amount'], ascending=[False, False])
                # Add overall Total row
                grand_total_row = pd.DataFrame([{'Year': 'GRAND TOTAL', 'category': '-', 'amount': yearly_summary_sorted['amount'].sum()}])
                yearly_summary_final = pd.concat([yearly_summary_sorted, grand_total_row], ignore_index=True)
                yearly_summary_final.to_excel(writer, sheet_name="Yearly Summary", index=False)

            st.download_button(
                label="📥 Download Yearly Report (Excel)",
                data=excel_data.getvalue(),
                file_name=f"expense_report_filtered.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        
        st.divider()
        
        # Monthly Summary
        st.subheader("📆 Monthly Summary")
        available_months = sorted(expenses_df['Month'].unique(), reverse=True)
        selected_month = st.selectbox("Select Month", options=available_months)
        
        if selected_month:
            month_df = expenses_df[expenses_df['Month'] == selected_month]
            monthly_summary = month_df.groupby('category')['amount'].sum().reset_index()
            
            # Monthly Pie Chart
            fig_monthly = px.pie(monthly_summary, values='amount', names='category',
                                  title=f'Expense Distribution for {selected_month}',
                                  hole=0.4,
                                  color_discrete_sequence=px.colors.qualitative.Safe)
            fig_monthly.update_traces(textinfo='percent+label')
            st.plotly_chart(fig_monthly, width='stretch')
            
            st.divider()
            
            # Key Metrics below the chart
            mcol1, mcol2 = st.columns(2)
            with mcol1:
                monthly_total = abs(monthly_summary['amount'].sum())
                st.markdown(f"""
                    <div style='display: flex; flex-direction: column;'>
                        <div style='font-size: 0.8rem; color: rgba(250, 250, 250, 0.6);'>Total Monthly Expense</div>
                        <div style='font-size: 1.8rem; font-weight: 600; color: #ff4b4b; padding-top: 5px;'>{monthly_total:.2f} €</div>
                    </div>
                """, unsafe_allow_html=True)
            with mcol2:
                st.download_button(
                    label="📥 Download Monthly CSV",
                    data=monthly_summary.to_csv(index=False).encode('utf-8'),
                    file_name=f"summary_{selected_month}.csv",
                    mime="text/csv",
                    key=f"dl_{selected_month}"
                )
    else:
        st.info("No transaction data available to generate statistics.")

# Startup section (informational)
st.divider()
st.caption("To set this app to open on Ubuntu startup, check the documentation provided in the setup guide.")
