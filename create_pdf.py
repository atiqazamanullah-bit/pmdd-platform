from fpdf import FPDF
import re

class PDF(FPDF):
    def header(self):
        self.set_font("helvetica", "B", 15)
        self.cell(0, 10, "PMDD Scientific Analysis Report", border=False, ln=1, align="C")
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font("helvetica", "I", 8)
        self.cell(0, 10, f"Page {self.page_no()}", align="C")

def markdown_to_pdf(md_path, pdf_path):
    pdf = PDF()
    pdf.add_page()
    pdf.set_auto_page_break(auto=True, margin=15)
    
    with open(md_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()

    for line in lines:
        line = line.strip()
        if not line:
            pdf.ln(5)
            continue
            
        # simple bold strip
        line = re.sub(r'\*\*(.*?)\*\*', r'\1', line)
        
        if line.startswith("# "):
            pdf.set_font("helvetica", "B", 18)
            pdf.multi_cell(0, 10, line[2:].replace('*', ''))
        elif line.startswith("## "):
            pdf.set_font("helvetica", "B", 14)
            pdf.multi_cell(0, 8, line[3:].replace('*', ''))
        elif line.startswith("### "):
            pdf.set_font("helvetica", "B", 12)
            pdf.multi_cell(0, 6, line[4:].replace('*', ''))
        elif line.startswith("- "):
            pdf.set_font("helvetica", size=11)
            pdf.multi_cell(0, 6, f"* {line[2:]}")
        elif line.startswith("---"):
            pdf.ln(2)
        else:
            pdf.set_font("helvetica", size=11)
            pdf.multi_cell(0, 6, line)

    pdf.output(pdf_path)
    print(f"PDF generated at {pdf_path}")

if __name__ == "__main__":
    markdown_to_pdf("report_design.md", "PMDD_Scientific_Analysis_Report_Design.pdf")
