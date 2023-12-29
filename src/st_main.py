import datetime

import pandas as pd
import streamlit as st
from icloud_mail_cleaner import ICloudCleaner
from st_supabase_connection import SupabaseConnection

st.set_page_config(
    page_title="iCloud email cleaner",
    page_icon="📨",
    menu_items={
        "About": f"Made with love and care at DataBooth"
        f"\nContact: [Michael Booth](mailto:michael@databooth.com.au)",
        "Get help": "https://www.databooth.com.au",
    },
)


class ICloudCleanerApp:
    def __init__(self):
        self.supabase_connection = SupabaseConnection(
            connection_name="ST-MAIN-APP",
            type=SupabaseConnection,
            ttl=None,
            url=st.secrets["SUPABASE_URL"],
            key=st.secrets["SUPABASE_KEY"],
        )
        self.user = None
        self.cleaner = None
        self.email_list = []

    def authenticate_user(self):
        # Use the SupabaseConnection component for authentication
        # self.user = self.supabase_connection.auth.sign_in_with_password()
        lcol, rcol = st.columns(2)
        email = lcol.text_input(label="Enter your email address:")
        password = rcol.text_input(
            label="Enter your password",
            placeholder="Min 6 characters",
            type="password",
            help="Password is encrypted",
        )
        if email and password:
            self.user = self.supabase_connection.auth.sign_up(email=email, password=password)
        if self.user:
            self.load_user_data()
        else:
            # Display login form using SupabaseConnection component
            # self.supabase_connection.login_form()
            pass

    def load_user_data(self):
        # Load user profile and email list from Supabase
        if self.user:
            result = (
                self.supabase_connection.client.table("profiles")
                .select("email_list")
                .eq("id", self.user.id)
                .execute()
            )
            data = result.data
            if data:
                self.email_list = data[0]["email_list"]

    def save_user_data(self):
        # Save user profile and email list to Supabase
        if self.user:
            self.supabase_connection.client.table("profiles").update(
                {"email_list": self.email_list}
            ).eq("id", self.user.id).execute()

    def log_activity(self, total_emails_count):
        # Log the email cleanup activity
        if self.user:
            self.supabase_connection.client.table("activity_logs").insert(
                {
                    "user_id": self.user.id,
                    "emails_deleted": total_emails_count,
                    "timestamp": datetime.now(),
                }
            ).execute()

    def manage_email_list(self):
        # Upload a file with email addresses
        uploaded_file = st.file_uploader(
            "Upload a file with email addresses (one per line)", type="txt"
        )
        if uploaded_file is not None:
            self.email_list = [
                line.decode("utf-8").strip()
                for line in uploaded_file
                if ICloudCleaner.validate_input_email(line.decode("utf-8").strip())
            ]
            st.success("Email list uploaded successfully!")

        # Add an email address
        new_email = st.text_input("Add an email address")
        if new_email and ICloudCleaner.validate_input_email(new_email):
            if new_email not in self.email_list:
                self.email_list.append(new_email)
                st.success("Email added successfully!")
            else:
                st.error("Email already in the list.")

        # Display and manage the current email list in a scrollable table
        if self.email_list:
            df = pd.DataFrame(self.email_list, columns=["Email Addresses"])
            # Create a temporary column to hold the remove button
            df["Remove"] = "Remove"
            st.dataframe(df)  # Display the dataframe as a table

            # Add functionality to remove an email from the list
            selected_indices = st.multiselect(
                "Select rows to delete",
                options=list(df.index),
                format_func=lambda x: df.iloc[x]["Email Addresses"],
            )
            if st.button("Remove selected emails"):
                self.email_list = [
                    email
                    for idx, email in enumerate(self.email_list)
                    if idx not in selected_indices
                ]
                st.success("Selected emails removed successfully!")

        # Save the email list to the user's profile
        if st.button("Save Email List"):
            self.save_user_data()
            st.success("Email list saved successfully!")

    def run_cleaner(self):
        # Run cleaning process
        if st.button("Clean Mailbox"):
            if self.cleaner and self.email_list:
                total_emails_count = self.cleaner.clean_mailbox(
                    close_mail_app=True, target_emails=self.email_list
                )
                st.success(f"Total emails deleted: {total_emails_count}")
                # Log the activity
                self.log_activity(total_emails_count)
            else:
                st.error("Cleaner is not configured or email list is empty!")

    def main(self):
        # Main app logic
        self.authenticate_user()
        self.manage_email_list()
        self.run_cleaner()


if __name__ == "__main__":
    app = ICloudCleanerApp()
    app.main()
