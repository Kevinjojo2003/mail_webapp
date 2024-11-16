import smtplib
import pandas as pd
import streamlit as st
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import time
from datetime import datetime
from io import StringIO

# Function to send bulk emails with additional features
def send_bulk_emails(sender_email, sender_password, contacts, subject, body_template, attachment=None, delay=0):
    try:
        # Connect to the SMTP server
        server = smtplib.SMTP('smtp.gmail.com', 587)
        server.starttls()  # Secure the connection
        server.login(sender_email, sender_password)

        # Loop through each contact and send an email
        for index, row in contacts.iterrows():
            recipient_name = row['Name']
            recipient_email = row['Email']

            # Personalize the email body
            personalized_body = f"Dear {recipient_name},\n\n{body_template}\n\nRegards,\nKevin Jojo"

            # Create the email
            msg = MIMEMultipart()
            msg['From'] = sender_email
            msg['To'] = recipient_email
            msg['Subject'] = subject
            msg.attach(MIMEText(personalized_body, 'plain'))

            # Attach a file if provided
            if attachment:
                part = MIMEBase('application', 'octet-stream')
                part.set_payload(attachment.read())
                encoders.encode_base64(part)
                part.add_header('Content-Disposition', f"attachment; filename={attachment.name}")
                msg.attach(part)

            # Send the email
            server.sendmail(sender_email, recipient_email, msg.as_string())
            st.success(f"Email sent to {recipient_name} ({recipient_email})")

            # Delay between emails if specified
            if delay > 0:
                time.sleep(delay)

        # Close the server connection
        server.quit()
        st.success("All emails sent successfully!")
    except Exception as e:
        st.error(f"Failed to send emails: {e}")

# Streamlit app UI
st.title("Enhanced Bulk Email Sender with Scheduler")

# User inputs
sender_email = st.text_input("Your Email")
sender_password = st.text_input("Your Password", type="password")
contact_input_option = st.radio("How would you like to input email contacts?", ("Upload CSV File", "Manual Input"))

if contact_input_option == "Upload CSV File":
    csv_file = st.file_uploader("Upload CSV File", type=["csv"])
    if csv_file is not None:
        contacts = pd.read_csv(csv_file)
else:
    manual_input = st.text_area("Enter contacts (Name,Email on each line)")
    if manual_input:
        contacts = pd.read_csv(StringIO(manual_input), header=None, names=["Name", "Email"])
        st.write("Contacts preview:", contacts)

subject = st.text_input("Email Subject")
body_template = st.text_area("Email Body Template")
attachment = st.file_uploader("Upload Attachment (optional)")
delay = st.slider("Delay between emails (seconds)", 0, 60, 0)
schedule_time = st.text_input("Schedule (YYYY-MM-DD HH:MM, optional)")

if st.button("Send Emails"):
    if sender_email and sender_password and 'contacts' in locals() and subject and body_template:
        if schedule_time:
            try:
                schedule_dt = datetime.strptime(schedule_time, "%Y-%m-%d %H:%M")
                current_dt = datetime.now()
                if schedule_dt > current_dt:
                    st.info(f"Scheduled to send emails at {schedule_dt}")
                    time.sleep((schedule_dt - current_dt).total_seconds())
            except ValueError:
                st.error("Invalid date format. Please use YYYY-MM-DD HH:MM.")
        send_bulk_emails(sender_email, sender_password, contacts, subject, body_template, attachment, delay)
    else:
        st.warning("Please fill out all fields and provide contacts.")
