import streamlit as st
import pandas as pd
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go

# Initialize session state to store our data
if 'pfep_data' not in st.session_state:
    st.session_state.pfep_data = pd.DataFrame(columns=[
        'Part Number', 'Description', 'Supplier', 'Packaging', 'Storage Location', 
        'Usage Rate', 'Min Inventory', 'Max Inventory', 'Lead Time', 'Last Updated'
    ])

def upload_excel():
    uploaded_file = st.file_uploader("Choose an Excel file", type="xlsx")
    if uploaded_file is not None:
        df = pd.read_excel(uploaded_file)
        df['Last Updated'] = datetime.now()
        st.session_state.pfep_data = pd.concat([st.session_state.pfep_data, df], ignore_index=True)
        st.success("Data uploaded successfully!")

def download_excel():
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

def display_data():
    st.subheader("PFEP Data")
    
    # Filter data
    filter_column = st.selectbox("Filter by column", st.session_state.pfep_data.columns)
    filter_value = st.text_input("Filter value")
    
    filtered_data = st.session_state.pfep_data
    if filter_value:
        filtered_data = filtered_data[filtered_data[filter_column].astype(str).str.contains(filter_value, case=False)]
    
    st.dataframe(filtered_data)

def add_edit_record():
    st.subheader("Add/Edit Record")
    
    # Select existing part number or create new
    part_numbers = ['New Record'] + list(st.session_state.pfep_data['Part Number'])
    selected_part = st.selectbox("Select Part Number or 'New Record'", part_numbers)
    
    if selected_part == 'New Record':
        record = pd.Series()
    else:
        record = st.session_state.pfep_data[st.session_state.pfep_data['Part Number'] == selected_part].iloc[0]
    
    # Create input fields for each column
    new_record = {}
    for col in st.session_state.pfep_data.columns:
        if col != 'Last Updated':
            new_record[col] = st.text_input(col, value=record.get(col, ''))
    
    if st.button("Save Record"):
        new_record['Last Updated'] = datetime.now()
        if selected_part == 'New Record':
            st.session_state.pfep_data = pd.concat([st.session_state.pfep_data, pd.DataFrame([new_record])], ignore_index=True)
        else:
            st.session_state.pfep_data.loc[st.session_state.pfep_data['Part Number'] == selected_part] = pd.Series(new_record)
        st.success("Record saved successfully!")

def analytics_and_reporting():
    st.subheader("Analytics and Reporting")

    if st.session_state.pfep_data.empty:
        st.warning("No data available for analysis. Please upload or add some data first.")
        return

    # 1. Inventory Analysis
    st.write("### Inventory Analysis")
    fig_inventory = px.bar(st.session_state.pfep_data, 
                           x='Part Number', 
                           y=['Min Inventory', 'Max Inventory'],
                           title="Inventory Levels by Part")
    st.plotly_chart(fig_inventory)

    # 2. Supplier Performance Metrics
    st.write("### Supplier Performance")
    supplier_metrics = st.session_state.pfep_data.groupby('Supplier').agg({
        'Lead Time': 'mean',
        'Part Number': 'count'
    }).rename(columns={'Part Number': 'Number of Parts'})
    st.dataframe(supplier_metrics)

    # 3. Usage Rate Trends
    st.write("### Usage Rate Trends")
    fig_usage = px.line(st.session_state.pfep_data, 
                        x='Part Number', 
                        y='Usage Rate',
                        title="Usage Rate by Part")
    st.plotly_chart(fig_usage)

    # 4. Lead Time Analysis
    st.write("### Lead Time Analysis")
    fig_lead_time = px.histogram(st.session_state.pfep_data, 
                                 x='Lead Time',
                                 title="Distribution of Lead Times")
    st.plotly_chart(fig_lead_time)

    # 5. Dashboard Summary
    st.write("### Dashboard Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Parts", len(st.session_state.pfep_data))
    with col2:
        st.metric("Average Lead Time", f"{st.session_state.pfep_data['Lead Time'].mean():.2f} days")
    with col3:
        st.metric("Total Suppliers", st.session_state.pfep_data['Supplier'].nunique())

def main():
    st.title("Interactive PFEP Management System")

    menu = ["Upload Data", "View Data", "Add/Edit Record", "Analytics and Reporting", "Download Data"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Upload Data":
        upload_excel()
    elif choice == "View Data":
        display_data()
    elif choice == "Add/Edit Record":
        add_edit_record()
    elif choice == "Analytics and Reporting":
        analytics_and_reporting()
    elif choice == "Download Data":
        download_excel()

if __name__ == "__main__":
    main()