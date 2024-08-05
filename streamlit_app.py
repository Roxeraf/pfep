import streamlit as st
import pandas as pd
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
import sqlite3

# Initialize database
def init_db():
    conn = sqlite3.connect('pfep_data.db')
    c = conn.cursor()
    c.execute('''CREATE TABLE IF NOT EXISTS pfep
                 (Part_Number TEXT PRIMARY KEY, 
                  Description TEXT, 
                  Supplier TEXT, 
                  Packaging TEXT, 
                  Storage_Location TEXT, 
                  Usage_Rate REAL, 
                  Min_Inventory REAL, 
                  Max_Inventory REAL, 
                  Lead_Time REAL, 
                  Last_Updated TEXT,
                  Order_Frequency TEXT, 
                  Min_Inventory_Level REAL, 
                  Max_Inventory_Level REAL, 
                  Avg_Lead_Time REAL, 
                  Unit_of_Measure TEXT, 
                  Packaging_Dimensions TEXT,
                  Reusable_Packaging INTEGER, 
                  Reusable_Packaging_Lead_Time REAL,
                  Total_Usage_Time REAL,
                  Order_Frequency_Days REAL,
                  Average_Daily_Usage REAL,
                  Current_Inventory REAL,
                  Remaining_Usage_Time REAL)''')
    conn.commit()
    conn.close()

# Function to load data from database
def load_data():
    conn = sqlite3.connect('pfep_data.db')
    df = pd.read_sql('SELECT * FROM pfep', conn)
    conn.close()
    return df

# Function to upload and process data
def upload_data():
    uploaded_file = st.file_uploader("Choose a file", type=['xlsx', 'csv'])
    if uploaded_file is not None:
        try:
            if uploaded_file.name.endswith('.xlsx'):
                df = pd.read_excel(uploaded_file)
            else:
                df = pd.read_csv(uploaded_file)
            
            df['Last Updated'] = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
            
            conn = sqlite3.connect('pfep_data.db')
            df.to_sql('pfep', conn, if_exists='replace', index=False)
            conn.close()
            
            st.session_state.pfep_data = df
            st.success("Data uploaded successfully and stored in the database!")
        except Exception as e:
            st.error(f"An error occurred: {e}")

# Function to display data
def display_data():
    st.subheader("PFEP Data")
    
    filter_column = st.selectbox("Filter by column", st.session_state.pfep_data.columns)
    filter_value = st.text_input("Filter value")
    
    filtered_data = st.session_state.pfep_data
    if filter_value:
        filtered_data = filtered_data[filtered_data[filter_column].astype(str).str.contains(filter_value, case=False)]
    
    st.dataframe(filtered_data)

# Function for analytics and reporting
def analytics_and_reporting():
    st.subheader("Advanced Analytics and Reporting")

    if st.session_state.pfep_data.empty:
        st.warning("No data available for analysis. Please upload data first.")
        return

    # Filtering options
    with st.expander("Data Filters"):
        col1, col2 = st.columns(2)
        with col1:
            selected_suppliers = st.multiselect(
                "Select Suppliers", options=st.session_state.pfep_data['Supplier'].unique()
            )
        with col2:
            selected_parts = st.multiselect(
                "Select Parts", options=st.session_state.pfep_data['Part Number'].unique()
            )

    # Apply filters
    filtered_data = st.session_state.pfep_data
    if selected_suppliers:
        filtered_data = filtered_data[filtered_data['Supplier'].isin(selected_suppliers)]
    if selected_parts:
        filtered_data = filtered_data[filtered_data['Part Number'].isin(selected_parts)]

    # Dashboard Summary
    st.write("### Dashboard Summary")
    col1, col2, col3, col4 = st.columns(4)
    with col1:
        st.metric("Total Parts", len(filtered_data))
    with col2:
        st.metric("Total Suppliers", filtered_data['Supplier'].nunique())
    with col3:
        st.metric("Average Lead Time", f"{filtered_data['Avg Lead Time (days)'].mean():.2f} days")
    with col4:
        st.metric("Total Current Inventory", f"{filtered_data['Current Inventory'].sum():,.0f}")

    # Tabs for different analyses
    tab1, tab2, tab3, tab4 = st.tabs(["Inventory Analysis", "Supplier Performance", "Usage Trends", "Lead Time Analysis"])

    with tab1:
        st.write("### Inventory Analysis")
        fig_inventory = px.bar(filtered_data, 
                               x='Part Number', 
                               y=['Current Inventory', 'Min Inventory', 'Max Inventory'],
                               title="Current Inventory vs Min/Max Levels by Part",
                               labels={'value': 'Quantity', 'variable': 'Metric'})
        fig_inventory.update_layout(xaxis_title="Part Number", yaxis_title="Quantity")
        st.plotly_chart(fig_inventory, use_container_width=True)

        # Inventory Optimization Suggestions
        st.write("### Inventory Optimization Suggestions")
        low_inventory = filtered_data[filtered_data['Current Inventory'] < filtered_data['Min Inventory']]
        if not low_inventory.empty:
            st.warning("The following parts have inventory levels below the minimum:")
            st.dataframe(low_inventory[['Part Number', 'Current Inventory', 'Min Inventory', 'Remaining Usage Time (Days)']])
        else:
            st.success("All parts have sufficient inventory levels.")

    with tab2:
        st.write("### Supplier Performance and Rating")
        supplier_metrics = filtered_data.groupby('Supplier').agg({
            'Avg Lead Time (days)': 'mean',
            'Part Number': 'count',
            'Usage Rate': 'sum',
            'Remaining Usage Time (Days)': 'mean'
        }).reset_index()
        supplier_metrics.columns = ['Supplier', 'Avg Lead Time', 'Number of Parts', 'Total Usage Rate', 'Avg Remaining Usage Time']
        
        # Calculate a simple supplier rating (higher is better)
        supplier_metrics['Rating'] = (
            (1 / supplier_metrics['Avg Lead Time']) * 0.4 +
            supplier_metrics['Number of Parts'] * 0.3 +
            supplier_metrics['Avg Remaining Usage Time'] * 0.3
        )
        supplier_metrics['Rating'] = supplier_metrics['Rating'] / supplier_metrics['Rating'].max() * 100  # Normalize to 0-100
        
        # Display supplier metrics
        st.dataframe(supplier_metrics.sort_values('Rating', ascending=False))

        # Supplier performance visualization
        fig_supplier = px.scatter(supplier_metrics, x='Avg Lead Time', y='Number of Parts', 
                                  size='Total Usage Rate', color='Rating', hover_name='Supplier',
                                  title='Supplier Performance Overview')
        st.plotly_chart(fig_supplier, use_container_width=True)

    with tab3:
        st.write("### Usage Rate Trends")
        selected_part = st.selectbox("Select a part for usage analysis", filtered_data['Part Number'].unique())
        part_data = filtered_data[filtered_data['Part Number'] == selected_part]
        
        if not part_data.empty:
            fig_usage = go.Figure()
            fig_usage.add_trace(go.Bar(x=['Current Usage Rate'], y=[part_data['Usage Rate'].values[0]], name='Current Usage Rate'))
            fig_usage.add_trace(go.Bar(x=['Average Daily Usage'], y=[part_data['Average Daily Usage'].values[0]], name='Average Daily Usage'))
            fig_usage.update_layout(title=f"Usage Rate Analysis for Part {selected_part}",
                                    xaxis_title="Metric", yaxis_title="Usage")
            st.plotly_chart(fig_usage, use_container_width=True)

            col1, col2, col3 = st.columns(3)
            col1.metric("Current Inventory", f"{part_data['Current Inventory'].values[0]:,.0f}")
            col2.metric("Remaining Usage Time", f"{part_data['Remaining Usage Time (Days)'].values[0]:.2f} days")
            col3.metric("Order Frequency", f"{part_data['Order Frequency (days)'].values[0]} days")

    with tab4:
        st.write("### Lead Time Analysis")
        fig_lead_time = px.box(filtered_data, x='Supplier', y='Avg Lead Time (days)', 
                               title="Lead Time Distribution by Supplier")
        fig_lead_time.update_layout(xaxis_title="Supplier", yaxis_title="Lead Time (days)")
        st.plotly_chart(fig_lead_time, use_container_width=True)

        # Additional lead time insights
        avg_lead_time = filtered_data['Avg Lead Time (days)'].mean()
        max_lead_time = filtered_data['Avg Lead Time (days)'].max()
        min_lead_time = filtered_data['Avg Lead Time (days)'].min()

        col1, col2, col3 = st.columns(3)
        col1.metric("Average Lead Time", f"{avg_lead_time:.2f} days")
        col2.metric("Max Lead Time", f"{max_lead_time:.2f} days")
        col3.metric("Min Lead Time", f"{min_lead_time:.2f} days")

# Function to download data
def download_data():
    output = io.BytesIO()
    with pd.ExcelWriter(output, engine='xlsxwriter') as writer:
        st.session_state.pfep_data.to_excel(writer, index=False, sheet_name='PFEP')
    excel_data = output.getvalue()
    st.download_button(
        label="Download PFEP data as Excel",
        data=excel_data,
        file_name="pfep_data.xlsx",
        mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
    )

def main():
    st.title("Advanced PFEP Management System")

    init_db()  # Initialize the database

    if 'pfep_data' not in st.session_state:
        st.session_state.pfep_data = load_data()

    menu = ["Upload Data", "View Data", "Analytics and Reporting", "Download Data"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Upload Data":
        upload_data()
    elif choice == "View Data":
        display_data()
    elif choice == "Analytics and Reporting":
        analytics_and_reporting()
    elif choice == "Download Data":
        download_data()

if __name__ == "__main__":
    main()