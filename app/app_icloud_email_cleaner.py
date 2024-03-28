import re
from pathlib import Path

import duckdb
import pandas as pd
import streamlit as st
from icloud_mail_cleaner.icloud_mail_cleaner import ICloudCleaner

# Assuming the config.ini is in the parent directory of the current script
CONFIG_FILE = Path(__file__).parent.parent / "config.ini"
EMAIL_LIST_PATH = "data/target_email_address.txt"


class EmailDatabaseManager:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = duckdb.connect(db_path)
        self.initialise_database()

    def initialise_database(self):
        self.conn.execute(
            """
            CREATE TABLE IF NOT EXISTS emails (
                id INTEGER PRIMARY KEY,
                email TEXT UNIQUE NOT NULL,
                added TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """
        )

    def load_emails(self):
        result = self.conn.execute("SELECT email FROM emails").fetchall()
        return [email[0] for email in result]

    def save_emails(self, emails):
        for email in emails:
            self.conn.execute("INSERT OR IGNORE INTO emails (email) VALUES (?)", (email,))

    # Additional methods for cleaning and validating emails would be similar to those in EmailManager


class EmailManager:
    def __init__(self, email_list_path):
        self.email_list_path = Path(email_list_path)

    def load_emails(self):
        """Load emails from a file into a list."""
        try:
            with self.email_list_path.open("r") as file:
                emails = file.read().splitlines()
            return emails
        except FileNotFoundError:
            return []

    def save_emails(self, emails):
        """Save a list of emails back to the file."""
        with self.email_list_path.open("w") as file:
            for email in emails:
                file.write(f"{email}\n")

    @staticmethod
    def is_valid_email(email):
        """Check if the email address has a valid format."""
        email_pattern = r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$"
        return re.match(email_pattern, email) is not None

    def clean_emails(self, emails):
        """Remove duplicates and invalid emails from the list."""
        cleaned_emails = []
        for email in emails:
            if email not in cleaned_emails and self.is_valid_email(email):
                cleaned_emails.append(email)
        return cleaned_emails


class ICloudEmailCleanerApp:
    def __init__(self, config_file, email_list_path):
        self.config_file = config_file
        self.email_manager = EmailManager(email_list_path)
        if "username" not in st.session_state:
            st.session_state["username"] = ""
        if "password" not in st.session_state:
            st.session_state["password"] = ""
        if "imap_server" not in st.session_state:
            st.session_state["imap_server"] = "imap.mail.me.com"  # Default IMAP server for iCloud
        if "imap_port" not in st.session_state:
            st.session_state["imap_port"] = "993"  # Default IMAP port

    def run(self):
        st.title("iCloud Email Cleaner")

        # Check if credentials are provided
        if not st.session_state["username"] or not st.session_state["password"]:
            st.warning("Please enter your iCloud username and password in the sidebar to proceed.")
            self.display_sidebar()
            return  # Exit the function early

        # Proceed with the rest of the app if credentials are provided
        self.display_sidebar()

        # Load emails and display them
        emails = self.email_manager.load_emails()
        emails_df = pd.DataFrame(emails, columns=["Email Addresses"])
        st.write(emails_df)

        # Add new email
        new_email = st.text_input("Add a new email address", "")
        if st.button("Add Email"):
            if new_email and new_email not in emails and EmailManager.is_valid_email(new_email):
                emails.append(new_email)
                self.email_manager.save_emails(emails)
                st.success("Email added successfully.")
                st.rerun()
            else:
                st.error("Email is either empty, invalid, or already exists.")

        # # Button to clean emails in iCloud
        # if st.button("Clean Emails in iCloud"):
        #     cleaned_emails = self.email_manager.clean_emails(emails)
        #     if len(cleaned_emails) < len(emails):
        #         self.email_manager.save_emails(cleaned_emails)
        #         st.success(f"Email list cleaned. Removed {len(emails) - len(cleaned_emails)} entries.")
        #         st.rerun()
        #     else:
        #         st.info("No changes made. Your email list is already clean.")

        if st.button("Clean iCloud emails"):
            # try:
            # st.write(f"Config file: {CONFIG_FILE.as_posix()}")
            cleaner = ICloudCleaner(config_file=CONFIG_FILE.as_posix())
            if cleaner.mode == "app":
                cleaner.connect(
                    st.session_state["username"],
                    st.session_state["password"],
                    st.session_state["imap_server"],
                    st.session_state["imap_port"],
                )
            else:
                st.info("Please enter your iCloud details.")
            total_emails_deleted = cleaner.clean_mailbox(close_mail_app=True, target_emails=emails)
            st.success(f"Total emails deleted: {total_emails_deleted}")
            # except Exception as e:
            #     st.error(f"An error occurred: {e}")

    def display_sidebar(self):
        st.sidebar.header("iCloud Account")
        st.sidebar.text_input("Username", key="username")
        st.sidebar.text_input("Password", type="password", key="password")
        st.sidebar.text_input("IMAP server:", value="", key="imap_server")
        st.sidebar.text_input("IMAP port:", value="993", key="imap_port")
        st.sidebar.header("Database Settings")
        st.sidebar.text("Future settings for DuckDB will go here.")


if __name__ == "__main__":
    app = ICloudEmailCleanerApp(CONFIG_FILE.as_posix(), EMAIL_LIST_PATH)
    app.run()
