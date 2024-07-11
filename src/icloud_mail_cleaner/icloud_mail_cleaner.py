import imaplib
import os
import re
import subprocess
import sys
from getpass import getpass
from pathlib import Path

from ..pyproject import PythonProject

from configobj import ConfigObj
from dotenv import load_dotenv
from loguru import logger
from tqdm.autonotebook import tqdm

# TODO: Adjust ICloudCleaner to work with Paths or strings
# TODO: Add typing to the code
# TODO: Add docs (including README.md)
# TODO: Get pytest-ing working

# Load secrets environment variables from .env file
load_dotenv()

class ICloudCleaner:
    def __init__(self, config_file, mode="app", log_level="WARNING"):
        self.config = ConfigObj(config_file)
        self.email_connection = None
        self.mode = mode
        logger.remove()  # Remove default logger
        log_file = self.config.get("Logging", {}).get("log_file", "default.log")
        logger.add(log_file, level="DEBUG")  # Log to file
        logger.add(sys.stderr, level=log_level)  # Log to console with level >= WARNING
        if mode != "app":
            self._ensure_password()
            self._connect()
        else:
            self.password = None
            self.username = None
        logger.info("New cleaning job starting...")

    def _ensure_password(self):
        if os.getenv('ICLOUD_PASSWORD') == "":
            self.password = getpass("Enter your email password: ")
            logger.info("Password obtained from user input.")
        else:
            logger.info("Using password from config.ini.")

    def _connect(self, mailbox="INBOX"):
        try:
            self.email_connection = imaplib.IMAP4_SSL(
                self.config["imap_server"], self.config["imap_port"]
            )
            logger.info(f"Username: {os.getenv('ICLOUD_USERNAME')}; IMAP server: {self.config['imap_server']}; Port: {self.config['imap_port']}")
            self.email_connection.login(os.getenv('ICLOUD_USERNAME'), os.getenv('ICLOUD_PASSWORD'))
            self.email_connection.select(mailbox)
            logger.info(f"Successfully connected to {os.getenv('ICLOUD_USERNAME')}@icloud.com - {mailbox}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def connect(self, username, password, imap_server, imap_port, mailbox="INBOX"):
        try:
            self.email_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
            self.email_connection.login(username, password)
            self.email_connection.select(mailbox)
            logger.info(f"Successfully connected to {username}@icloud.com - {mailbox}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise

    def search_emails(self, sender):
        try:
            _, data = self.email_connection.search(None, f'(FROM "{sender}")')
            mail_ids = data[0]
            return mail_ids.split() if mail_ids else None
        except Exception as e:
            logger.error(f"Error searching emails from {sender}: {e}")
            return None

    def set_deleted(self, email_uid):
        try:
            self.email_connection.uid(
                "STORE", bytes(str(email_uid).strip(), "ascii"), "+FLAGS", "(\\Deleted)"
            )
            logger.info(f"Email UID {email_uid} marked for deletion.")
        except Exception as e:
            logger.error(f"Error setting email UID {email_uid} as deleted: {e}")

    def fetch_uid(self, email_id):
        try:
            _, uid_string = self.email_connection.fetch(email_id, "UID")
            uid_str = [str(x, encoding="utf-8") for x in uid_string]
            uid_res = re.search(r"\((UID.*?)\)", uid_str[0])
            return uid_res[1].replace("UID", "") if uid_res else None
        except Exception as e:
            logger.error(f"Error fetching UID for email ID {email_id}: {e}")
            return None

    def load_target_emails(self):
        target_emails_file = self.config.get("target_emails_file")
        target_emails_file = f"{PythonProject().root}/{target_emails_file}"
        if target_emails_file and Path(target_emails_file).is_file():
            with open(target_emails_file, "r") as file:
                target_emails = file.read().splitlines()
                logger.info(f"Imported {len(target_emails)} emails from {target_emails_file}.")
                # print(f"INFO: Imported {len(target_emails)} emails from {target_emails_file}")
                return target_emails
        else:
            if not Path(target_emails_file).exists():
                logger.error(f"ERROR: {target_emails_file} not found.")
            logger.info(
                "No target emails file specified or file does not exist. Using provided email list."
            )
            return []

    def clean_mailbox(self, close_mail_app=True, target_emails=None):
        if close_mail_app and self.is_apple_mail_app_running():
            logger.info("INFO: Mail app is being closed...")
            self.close_mail_app()
        try:
            if target_emails is None:
                target_emails = self.load_target_emails()
            if not target_emails:
                logger.error("No target emails provided.")
                raise ValueError("No target emails provided.")
            total_emails_deleted = 0

            # Initialize tqdm for the total emails
            with tqdm(total=len(target_emails), desc="Total emails") as pbar:
                for target_email in target_emails:
                    if not self.validate_input_email(target_email):
                        logger.warning(f"The email '{target_email}' is not valid")
                        pbar.update(1)
                        continue

                    emails = self.search_emails(target_email)
                    emails_count = len(emails) if emails else 0
                    n_deleted_email = 0

                    while emails_count > 0:
                        for email in tqdm(emails, total=emails_count, desc=target_email):
                            uid = self.fetch_uid(email)
                            if uid:
                                self.set_deleted(uid)
                                n_deleted_email += 1

                        self.email_connection.expunge()
                        logger.info(f"Deleted {emails_count} email(s) for {target_email}")
                        emails = self.search_emails(target_email)
                        emails_count = len(emails) if emails else 0

                    logger.info(
                        f"Cleanup for {target_email} was successful. Deleted {n_deleted_email} email(s)"
                    )
                    total_emails_deleted += n_deleted_email
                    pbar.update(1)  # Update the total emails progress bar

            logger.info(f"The cleanup was successful. Deleted {total_emails_deleted} email(s)")
            return total_emails_deleted

        finally:
            self.close_connection()

    def close_connection(self):
        if self.email_connection:
            try:
                self.email_connection.close()
                self.email_connection.logout()
                logger.info("IMAP connection closed successfully.")
            except Exception as e:
                logger.error(f"Failed to close IMAP connection: {e}")

    @staticmethod
    def validate_input_email(email_address):
        if re.match(r"[^@]+@[^@]+\.[^@]+", email_address):
            return True
        else:
            logger.warning(f"Invalid email format: {email_address}")
            return False

    @staticmethod
    def import_emails_from_file(filename):
        if Path(filename).is_file():
            with open(filename, "r") as file:
                emails = file.read().splitlines()
                logger.info(f"Imported {len(emails)} emails from {filename}.")
                return emails
        else:
            logger.error(f"The file {filename} doesn't exist.")
            return []

    def is_apple_mail_app_running(self):
        try:
            script = 'tell application "System Events" to (name of processes) contains "Mail"'
            result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True)
            return "true" in result.stdout.lower()
        except Exception as e:
            logger.error(f"Error checking if Mail app is running: {e}")
            return False

    def close_mail_app(self):
        if self.is_apple_mail_app_running():
            try:
                script = 'tell application "Mail" to quit'
                subprocess.run(["osascript", "-e", script], capture_output=True)
                logger.info("Mail app closed successfully.")
            except Exception as e:
                logger.error(f"Error closing Mail app: {e}")
