import streamlit as st
import pandas as pd
import io
from datetime import datetime
import plotly.express as px
import plotly.graph_objects as go
from sklearn.linear_model import LinearRegression
from sklearn.model_selection import train_test_split
import numpy as np

# Initialize session state to store our data
if 'pfep_data' not in st.session_state:
    st.session_state.pfep_data = pd.DataFrame(columns=[
        'Part Number', 'Description', 'Supplier', 'Packaging', 'Storage Location', 
        'Usage Rate', 'Min Inventory', 'Max Inventory', 'Lead Time', 'Last Updated',
        'Order Frequency', 'Min Inventory Level', 'Max Inventory Level', 
        'Avg Lead Time (days)', 'Unit of Measure', 'Packaging Dimensions (LxWxH)',
        'Reusable Packaging', 'Reusable Packaging Lead Time (days)'
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
            if col == 'Reusable Packaging':
                new_record[col] = st.checkbox(col, value=record.get(col, False))
            elif col == 'Packaging Dimensions (LxWxH)':
                new_record[col] = st.text_input(col, value=record.get(col, ''))
            else:
                new_record[col] = st.text_input(col, value=record.get(col, ''))
    
    if st.button("Save Record"):
        new_record['Last Updated'] = datetime.now()
        if selected_part == 'New Record':
            st.session_state.pfep_data = pd.concat([st.session_state.pfep_data, pd.DataFrame([new_record])], ignore_index=True)
        else:
            st.session_state.pfep_data.loc[st.session_state.pfep_data['Part Number'] == selected_part] = pd.Series(new_record)
        st.success("Record saved successfully!")

def analytics_and_reporting():
    st.subheader("Advanced Analytics and Reporting")

    if st.session_state.pfep_data.empty:
        st.warning("No data available for analysis. Please upload or add some data first.")
        return

    # Filtering options
    st.sidebar.subheader("Filters")
    selected_suppliers = st.sidebar.multiselect(
        "Select Suppliers", options=st.session_state.pfep_data['Supplier'].unique()
    )
    selected_parts = st.sidebar.multiselect(
        "Select Parts", options=st.session_state.pfep_data['Part Number'].unique()
    )

    # Apply filters
    filtered_data = st.session_state.pfep_data
    if selected_suppliers:
        filtered_data = filtered_data[filtered_data['Supplier'].isin(selected_suppliers)]
    if selected_parts:
        filtered_data = filtered_data[filtered_data['Part Number'].isin(selected_parts)]

    # Convert numeric columns to appropriate types
    numeric_columns = ['Usage Rate', 'Min Inventory', 'Max Inventory', 'Lead Time', 
                       'Min Inventory Level', 'Max Inventory Level', 'Avg Lead Time (days)']
    for col in numeric_columns:
        filtered_data[col] = pd.to_numeric(filtered_data[col], errors='coerce')

    # 1. Enhanced Inventory Analysis
    st.write("### Inventory Analysis")
    fig_inventory = px.bar(filtered_data, 
                           x='Part Number', 
                           y=['Min Inventory', 'Max Inventory', 'Usage Rate'],
                           title="Inventory Levels and Usage Rate by Part")
    st.plotly_chart(fig_inventory)

    # 2. Supplier Performance Metrics and Rating System
    st.write("### Supplier Performance and Rating")
    supplier_metrics = filtered_data.groupby('Supplier').agg({
        'Avg Lead Time (days)': 'mean',
        'Lead Time': 'std',
        'Part Number': 'count',
        'Usage Rate': 'sum'
    }).reset_index()
    supplier_metrics.columns = ['Supplier', 'Avg Lead Time', 'Lead Time Std', 'Number of Parts', 'Total Usage']
    
    # Calculate a simple supplier rating (lower is better)
    supplier_metrics['Rating'] = (
        supplier_metrics['Avg Lead Time'] * 0.4 +
        supplier_metrics['Lead Time Std'] * 0.3 +
        (1 / supplier_metrics['Number of Parts']) * 0.3
    )
    supplier_metrics['Rating'] = supplier_metrics['Rating'].round(2)
    
    st.dataframe(supplier_metrics.sort_values('Rating'))

    # 3. Usage Rate Trends and Predictive Analytics
    st.write("### Usage Rate Trends and Prediction")
    if len(filtered_data['Part Number'].unique()) > 0:
        selected_part = st.selectbox("Select a part for prediction", filtered_data['Part Number'].unique())
        part_data = filtered_data[filtered_data['Part Number'] == selected_part]
        
        if len(part_data) > 1:  # Ensure we have enough data points for prediction
            # Assuming we have historical data with timestamps
            # For this example, we'll simulate it
            part_data['Timestamp'] = pd.date_range(end=pd.Timestamp.now(), periods=len(part_data), freq='D')
            part_data['Days'] = (part_data['Timestamp'] - part_data['Timestamp'].min()).dt.days
            
            # Prepare data for prediction
            X = part_data[['Days']]
            y = part_data['Usage Rate']
            X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
            
            # Train a simple linear regression model
            model = LinearRegression()
            model.fit(X_train, y_train)
            
            # Make future predictions
            future_days = pd.DataFrame({'Days': range(X['Days'].max(), X['Days'].max() + 30)})
            future_predictions = model.predict(future_days)
            
            # Plot actual and predicted usage
            fig_usage = go.Figure()
            fig_usage.add_trace(go.Scatter(x=part_data['Timestamp'], y=part_data['Usage Rate'], mode='markers', name='Actual Usage'))
            fig_usage.add_trace(go.Scatter(x=pd.date_range(start=part_data['Timestamp'].max(), periods=30, freq='D'), 
                                           y=future_predictions, mode='lines', name='Predicted Usage'))
            fig_usage.update_layout(title=f"Usage Rate Trend and Prediction for {selected_part}")
            st.plotly_chart(fig_usage)
        else:
            st.warning(f"Not enough data points for part {selected_part} to make predictions.")
    else:
        st.warning("No parts available for prediction.")

    # 4. Lead Time Analysis
    st.write("### Lead Time Analysis")
    fig_lead_time = px.box(filtered_data, x='Supplier', y='Avg Lead Time (days)', title="Lead Time Distribution by Supplier")
    st.plotly_chart(fig_lead_time)

    # 5. Enhanced Dashboard Summary
    st.write("### Dashboard Summary")
    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("Total Parts", len(filtered_data))
    with col2:
        st.metric("Average Lead Time", f"{filtered_data['Avg Lead Time (days)'].mean():.2f} days")
    with col3:
        st.metric("Total Suppliers", filtered_data['Supplier'].nunique())

    # 6. Inventory Optimization Suggestions
    st.write("### Inventory Optimization Suggestions")
    inventory_suggestions = filtered_data[filtered_data['Usage Rate'] > filtered_data['Max Inventory']]
    if not inventory_suggestions.empty:
        st.warning("The following parts may need increased max inventory levels:")
        st.dataframe(inventory_suggestions[['Part Number', 'Usage Rate', 'Max Inventory']])
    else:
        st.success("Current inventory levels appear to be sufficient based on usage rates.")

def main():
    st.title("Advanced PFEP Management System")

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