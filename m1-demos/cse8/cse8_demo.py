from pathlib import Path
from email.message import EmailMessage
from docx import Document
from playwright.sync_api import sync_playwright

out = Path(__file__).parent / "output"
out.mkdir(exist_ok=True)

plan = {
    "course": "CSE 4101",
    "work": "Milestone 1",
    "due": "Sep 28",
    "progress": "40%",
    "xp": "120",
    "game": "2 wins",
}
shared = {k: plan[k] for k in ("course", "work", "due")}
lines = ["Folio Plan"] + [f"{k.title()}: {v}" for k, v in shared.items()]
text = "\n".join(lines)

with sync_playwright() as p:
    browser = p.chromium.launch()
    page = browser.new_page()
    page.set_content("<br>".join(lines))
    page.pdf(path=out / "sample-plan.pdf", format="Letter")
    browser.close()

doc = Document()
for line in lines:
    doc.add_paragraph(line)
doc.save(out / "sample-plan.docx")

msg = EmailMessage()
msg["To"] = "instructor@example.edu"
msg["Subject"] = "Folio plan"
msg.set_content("Please review my plan:\n\n" + text)
(out / "email-preview.txt").write_text(str(msg))

assert not {"progress", "xp", "game"} & shared.keys()
print("Made PDF, DOCX, email preview. Privacy check: PASS")
