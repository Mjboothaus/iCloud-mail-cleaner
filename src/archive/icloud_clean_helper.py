
import argparse
import imaplib
import logging
import os.path
import re
import sys

from configobj import ConfigObj

from tqdm.notebook import tqdm, trange

def progress_bar(n_delete: int, email_address: str) -> None:
    """
    Progress bar.

    Args:
        n_delete: An integer representing the number of iterations for the progress bar (number of emails to delete in this instance).

    Returns:
        None
    """
    for i in trange(n_delete, desc=email_address):
    return None


def connect(config, mailbox="inbox"):
    """
    Establishes a secure connection to an IMAP server and logs in to a specific mailbox.

    Args:
        config (dict): A dictionary containing the configuration details for the IMAP server, including the server address, port, username, and password.
        mailbox (str, optional): The name of the mailbox to select after connecting. The default value is "inbox".

    Returns:
        email_connection (IMAP4_SSL object): The established connection to the IMAP server, or None if the connection or login fails.
    """
    email_connection = None
    try:
        email_connection = imaplib.IMAP4_SSL(config["imap_server"], config["imap_port"])
        email_connection.login(config["username"], config["password"])
        email_connection.select(mailbox)
        logging.info(f"Successfully connected to {config['username']}@icloud.com {mailbox}")
        return email_connection
    except Exception as e:
        logging.error(f"Failed to connect or login: {str(e)}")
        return None
    finally:
        if email_connection is not None:
            email_connection.close()


def search_emails(email_connection, sender):
    """
    Search for emails from a specific sender.

    Args:
        email_connection: The connection to the email server.
        sender (str): The email address of the sender.

    Returns:
        list or None: A list of email identifiers if emails are found, None otherwise.
    """
    try:
        _, data = email_connection.search(None, f'(FROM "{sender}")')
        # Split the email identifiers in an array
        mail_ids = data[0]
        if mail_ids is None:
            return None
        return mail_ids.split()
    except Exception as e:
        print(f"An error occurred while searching emails: {str(e)}")
        return None


# Add the deleted flag to an email
def set_deleted(email_connection, email_uid):
    """
    Sets the email with the given UID as deleted.

    Args:
        email_connection: The connection to the email server.
        email_uid: The UID of the email to be deleted.

    Returns:
        True if the deletion was successful, False otherwise.
    """
    try:
        if not isinstance(email_uid, int):
            raise ValueError("email_uid must be an integer")
        email_connection.uid("STORE", bytes(str(email_uid).strip(), 'ascii'), "+FLAGS", "(\\Deleted)")
        return True
    except Exception:
        return False


def fetch_uid(email_connection, email_id):
    """
    Fetches the UID of an email from the email server.

    Args:
        email_connection: The connection to the email server.
        email_id: The ID of the email.

    Returns:
        The UID of the email, or None if it cannot be fetched.
    """
    if email_connection is None or not email_connection.is_open():
        raise ConnectionError("Email connection is not valid or open")

    try:
        _, uid_string = email_connection.fetch(email_id, "UID")
    except imaplib.IMAP4.error:
        raise ConnectionError("Failed to fetch UID")

    uid_str = [str(x, encoding='utf-8') for x in uid_string] if uid_string else []

    uid_res = uid_str[0].split("(UID", 1)
    return uid_res[1].replace(")", "") if len(uid_res) > 1 else None


def parse_args():
    parser = argparse.ArgumentParser(
        description="Delete all incoming emails from a sender email address"
    )
    parser.add_argument("--email", help="The sender whose messages should be deleted")
    parser.add_argument(
        "--file",
        help="A file which contains the target emails. Each email should be on a separate line.",
    )
    return parser.parse_args()


def validate_input_email(email):
    return re.match(r"[^@]+@[^@]+\.[^@]+", email)


def verify_cli_args(args):
    if args.email is None and args.file is None:
        print("You need to specify a target email or a file. Use --help for details")
        sys.exit()


def import_emails_from_file(filename):
    if os.path.isfile(filename):
        return open(filename).read().split("\n")
    else:
        print(f"The file {filename} doesn't exist")

def connect_and_clean(config, target_emails):
    print("Connecting to " + config["username"] + "@icloud.com...")
    email_connection = connect(config)

    while email_connection.check()[0] == "OK":

        total_emails_count = 0
        for target_email in target_emails:
            if not validate_input_email(target_email):
                print(f"The email '{target_email}' is not valid")
                continue

            emails = search_emails(email_connection, target_email)
            if emails is not None:
                emails_count = str(len(emails))
            else:
                emails_count = 0
            total_emails_for_target = int(emails_count)
            total_deleted_emails = 0

            while int(emails_count) > 0:
                print(f"Found {emails_count} email(s) for {target_email}")

                for idx, e in enumerate(emails):
                    # The fetching of the email UID is required
                    # since the email ID may change between operations
                    # as specified by the IMAP standard
                    uid = fetch_uid(email_connection, e)
                    if uid is None:
                        print(
                            f"Email {str(total_deleted_emails + idx + 1)}/{str(total_emails_for_target)} was not valid"
                        )

                    else:
                        #print(
                        #    f"Deleted email {str(total_deleted_emails + idx + 1)}/{str(total_emails_for_target)}"
                        #)
                        set_deleted(email_connection, uid)
                # Confirm the deletion of the messages
                email_connection.expunge()

                print(f"Deleted {emails_count} email(s) for {target_email}")
                print("Checking for remaining emails...")

                # Verify if there are any emails left on the server for
                # the target address. This is required to circumvent the
                # chunking of the search results by iCloud
                emails = search_emails(email_connection, target_email)
                if emails is not None:
                    emails_count = str(len(emails))
                else:
                    emails_count = 0
                total_deleted_emails = total_emails_for_target
                total_emails_for_target += int(emails_count)

            print(
                f"The cleanup for {target_email} was successful. Deleted {str(total_emails_for_target)} email(s)"
            )
            total_emails_count += total_emails_for_target

    print(f"The cleanup was successful. Deleted {str(total_emails_count)} email(s)")

    # Close the mailbox and logout
    email_connection.close()
    email_connection.logout()
    return total_emails_count