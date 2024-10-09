import pytest
from unittest.mock import Mock, patch
from pathlib import Path
from src.icloud_mail_cleaner.icloud_mail_cleaner import ICloudCleaner

@pytest.fixture
def config_file(tmp_path):
    config = tmp_path / "test_config.ini"
    config.write_text("""
    [DEFAULT]
    imap_server = imap.mail.me.com
    imap_port = 993
    [Logging]
    log_file = test.log
    """)
    return str(config)

@pytest.fixture
def mock_imap():
    with patch('imaplib.IMAP4_SSL') as mock_imap:
        yield mock_imap

@pytest.fixture
def cleaner(config_file, mock_imap):
    with patch.dict('os.environ', {'ICLOUD_USERNAME': 'test@icloud.com', 'ICLOUD_PASSWORD': 'password'}):
        return ICloudCleaner(config_file, mode="script", log_level="ERROR")

def test_init(cleaner):
    assert cleaner.config['imap_server'] == 'imap.mail.me.com'
    assert cleaner.config['imap_port'] == '993'

def test_validate_input_email():
    assert ICloudCleaner.validate_input_email("valid@email.com") is True
    assert ICloudCleaner.validate_input_email("invalid-email") is False

def test_connect(cleaner, mock_imap):
    cleaner.connect("test@icloud.com", "password", "imap.mail.me.com", 993)
    mock_imap.return_value.login.assert_called_once_with("test@icloud.com", "password")
    mock_imap.return_value.select.assert_called_once_with("INBOX")

def test_search_emails(cleaner, mock_imap):
    mock_imap.return_value.search.return_value = (None, [b'1 2 3'])
    emails = cleaner.search_emails("sender@example.com")
    assert emails == [b'1', b'2', b'3']
    mock_imap.return_value.search.assert_called_once_with(None, '(FROM "sender@example.com")')

def test_set_deleted(cleaner, mock_imap):
    cleaner.set_deleted("123")
    mock_imap.return_value.uid.assert_called_once_with("STORE", b"123", "+FLAGS", "(\\Deleted)")

def test_fetch_uid(cleaner, mock_imap):
    mock_imap.return_value.fetch.return_value = (None, [b'(UID 123)'])
    uid = cleaner.fetch_uid(b'1')
    assert uid == '123'
    mock_imap.return_value.fetch.assert_called_once_with(b'1', "UID")

@pytest.mark.parametrize("file_content,expected", [
    ("email1@example.com\nemail2@example.com", ["email1@example.com", "email2@example.com"]),
    ("", [])
])

def test_import_emails_from_file(tmp_path, file_content, expected):
    test_file = tmp_path / "test_emails.txt"
    test_file.write_text(file_content)
    result = ICloudCleaner.import_emails_from_file(str(test_file))
    assert result == expected

@patch('subprocess.run')
def test_is_mail_app_running(mock_run, cleaner):
    mock_run.return_value.stdout = "true"
    assert cleaner.is_mail_app_running() is True
    mock_run.return_value.stdout = "false"
    assert cleaner.is_mail_app_running() is False

@patch('subprocess.run')
def test_close_mail_app(mock_run, cleaner):
    with patch.object(cleaner, 'is_mail_app_running', return_value=True):
        cleaner.close_mail_app()
        mock_run.assert_called_once()

def test_load_target_emails(cleaner, tmp_path):
    test_file = tmp_path / "target_emails.txt"
    test_file.write_text("email1@example.com\nemail2@example.com")
    cleaner.config['target_emails_file'] = str(test_file)
    
    with patch('icloud_cleaner.PythonProject') as mock_project:
        mock_project.return_value.root = str(tmp_path)
        result = cleaner.load_target_emails()
    
    assert result == ["email1@example.com", "email2@example.com"]