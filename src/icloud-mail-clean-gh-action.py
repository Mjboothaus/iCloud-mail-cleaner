from pathlib import Path
from icloud_mail_cleaner.icloud_mail_cleaner import ICloudCleaner
from loguru import logger

CONFIG_FILE = Path.cwd() / "config.ini"
assert CONFIG_FILE.exists()

# `target_emails_file` is defined within `config.ini`

cleaner = ICloudCleaner(str(CONFIG_FILE), mode="script", log_level="WARNING")
deletion_results = cleaner.clean_mailbox(close_mail_app=True)
total_deletions = sum(count for _, count in deletion_results)
logger.info(f"Total emails deleted: {total_deletions}")
print(f"Total emails deleted: {total_deletions}")
