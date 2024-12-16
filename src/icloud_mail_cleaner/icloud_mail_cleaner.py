import imaplib
import os
import platform
import re
import subprocess
import sys
from getpass import getpass
from pathlib import Path
from typing import List, Optional, Union

from configobj import ConfigObj
from dotenv import load_dotenv
from loguru import logger
from tenacity import retry, stop_after_attempt, wait_exponential
from tqdm.autonotebook import tqdm

from .pyproject import PythonProject

# TODO: Get pytest-ing working

# Load secrets environment variables from .env file
load_dotenv()


class ICloudConnectionError(Exception):
    """Custom exception for iCloud connection errors."""

    pass


class EmailSearchError(Exception):
    """Custom exception for email search errors."""

    pass


class EmailDeletionError(Exception):
    """Custom exception for email deletion errors."""

    pass


class ICloudCleaner:
    """
    A class to manage and clean iCloud email accounts.

    This class provides functionality to connect to an iCloud email account,
    search for emails from specific senders, and delete them in bulk.
    """   
    def __init__(self, config_file: Union[str, Path], mode: str = "app", log_level: str = "WARNING"):
        self.config = ConfigObj(str(config_file))
        self.email_connection: Optional[imaplib.IMAP4_SSL] = None
        self.mode = mode
        self.is_connected = False
        self.username: Optional[str] = None
        self.password: Optional[str] = None
        self._setup_logging(log_level)
        if mode != "app":
            self._ensure_password()
            self._connect()
        logger.info("New cleaning job starting...")


    def print_config(self):
        """Print out the current configuration settings."""
        print("Configuration Settings:")
        for section in self.config:
            print(f"\n[{section}]")
            print(f"Type: {type(self.config[section])}")
            if isinstance(self.config[section], dict):
                for key, value in self.config[section].items():
                    print(f"{key} = {value}")
            else:
                print(self.config[section])


    def _setup_logging(self, log_level: str) -> None:
        """Set up logging configuration."""
        logger.remove()  # Remove default logger
        log_file = self.config.get("Logging", {}).get("log_file", "icloud_cleaner.log")
        logger.add(log_file, level="DEBUG", rotation="10 MB", compression="zip")
        logger.add(sys.stderr, level=log_level)

    def ensure_connection(self):
        if not self.is_connected:
            if not self.username or not self.password:
                raise ValueError("Username and password must be set before connecting")
            self._connect()

    def _ensure_password(self) -> None:
        """Ensure that the iCloud username and password are available."""
        self.username = os.getenv("ICLOUD_USERNAME")
        if not self.username:
            self.username = input("Enter your iCloud username: ")
        
        if os.getenv("ICLOUD_PASSWORD") == "":
            self.password = getpass("Enter your email password: ")
            logger.info("Password obtained from user input.")
        else:
            self.password = os.getenv("ICLOUD_PASSWORD")
            logger.info("Using password from environment variable.")


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def _connect(self, mailbox: str = "INBOX") -> None:
        try:
            self.email_connection = imaplib.IMAP4_SSL(self.config["imap_server"], int(self.config["imap_port"]))
            self.email_connection.login(self.username, self.password)
            self.email_connection.select(mailbox)
            self.is_connected = True
            logger.info(f"Successfully connected to {self.username}@icloud.com - {mailbox}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            raise ICloudConnectionError(f"Failed to connect to iCloud: {e}")


    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def search_emails(self, sender: str) -> Optional[List[bytes]]:
        self.ensure_connection()
        try:
            _, data = self.email_connection.search(None, f'(FROM "{sender}")')
            mail_ids = data[0]
            return mail_ids.split() if mail_ids else None
        except imaplib.IMAP4.error as e:
            if "LOGOUT" in str(e):
                logger.warning("Connection lost. Attempting to reconnect.")
                self.is_connected = False
                self.ensure_connection()
                return self.search_emails(sender)
            logger.error(f"Error searching emails from {sender}: {e}")
            return None

    @retry(stop=stop_after_attempt(3), wait=wait_exponential(multiplier=1, min=4, max=10))
    def set_deleted(self, email_uid: Union[str, bytes]) -> None:
        """
        Mark an email for deletion.

        Args:
            email_uid (Union[str, bytes]): The UID of the email to be deleted.

        Raises:
            EmailDeletionError: If there's an error marking the email for deletion.
        """
        try:
            self.email_connection.uid("STORE", bytes(str(email_uid).strip(), "ascii"), "+FLAGS", "(\\Deleted)")
            logger.info(f"Email UID {email_uid} marked for deletion.")
        except Exception as e:
            logger.error(f"Error setting email UID {email_uid} as deleted: {e}")
            raise EmailDeletionError(f"Error marking email UID {email_uid} for deletion: {e}")


    def clean_mailbox(self, target_emails: List[str] = None, close_mail_app: bool = True) -> List[tuple]:
        """
        Clean the mailbox by deleting emails from specified senders.

        Args:
            close_mail_app (bool): Whether to close the Mail app before cleaning.
            target_emails (Optional[List[str]]): List of email addresses to target for deletion.

        Returns:
            int: The total number of emails deleted.

        Raises:
            ValueError: If no target emails are provided.
        """
        if close_mail_app and self.is_mail_app_running():
            logger.info("Mail app is being closed...")
            self.close_mail_app()

        if target_emails is None:
            target_emails = self.load_target_emails()

        self.ensure_connection()
        results = []
        

        with tqdm(total=len(target_emails), desc="Overall progress") as pbar:
            for target_email in target_emails:
                emails = self.search_emails(target_email)
                count = 0
                if emails:
                    with tqdm(total=len(emails), desc=f"Processing {target_email}", leave=False) as email_pbar:
                        for email in emails:
                            uid = self.fetch_uid(email)
                            if uid:
                                self.set_deleted(uid)
                                count += 1
                            email_pbar.update(1)
                self.email_connection.expunge()
                results.append((target_email.strip(), count))
                pbar.update(1)
        return results


    def connect(self, username: str, password: str, imap_server: str, imap_port: int, mailbox: str = "INBOX"):
        try:
            if self.email_connection:
                self.close_connection()
            
            self.email_connection = imaplib.IMAP4_SSL(imap_server, imap_port)
            self.email_connection.login(username, password)
            self.email_connection.select(mailbox)
            self.is_connected = True
            self.username = username
            self.password = password
            logger.info(f"Successfully connected to {username}@icloud.com - {mailbox}")
        except Exception as e:
            logger.error(f"Failed to connect: {e}")
            self.is_connected = False
            raise

    def close_connection(self):
        if self.is_connected and self.email_connection:
            try:
                self.email_connection.close()
                self.email_connection.logout()
                logger.info("IMAP connection closed successfully.")
            except Exception as e:
                logger.error(f"Failed to close IMAP connection: {e}")
            finally:
                self.is_connected = False
                self.email_connection = None
                self.username = None
                self.password = None

    def fetch_uid(self, email_id: bytes) -> Optional[str]:
        """
        Fetch the UID of an email.

        Args:
            email_id (bytes): The ID of the email.

        Returns:
            Optional[str]: The UID of the email if found, None otherwise.
        """
        try:
            _, uid_string = self.email_connection.fetch(email_id, "UID")
            uid_str = [str(x, encoding="utf-8") for x in uid_string]
            uid_res = re.search(r"\((UID.*?)\)", uid_str[0])
            return uid_res[1].replace("UID", "") if uid_res else None
        except Exception as e:
            logger.error(f"Error fetching UID for email ID {email_id}: {e}")
            return None

    def load_target_emails(self) -> List[str]:
        """
        Load target email addresses from a file specified in the configuration.

        Returns:
            List[str]: A list of target email addresses.
        """
        target_emails_file = self.config.get("target_emails_file")
        target_emails_file = f"{PythonProject().root}/{target_emails_file}"
        if target_emails_file and Path(target_emails_file).is_file():
            with open(target_emails_file, "r") as file:
                target_emails = file.read().splitlines()
                logger.info(f"Imported {len(target_emails)} emails from {target_emails_file}.")
                return target_emails
        else:
            if not Path(target_emails_file).exists():
                logger.error(f"ERROR: {target_emails_file} not found.")
            logger.info("No target emails file specified or file does not exist. Using provided email list.")
            return []

    @staticmethod
    def validate_input_email(email_address: str) -> bool:
        """
        Validate the format of an email address.

        Args:
            email_address (str): The email address to validate.

        Returns:
            bool: True if the email address is valid, False otherwise.
        """
        if re.match(r"[^@]+@[^@]+\.[^@]+", email_address):
            return True
        else:
            logger.warning(f"Invalid email format: {email_address}")
            return False

    @staticmethod
    def import_emails_from_file(filename: str) -> List[str]:
        """
        Import email addresses from a file.

        Args:
            filename (str): The path to the file containing email addresses.

        Returns:
            List[str]: A list of email addresses imported from the file.
        """
        if Path(filename).is_file():
            with open(filename, "r") as file:
                emails = file.read().splitlines()
                logger.info(f"Imported {len(emails)} emails from {filename}.")
                return emails
        else:
            logger.error(f"The file {filename} doesn't exist.")
            return []

    def is_mail_app_running(self) -> bool:
        """
        Check if the default mail app is running on the current operating system.

        Returns:
            bool: True if the mail app is running, False otherwise.

        Raises:
            NotImplementedError: If the current operating system is not supported.
        """
        os_name = platform.system().lower()

        if os_name == "darwin":  # macOS
            try:
                script = 'tell application "System Events" to (name of processes) contains "Mail"'
                result = subprocess.run(["osascript", "-e", script], capture_output=True, text=True, check=True)
                return "true" in result.stdout.lower()
            except subprocess.CalledProcessError as e:
                logger.error(f"Error checking if Mail app is running on macOS: {e}")
                return False
        elif os_name == "windows":
            try:
                result = subprocess.run(
                    ["tasklist", "/FI", "IMAGENAME eq outlook.exe"], capture_output=True, text=True, check=True
                )
                return "outlook.exe" in result.stdout.lower()
            except subprocess.CalledProcessError as e:
                logger.error(f"Error checking if Outlook is running on Windows: {e}")
                return False
        elif os_name == "linux":
            # This is a basic check and may need to be adjusted based on the specific Linux mail client
            try:
                result = subprocess.run(
                    ["pgrep", "-f", "thunderbird|evolution|geary"], capture_output=True, text=True, check=True
                )
                return bool(result.stdout.strip())
            except subprocess.CalledProcessError as e:
                logger.error(f"Error checking if mail app is running on Linux: {e}")
                return False
        else:
            raise NotImplementedError(f"Checking mail app status is not implemented for {os_name}")

    def close_mail_app(self) -> None:
        """
        Close the Apple Mail app if it's running.
        """
        if self.is_mail_app_running():
            try:
                script = 'tell application "Mail" to quit'
                subprocess.run(["osascript", "-e", script], capture_output=True)
                logger.info("Mail app closed successfully.")
            except Exception as e:
                logger.error(f"Error closing Mail app: {e}")
