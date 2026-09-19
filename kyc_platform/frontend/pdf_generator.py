from fpdf import FPDF
import io
import textwrap

class KYCReportPDF(FPDF):
    def header(self):
        self.set_font('helvetica', 'B', 15)
        self.cell(0, 10, 'DN Agentic KYC Intelligence Platform', 0, 1, 'C')
        self.set_font('helvetica', '', 10)
        self.cell(0, 10, 'Automated Due Diligence Evidence Report', 0, 1, 'C')
        self.ln(5)

    def footer(self):
        self.set_y(-15)
        self.set_font('helvetica', 'I', 8)
        self.cell(0, 10, f'Page {self.page_no()}', 0, 0, 'C')

def generate_kyc_pdf_report(customer_id: str, report: dict) -> bytes:
    pdf = KYCReportPDF()
    pdf.add_page()
    
    decision = report.get("decision", "UNKNOWN")
    score = report.get("overall_risk_score", 0)
    band = report.get("risk_band", "UNKNOWN")
    rationale = report.get("decision_rationale", "No rationale provided.")
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, f"Customer ID: {customer_id}", 0, 1)
    pdf.cell(0, 8, f"Final AI Decision: {decision}", 0, 1)
    pdf.cell(0, 8, f"Risk Score: {score}/100", 0, 1)
    pdf.cell(0, 8, f"Risk Band: {band}", 0, 1)
    pdf.ln(5)
    
    pdf.set_font("helvetica", "B", 12)
    pdf.cell(0, 8, "AI Decision Rationale:", 0, 1)
    pdf.set_font("helvetica", "", 10)
    
    # Strip unsupported unicode chars
    def _clean(t):
        s = str(t).replace('—', '-').replace('–', '-').replace('’', "'").replace('“', '"').replace('”', '"')
        s = s.replace('\t', '    ')
        return s.encode('ascii', 'ignore').decode('ascii')
        
    pdf.write(6, _clean(rationale))
    pdf.ln(8)
    
    flags = report.get("flags", [])
    if flags:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Risk Flags Raised:", 0, 1)
        pdf.set_font("helvetica", "", 10)
        for flag in flags:
            pdf.cell(0, 6, f"- {_clean(flag)}", 0, 1)
        pdf.ln(5)
        
    evidence_trail = report.get("evidence_trail", [])
    if evidence_trail:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Evidence Trail:", 0, 1)
        pdf.set_font("helvetica", "", 10)
        for ev in evidence_trail:
            impact = ev.get("impact", "NEUTRAL")
            agent = ev.get("agent", "Unknown Agent")
            finding = ev.get("finding", "No finding")
            txt = f"[{impact}] {agent}: {finding}"
            pdf.write(6, _clean(txt))
            pdf.ln(8)
        
    actions = report.get("recommended_actions", [])
    if actions:
        pdf.set_font("helvetica", "B", 12)
        pdf.cell(0, 8, "Recommended Actions:", 0, 1)
        pdf.set_font("helvetica", "", 10)
        for act in actions:
            pdf.write(6, f"- {_clean(act)}")
            pdf.ln(8)
            
    # return binary bytes
    return bytes(pdf.output())
