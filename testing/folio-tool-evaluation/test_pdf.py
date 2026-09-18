from pathlib import Path

from fpdf import FPDF
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas


REPORT_ROWS = [
   ("Design Review", "CS 491", "High", "2026-09-30"),
   ("Lab 2", "CS 491", "Medium", "2026-10-02"),
   ("Reading", "ENG 210", "Low", "2026-10-01"),
]


def fpdf_candidate(path: Path):
   pdf = FPDF()
   pdf.add_page()
   pdf.set_font("Helvetica", "B", 16)
   pdf.cell(0, 10, "Folio Weekly Report", ln=True)
   pdf.set_font("Helvetica", size=11)
   pdf.cell(0, 8, "Student: Alex Rivera", ln=True)
   pdf.cell(0, 8, "Project: Senior Design", ln=True)
   pdf.ln(4)
   pdf.set_font("Helvetica", "B", 10)
   pdf.cell(50, 8, "Assignment", border=1)
   pdf.cell(35, 8, "Course", border=1)
   pdf.cell(25, 8, "Priority", border=1)
   pdf.cell(30, 8, "Due", border=1, ln=True)
   pdf.set_font("Helvetica", size=10)
   for assignment, course, priority, due in REPORT_ROWS:
      pdf.cell(50, 8, assignment, border=1)
      pdf.cell(35, 8, course, border=1)
      pdf.cell(25, 8, priority, border=1)
      pdf.cell(30, 8, due, border=1, ln=True)
   pdf.output(path)
   assert path.exists() and path.stat().st_size > 0
   return path


def reportlab_candidate(path: Path):
   c = canvas.Canvas(str(path))
   c.setTitle("Folio Weekly Report")
   c.drawString(72, 720, "Folio Weekly Report")
   c.drawString(72, 700, "Student: Alex Rivera")
   c.drawString(72, 686, "Project: Senior Design")
   y = 650
   for idx, (assignment, course, priority, due) in enumerate(REPORT_ROWS):
      c.drawString(72, y, f"{assignment} | {course} | {priority} | {due}")
      y -= 18
   c.save()
   assert path.exists() and path.stat().st_size > 0
   return path


def test_pdf_generation(tmp_path):
   base = tmp_path / "folio_report_fpdf.pdf"
   fpdf_candidate(base)
   lab = tmp_path / "folio_report_reportlab.pdf"
   reportlab_candidate(lab)
   assert base.exists()
   assert lab.exists()


def test_pdf_repeated_generation(tmp_path):
   for idx in range(2):
      path = tmp_path / f"repeat_{idx}.pdf"
      fpdf_candidate(path)
