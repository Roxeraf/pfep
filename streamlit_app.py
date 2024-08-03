import streamlit as st
import pandas as pd
import io
from datetime import datetime

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

def main():
    st.title("Interactive PFEP Management System")

    menu = ["Upload Data", "View Data", "Add/Edit Record", "Download Data"]
    choice = st.sidebar.selectbox("Menu", menu)

    if choice == "Upload Data":
        upload_excel()
    elif choice == "View Data":
        display_data()
    elif choice == "Add/Edit Record":
        add_edit_record()
    elif choice == "Download Data":
        download_excel()

if __name__ == "__main__":
    main()