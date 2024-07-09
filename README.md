## iCloud email cleaning tool

A simple tool to batch delete all incoming iCloud emails from a list of specified senders. Especially useful if you subscribe to a bunch of newsletters and don't bother to delete the emails day by day.

**WARNING:** *The emails deleted with this tool will be gone forever. Use this tool carefully!*

#### Requirements

- iCloud account with two-factor authentication enabled

#### Installation

- Clone the repo
- Install python and the dependencies see `pyproject.toml`

#### Usage

1. To use the tool you have to create a configuration file named `config.ini`. You can use the provided `config.example.ini` file as a template in which you have to replace `your_icloud_username` with your iCloud email without the `@icloud.com` part. If for some reasons the tool throws an `AUTHENTICATIONFAILED` error try to replace this variable with the full email address as stated [here](https://support.apple.com/en-us/HT202304). 

2. You also have to replace `your_app_specific_passsord` with an app specific password generated in your [Apple ID setting page](https://appleid.apple.com/) under the app-specific password subsection.

3. Specify a list of email addresses to delete emails for in `data/target_email_address.txt` (one per line).

4. After you finished setting up the configuration file in order to use the tool you just have to run
```{bash}
 python src/icloud-mail-clean.py
 ```

----

### Original README

See `README_original.md`.