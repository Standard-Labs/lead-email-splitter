"""Main app to split emails into unqiue rows."""
import streamlit as st
import pandas as pd
import re
import io
import ast

def parse_email_array(email_array_str):
    """Parse the email array string to extract email addresses."""
    if pd.isna(email_array_str) or email_array_str == '[]':
        return []
        
    # Handle the format: "[email1@domain.com, email2@domain.com]"
    try:
        # Use ast.literal_eval for safer parsing of the string representation of a list
        return ast.literal_eval(email_array_str)
    except (ValueError, SyntaxError):
        # Fallback to regex if ast.literal_eval fails
        emails = re.findall(r'[\w\.-]+@[\w\.-]+', email_array_str)
        return emails

def process_csv(df):
    """Process the CSV to split rows with multiple emails into separate rows."""
    # Make a copy of the dataframe to avoid modifying the original
    df_copy = df.copy()
    
    # Parse the email array column
    df_copy['parsed_emails'] = df_copy['pii.Email_Array'].apply(parse_email_array)
    
    # Count emails before processing
    total_emails_before = df_copy['parsed_emails'].apply(len).sum()
    total_rows_before = len(df_copy)
    
    # Filter out rows with no emails
    df_with_emails = df_copy[df_copy['parsed_emails'].apply(len) > 0].copy()
    
    # Explode the dataframe to have one row per email
    df_exploded = df_with_emails.explode('parsed_emails')
    
    # Rename the column to 'email' for clarity
    df_exploded = df_exploded.rename(columns={'parsed_emails': 'email'})
    
    # Count stats after processing
    total_rows_after = len(df_exploded)
    
    return df_exploded, {
        'rows_before': total_rows_before,
        'rows_after': total_rows_after,
        'emails_found': total_emails_before
    }

def main():
    """Main function to run the Streamlit app."""
    st.title('Lead Email Splitter')
    
    st.write("""
    ## Purpose
    This app takes a CSV file with leads where some rows have multiple email addresses 
    and splits them into separate rows, one for each email address.
    
    ## How to use
    1. Upload your CSV file using the uploader below
    2. The app will process the file and show you the results
    3. You can download the processed file using the download button
    """)
    
    uploaded_file = st.file_uploader("Choose a CSV file", type="csv")
    
    if uploaded_file is not None:
        # Read the CSV file
        df = pd.read_csv(uploaded_file)
        
        # Show the original dataframe
        st.subheader("Original Data (First 5 Rows)")
        st.dataframe(df.head())
        
        # Check if the required column exists
        if 'pii.Email_Array' not in df.columns:
            st.error("The CSV file must contain a column named 'pii.Email_Array' with email addresses.")
        else:
            # Process the CSV
            with st.spinner('Processing CSV...'):
                df_processed, stats = process_csv(df)
            
            # Show processing stats
            st.success(f"Processing complete! Found {stats['emails_found']} emails in {stats['rows_before']} rows. "
                      f"Generated {stats['rows_after']} rows after splitting.")
            
            # Show the processed dataframe
            st.subheader("Processed Data (First 5 Rows)")
            st.dataframe(df_processed.head())
            
            # Allow the user to download the processed file
            csv = df_processed.to_csv(index=False)
            st.download_button(
                label="Download Processed CSV",
                data=csv,
                file_name="processed_leads.csv",
                mime="text/csv",
            )
            
            # Show additional details about the data
            with st.expander("View Data Details"):
                st.subheader("Email Distribution")
                email_counts = df['pii.Email_Array'].apply(lambda x: len(parse_email_array(x)))
                email_distribution = email_counts.value_counts().reset_index()
                email_distribution.columns = ['Number of Emails', 'Count of Leads']
                st.dataframe(email_distribution)

if __name__ == "__main__":
    main()
