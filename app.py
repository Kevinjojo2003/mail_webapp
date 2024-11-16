import streamlit as st
import pandas as pd
import pytz
from datetime import datetime
import smtplib
import dns.resolver
from email.mime.base import MIMEBase
from email import encoders
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from pathlib import Path
import json
import time

# --- Configuration and Styling ---
st.set_page_config(
    page_title="✉️ Professional Bulk Email Sender",
    page_icon="✉️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for better styling
st.markdown("""
    <style>
    .stButton>button {
        width: 100%;
        background-color: #4CAF50;
        color: white;
        padding: 0.5rem 1rem;
        border-radius: 5px;
    }
    .error-box {
        padding: 1rem;
        background-color: #ffebee;
        border-left: 5px solid #f44336;
        margin: 1rem 0;
    }
    .success-box {
        padding: 1rem;
        background-color: #e8f5e9;
        border-left: 5px solid #4caf50;
        margin: 1rem 0;
    }
    .info-box {
        padding: 1rem;
        background-color: #e3f2fd;
        border-left: 5px solid #2196f3;
        margin: 1rem 0;
    }
    </style>
""", unsafe_allow_html=True)

# --- Load Templates ---
def load_templates():
    try:
        with open("template.json", "r") as file:
            return json.load(file)
    except FileNotFoundError:
        st.error("Template file not found. Ensure 'template.json' is in the project directory.")
        return {}

templates = load_templates()

# --- Helper Functions ---
def load_contacts(file):
    """Load and validate contacts from CSV file"""
    try:
        df = pd.read_csv(file)
        required_columns = ['Name', 'Email']
        if not all(col in df.columns for col in required_columns):
            st.error("CSV must contain 'Name' and 'Email' columns.")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading contacts: {e}")
        return None

# --- Email Sending Function ---
def send_email(to_email, subject, body, from_email, attachment_path=None):
    try:
        mx_records = dns.resolver.resolve(to_email.split('@')[1], 'MX')
        mail_server = str(mx_records[0].exchange)
        
        # Connect to the mail server
        with smtplib.SMTP(mail_server, 25) as server:
            msg = MIMEMultipart()
            msg['From'] = from_email
            msg['To'] = to_email
            msg['Subject'] = subject
            msg.attach(MIMEText(body, 'plain'))
            
            # Attach a file if provided
            if attachment_path:
                attachment = MIMEBase('application', 'octet-stream')
                with open(attachment_path, 'rb') as attach_file:
                    attachment.set_payload(attach_file.read())
                encoders.encode_base64(attachment)
                attachment.add_header('Content-Disposition', f'attachment; filename={Path(attachment_path).name}')
                msg.attach(attachment)
            
            server.send_message(msg)
        return True
    except Exception as e:
        st.error(f"Failed to send email to {to_email}: {e}")
        return False

# --- Streamlit App Interface ---
st.title("✉️ Professional Bulk Email Sender")
st.sidebar.header("Upload Contact List")

uploaded_file = st.sidebar.file_uploader("Upload CSV file with 'Name' and 'Email' columns", type=['csv'])

selected_template = st.sidebar.selectbox("Choose an Email Template", options=["Select a Template"] + [f"{cat} - {sub}" for cat in templates for sub in templates[cat]])

if uploaded_file and selected_template != "Select a Template":
    contacts_df = load_contacts(uploaded_file)
    if contacts_df is not None:
        st.sidebar.success(f"Loaded {len(contacts_df)} contacts.")

        selected_category, selected_subcategory = selected_template.split(' - ')
        template = templates[selected_category][selected_subcategory]

        # Input fields for email customization
        from_email = st.text_input("Sender Email Address")
        attachment_path = st.file_uploader("Upload Attachment (optional)", type=["pdf", "docx", "png", "jpg"])

        with st.form("email_form"):
            subject = st.text_input("Email Subject", value=template['subject'])
            body = st.text_area("Email Body", value=template['body'])
            submit_button = st.form_submit_button("Send Emails")

            if submit_button and from_email:
                st.info("Sending emails...")
                success_count = 0
                
                for _, contact in contacts_df.iterrows():
                    personalized_body = body.format(Name=contact['Name'])
                    result = send_email(contact['Email'], subject, personalized_body, from_email, attachment_path)
                    if result:
                        success_count += 1
                        time.sleep(1)  # Pause to avoid overwhelming SMTP servers
                
                st.success(f"Emails sent successfully to {success_count} out of {len(contacts_df)} contacts.")
