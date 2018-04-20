import re
import sys
import email
import imaplib
import email.header
import argparse
from email_validator import validate_email, EmailNotValidError

from configobj import ConfigObj

def connect(config):
    email_connection = imaplib.IMAP4_SSL(config['imap_server'], config['imap_port'])
    email_connection.login(config['username'], config['password'])
    email_connection.select('inbox')

    return email_connection

def search_emails(email_connection, sender):
    typ, data = email_connection.search(None, '(FROM "' + sender + '")')
    
    # Split the email identifiers in an array
    mail_ids = data[0]
    return mail_ids.split()

# Add the deleted flag to an email
def set_deleted(email_connection, email_uid):
    email_connection.uid("STORE", int(email_uid), "+FLAGS", "(\\Deleted)")

def fetch_uid(email_connection, email_id):
    status, uid_string = email_connection.fetch(email_id, 'UID')
    uid_res = re.search(r'\((.*?)\)', uid_string[0])
    
    if (uid_res != None):
        return uid_res.group(1).replace('UID', '')
    else:
        return None

def parse_args():
    parser = argparse.ArgumentParser(description='Delete all incoming emails from a sender email address')
    parser.add_argument('sender_email', help='The sender whose messages should be deleted')
    return parser.parse_args()

def validate_input_email(email):
    try:
        v = validate_email(email) # validate and get info
        return v['email'] # replace with normalized form
    except EmailNotValidError as e:
        print('The email \'' + email + '\' is not valid')
        sys.exit()

args = parse_args()
normalized_email = validate_input_email(args.sender_email)

config = ConfigObj('config.ini')
email_connection = connect(config)

emails = search_emails(email_connection, normalized_email)
emails_count = str(len(emails))
print('Found ' + emails_count + ' email(s) for ' + normalized_email)

for idx, e in enumerate(emails):
    # The fetching of the email UID is required
    # since the email ID may change between operations
    # as specified by the IMAP standard
    uid = fetch_uid(email_connection, e)
    if (uid != None):
        set_deleted(email_connection, uid)
    
    print('Deleted email ' + str(idx + 1) + '/' + emails_count)

# Confirm the deletion of the messages
email_connection.expunge()

print('Deleted ' + emails_count + ' email(s) for ' + normalized_email)

# Close the mailbox and logout
email_connection.close()
email_connection.logout()