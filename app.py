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
import time
import json

# --- Configuration and Styling ---
st.set_page_config(
    page_title="📧 Professional Bulk Email Sender",
    page_icon="📧",
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

# --- Load Templates from JSON ---
def load_templates():
    with open('templates.json', 'r') as file:
        return json.load(file)

templates = load_templates()

# --- Helper Functions ---
def load_contacts(file):
    """Load and validate contacts from CSV file"""
    try:
        df = pd.read_csv(file)
        required_columns = ['Name', 'Email']
        if not all(col in df.columns for col in required_columns):
            st.error("CSV must contain 'Name' and 'Email' columns")
            return None
        return df
    except Exception as e:
        st.error(f"Error loading contacts: {str(e)}")
        return None

def validate_email(email):
    """Basic email validation"""
    import re
    pattern = r'^[\w\.-]+@[\w\.-]+\.\w+$'
    return re.match(pattern, email) is not None

def get_mx_server(domain):
    """Lookup MX records with error handling"""
    try:
        result = dns.resolver.resolve(domain, 'MX')
        return sorted([(r.preference, r.exchange.to_text()) for r in result])[0][1]
    except Exception as e:
        st.error(f"MX lookup failed for {domain}: {str(e)}")
        return None

# --- Main Application Logic ---
def main():
    # Sidebar navigation with custom styling
    with st.sidebar:
        st.image("assets/logo.png", width=150)
        st.title("Email Sender")
        selected_page = st.radio(
            "Navigation",
            ["Dashboard", "Send Emails", "Templates", "Settings"],
            index=0
        )
        
        # Show current timezone info
        st.markdown("---")
        selected_timezone = st.selectbox(
            "Timezone",
            pytz.common_timezones,
            index=pytz.common_timezones.index('UTC')
        )
        local_time = datetime.now(pytz.timezone(selected_timezone))
        st.caption(f"Local time: {local_time.strftime('%H:%M:%S')}")

    # Page content
    if selected_page == "Dashboard":
        st.title("📊 Dashboard")
        
        # Statistics cards in columns
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Emails Sent Today", "0")
        with col2:
            st.metric("Delivery Rate", "0%")
        with col3:
            st.metric("Templates Available", str(sum(len(cat) for cat in templates.values())))
        
        # Recent activity
        st.subheader("Recent Activity")
        st.info("No recent email campaigns")

    elif selected_page == "Send Emails":
        st.title("📤 Send Bulk Emails")

        # Create tabs for different steps
        tab1, tab2, tab3 = st.tabs(["1. Setup", "2. Content", "3. Review & Send"])
        
        with tab1:
            st.subheader("Email Configuration")
            sender_email = st.text_input("Sender Email Address")
            sender_name = st.text_input("Sender Name")
            smtp_password = st.text_input("SMTP Password", type="password")
            
            st.subheader("Upload Contacts")
            contacts_file = st.file_uploader(
                "Upload CSV file with contacts",
                type=['csv'],
                help="CSV must contain 'Name' and 'Email' columns"
            )
            
            if contacts_file:
                contacts_df = load_contacts(contacts_file)
                if contacts_df is not None:
                    st.success(f"✅ Loaded {len(contacts_df)} contacts")
                    st.dataframe(contacts_df.head())

        with tab2:
            st.subheader("Email Content")
            
            # Template selection
            category = st.selectbox("Category", list(templates.keys()))
            template_name = st.selectbox("Template", list(templates[category].keys()))
            selected_template = templates[category][template_name]
            
            # Email content editing
            subject = st.text_input("Subject", value=selected_template["subject"])
            body = st.text_area("Body", value=selected_template["body"], height=300)
            
            # Attachments
            st.subheader("Attachments")
            files = st.file_uploader("Upload files", accept_multiple_files=True)
            if files:
                for file in files:
                    st.write(f"📎 {file.name}")

        with tab3:
            st.subheader("Review & Send")
            
            # Show preview
            if 'contacts_df' in locals():
                st.info("Preview for first recipient:")
                preview_data = {
                    "Name": contacts_df.iloc[0]["Name"],
                    "ProductDetails": "Sample product details",
                    "ProductLink": "https://example.com",
                    "SenderName": sender_name
                }
                try:
                    preview_body = body.format(**preview_data)
                    st.code(preview_body)
                except KeyError as e:
                    st.error(f"Template error: Missing field {str(e)}")
            
            # Send button with confirmation
            if st.button("Send Emails"):
                # Add sending logic here
                with st.spinner("Sending emails..."):
                    time.sleep(2)  # Simulate sending
                    st.success("✅ Emails sent successfully!")

    elif selected_page == "Templates":
        st.title("📝 Email Templates")
        
        # Template management interface
        for category in templates:
            st.subheader(category)
            for template_name, template_content in templates[category].items():
                with st.expander(template_name):
                    st.write("**Subject:**", template_content["subject"])
                    st.write("**Body:**")
                    st.text(template_content["body"])

    elif selected_page == "Settings":
        st.title("⚙️ Settings")
        
        # SMTP Settings
        st.subheader("SMTP Configuration")
        smtp_host = st.text_input("SMTP Host", value="smtp.gmail.com")
        smtp_port = st.number_input("SMTP Port", value=587)
        
        # Email Limits
        st.subheader("Sending Limits")
        daily_limit = st.slider("Daily Email Limit", 0, 2000, 500)
        batch_size = st.slider("Batch Size", 10, 100, 50)
        
        if st.button("Save Settings"):
            st.success("Settings saved successfully!")

if __name__ == "__main__":
    main()
