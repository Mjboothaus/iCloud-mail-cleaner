
1. Test Initialization and Configuration Loading:
- Verify that the ICloudCleaner object initializes correctly with a given configuration file.
- Check if the password is prompted when not provided in the configuration.

2. Test IMAP Connection:
- Test _connect method to ensure it handles successful and failed connections.
- Mock the `imaplib.IMAP4_SSL` object to simulate server responses.

3. Test Email Searching:
- Test search_emails method with a known sender to check if it returns the correct email IDs.
- Simulate a case where the search should return no results.

4. Test Email Deletion:
- Test set_deleted method to ensure it marks emails for deletion correctly.
- Check how it handles an invalid UID.

5. Test UID Fetching:
- Test fetch_uid method with a known email ID to ensure it extracts the correct UID.
- Simulate a case where the UID cannot be found or an error occurs.

6. Test Mailbox Cleaning:
- Test clean_mailbox method with a list of target emails to ensure it deletes the correct emails.
- Check the behavior when no target emails are provided or when an error occurs during the process.

7. Test Connection Closure:
- Test close_connection method to ensure it closes the IMAP connection properly.
- Simulate a case where the connection cannot be closed or an error occurs.

8. Test Email Validation:
- Test validate_input_email with valid and invalid email formats.

9. Test Mail App Interaction:
- Test is_mail_app_running to check if it correctly identifies the running state of the Mail app.
- Test close_mail_app to ensure it closes the Mail app when it's running.
