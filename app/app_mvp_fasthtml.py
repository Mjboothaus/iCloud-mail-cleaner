
from icloud_mail_cleaner.icloud_mail_cleaner import ICloudCleaner

from fasthtml.common import *

app, rt = fast_app(debug=True)

cleaner = ICloudCleaner('config.ini', mode='app')

def email_form():
    return Form(
        Input(type="email", name="username", placeholder="iCloud Email"),
        Input(type="password", name="password", placeholder="Password"),
        Input(type="text", name="target_emails", placeholder="Target emails (comma-separated)"),
        Button("Clean Emails", type="submit"),
        action="/clean", method="POST"
    )

def results_table(results):
    return Table(
        *[Tr(Td(email), Td(str(count))) for email, count in results]
    ) + P(f"Total emails deleted: {sum(count for _, count in results)}")

@rt("/")
def get():
    return Titled("iCloud Email Cleaner", 
        email_form(),
        Div(id="results")
    )

@rt("/clean")
def post(request):
    form_data = request.form
    username = form_data.get('username')
    password = form_data.get('password')
    target_emails = form_data.get('target_emails', '').split(',')

    if not all([username, password, target_emails]):
        return P("Please fill in all fields.")

    try:
        cleaner.connect(username, password, cleaner.config['imap_server'], int(cleaner.config['imap_port']))
        
        results = []
        for email in target_emails:
            count = cleaner.clean_mailbox(target_emails=[email.strip()])
            results.append((email.strip(), count))

        cleaner.close_connection()

        return results_table(results)
    except Exception as e:
        return P(f"An error occurred: {str(e)}")

serve()