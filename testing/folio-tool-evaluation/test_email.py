from email.message import EmailMessage
from email.parser import BytesParser


VALID_MESSAGE = {
   "from": "folio@example.edu",
   "to": "student@example.edu",
   "subject": "Folio assignment reminder",
   "plain_body": "Your Design Review assignment is due on 2026-09-30.",
   "html_body": "<p>Your <strong>Design Review</strong> assignment is due on 2026-09-30.</p>",
}


def build_email_message(message):
   email = EmailMessage()
   email["From"] = message["from"]
   email["To"] = message["to"]
   email["Subject"] = message["subject"]
   email.set_content(message["plain_body"])
   if message.get("html_body"):
      email.add_alternative(message["html_body"], subtype="html")
   return email


def validate_message(email):
   assert email["From"] == VALID_MESSAGE["from"]
   assert email["To"] == VALID_MESSAGE["to"]
   assert email["Subject"] == VALID_MESSAGE["subject"]
   assert "Design Review" in email.get_body(preferencelist=("plain",)).get_content()
   assert "2026-09-30" in email.get_body(preferencelist=("html",)).get_content()
   return True


def test_email_message_construction():
   email = build_email_message(VALID_MESSAGE)
   assert validate_message(email)


def test_email_message_with_attachment():
   email = EmailMessage()
   email["From"] = VALID_MESSAGE["from"]
   email["To"] = VALID_MESSAGE["to"]
   email["Subject"] = "Folio report"
   email.set_content("Attached report")
   email.add_attachment(b"PDF bytes", maintype="application", subtype="pdf", filename="folio-report.pdf")
   assert email.get_filename() is None
   assert email.get_payload()[1].get_filename() == "folio-report.pdf"


def test_email_required_fields_validation():
   email = EmailMessage()
   invalid = []
   if not email.get("From"):
      invalid.append("From")
   if not email.get("To"):
      invalid.append("To")
   if not email.get("Subject"):
      invalid.append("Subject")
   assert invalid == ["From", "To", "Subject"]
