# test_icloud_mail_cleaner.py
import pytest
from src.icloud_mail_cleaner import ICloudCleaner

@pytest.fixture
def mock_imap(mocker):
    imap_class = mocker.patch('icloud_mail_cleaner.imaplib.IMAP4_SSL')
    imap_instance = imap_class.return_value
    imap_instance.search.return_value = ('OK', [b'1 2 3'])
    imap_instance.login.return_value = ('OK', [])
    imap_instance.select.return_value = ('OK', [])
    return imap_instance

@pytest.fixture
def cleaner(mock_imap, mocker):
    mocker.patch('icloud_mail_cleaner.ConfigObj', return_value={
        'imap_server': 'mockserver',
        'imap_port': '993',
        'username': 'mockuser',
        'password': 'mockpassword',
        'target_emails_file': 'mockfile'
    })
    mocker.patch('icloud_mail_cleaner.getpass', return_value='mockpassword')
    return ICloudCleaner('path/to/mock/config.ini')

def test_search_emails(cleaner, mock_imap):
    sender = 'test@example.com'
    result = cleaner.search_emails(sender)
    assert result == [b'1', b'2', b'3']
    mock_imap.search.assert_called_with(None, f'(FROM "{sender}")')

def test_set_deleted(cleaner, mock_imap):
    email_uid = '123'
    cleaner.set_deleted(email_uid)
    mock_imap.uid.assert_called_with("STORE", b'123', "+FLAGS", "(\\Deleted)")

def test_fetch_uid(cleaner, mock_imap):
    email_id = '1'
    mock_imap.fetch.return_value = ('OK', [b'1 (UID 123)'])
    uid = cleaner.fetch_uid(email_id)
    assert uid == '123'
    mock_imap.fetch.assert_called_with('1', 'UID')

def test_validate_input_email():
    valid_email = 'test@example.com'
    invalid_email = 'not-an-email'
    assert ICloudCleaner.validate_input_email(valid_email) is True
    assert ICloudCleaner.validate_input_email(invalid_email) is False

# Additional tests can be added following the same pattern