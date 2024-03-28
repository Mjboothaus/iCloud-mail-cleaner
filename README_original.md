TODO: Create updated README



### Requirements

See `pyproject.toml`




----

## Original README

### iCloud email cleaning tool

A simple tool to batch delete all incoming emails from a sender. Especially useful if you subscribe to a bunch of newsletters and don't bother to delete the emails day by day

**WARNING:** the emails deleted with this tool will be gone forever. Use this tool carefully!

#### Requirements

- python 2.7
- pip
- an iCloud account with two-factor authentication enabled

#### Installation

Run `sh install.sh` in the program directory and you're done

#### Usage

To use the tool you have to create a configuration file named `config.ini`. You can use the provided `config.example.ini` file as a template in which you have to replace `your_icloud_username` with your iCloud email without the `@icloud.com` part. If for some reasons the tool throws an `AUTHENTICATIONFAILED` error try to replace this variable with the full email address as stated [here](https://support.apple.com/en-us/HT202304). You also have to replace `your_app_specific_passsord` with an app specific password generated in your [Apple ID setting page](https://appleid.apple.com/) under the app specific password subsection.

After you finished setting up the configuration file in order to use the tool you just have to run `python icloud_cleaner.py --email [target_email_address]` in the script directory. If you want to batch process a list of emails create a text file with the target emails (one email per line) and run `python icloud_cleaner.py --file [filename]`