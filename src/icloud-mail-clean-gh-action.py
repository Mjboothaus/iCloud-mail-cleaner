from pathlib import Path
from icloud_mail_cleaner.icloud_mail_cleaner import ICloudCleaner
from loguru import logger

CONFIG_FILE = Path.cwd() / "config.ini"
assert CONFIG_FILE.exists()

# `target_emails_file` is defined within `config.ini`

cleaner = ICloudCleaner(str(CONFIG_FILE), mode="script", log_level="WARNING")
total_emails_deleted = cleaner.clean_mailbox(close_mail_app=False)
logger.info(f"Total emails deleted: {total_emails_deleted}")
print(f"Total emails deleted: {total_emails_deleted}")
