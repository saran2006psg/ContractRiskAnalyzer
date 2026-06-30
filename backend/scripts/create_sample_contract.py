import os
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer

def create_sample_contract(filename="sample_employment_contract.pdf"):
    doc = SimpleDocTemplate(filename, pagesize=letter,
                            rightMargin=72, leftMargin=72,
                            topMargin=72, bottomMargin=72)
    styles = getSampleStyleSheet()
    
    # Custom styles
    title_style = ParagraphStyle(
        'ContractTitle',
        parent=styles['Heading1'],
        fontSize=18,
        leading=22,
        alignment=1, # Center
        spaceAfter=20
    )
    
    section_style = ParagraphStyle(
        'ContractSection',
        parent=styles['Heading2'],
        fontSize=12,
        leading=14,
        spaceBefore=10,
        spaceAfter=6
    )
    
    body_style = ParagraphStyle(
        'ContractBody',
        parent=styles['Normal'],
        fontSize=10,
        leading=14,
        spaceAfter=10
    )
    
    story = []
    
    # Title
    story.append(Paragraph("EMPLOYMENT AGREEMENT", title_style))
    story.append(Spacer(1, 12))
    
    # Preamble
    preamble = (
        "This Employment Agreement (the \"Agreement\") is entered into as of July 1, 2026, "
        "by and between Acme Corporation, a Delaware corporation (the \"Company\"), and "
        "John Doe, an individual residing in California (the \"Employee\")."
    )
    story.append(Paragraph(preamble, body_style))
    
    # Section 1: Position and Duties
    story.append(Paragraph("1. Position and Duties", section_style))
    p1 = (
        "The Employee shall serve in the position of Senior Software Engineer. The Employee "
        "shall perform all duties and responsibilities standard for this position, and such "
        "other duties as may be assigned by the Company from time to time."
    )
    story.append(Paragraph(p1, body_style))
    
    # Section 2: Compensation
    story.append(Paragraph("2. Compensation", section_style))
    p2 = (
        "The Company shall pay the Employee a base salary at the annual rate of $120,000, "
        "payable in accordance with the Company's standard payroll practices. The Employee "
        "shall also be eligible to participate in the Company's employee benefit plans."
    )
    story.append(Paragraph(p2, body_style))
    
    # Section 3: Termination (HIGH RISK CLAUSE)
    story.append(Paragraph("3. Termination", section_style))
    p3 = (
        "The Company may terminate the Employee's employment at any time, for any reason or "
        "no reason, immediately upon written notice, without any obligation to pay severance, "
        "accrued PTO, or any other compensation. The Employee may terminate their employment "
        "only upon providing the Company with ninety (90) days' prior written notice."
    )
    story.append(Paragraph(p3, body_style))
    
    # Section 4: Non-Compete and Non-Solicitation (HIGH RISK CLAUSE)
    story.append(Paragraph("4. Restrictive Covenants", section_style))
    p4 = (
        "During the term of employment and for a period of five (5) years following the "
        "termination of employment for any reason, the Employee shall not, directly or indirectly, "
        "engage in, consult for, perform services for, or own any interest in any business, "
        "entity, or venture that competes with the Company, its parents, or affiliates, anywhere "
        "in the world. The Employee shall also not solicit any clients or employees of the Company "
        "during this five-year period."
    )
    story.append(Paragraph(p4, body_style))
    
    # Section 5: Intellectual Property (HIGH RISK CLAUSE)
    story.append(Paragraph("5. Intellectual Property and Inventions", section_style))
    p5 = (
        "The Employee agrees that all ideas, inventions, discoveries, designs, computer programs, "
        "and developments (whether or not patentable or copyrightable) made, conceived, or "
        "developed by the Employee during or outside of working hours, whether using Company "
        "resources or their own personal resources, and whether or not related to the Company's "
        "current or anticipated business, shall be the sole and exclusive property of the Company."
    )
    story.append(Paragraph(p5, body_style))
    
    # Section 6: Indemnification (HIGH RISK CLAUSE)
    story.append(Paragraph("6. Indemnification", section_style))
    p6 = (
        "The Employee agrees to indemnify, defend, and hold harmless the Company, its directors, "
        "officers, and employees from and against any and all claims, liabilities, damages, "
        "losses, or expenses (including attorney's fees) arising out of or in connection with "
        "the Employee's employment, including any claims resulting from the Company's own "
        "negligent acts or omissions."
    )
    story.append(Paragraph(p6, body_style))
    
    # Section 7: Governing Law
    story.append(Paragraph("7. Governing Law", section_style))
    p7 = (
        "This Agreement shall be governed by, and construed in accordance with, the laws of "
        "the State of Delaware, without regard to its conflict of laws principles. Any legal "
        "action arising under this Agreement shall be brought exclusively in the state or "
        "federal courts located in Delaware."
    )
    story.append(Paragraph(p7, body_style))
    
    # Signatures
    story.append(Spacer(1, 20))
    sig_text = (
        "IN WITNESS WHEREOF, the parties have executed this Employment Agreement as of "
        "the date first written above.<br/><br/>"
        "ACME CORPORATION:<br/>"
        "By: ___________________________<br/>"
        "Title: Chief Executive Officer<br/><br/>"
        "EMPLOYEE:<br/>"
        "By: ___________________________<br/>"
        "John Doe"
    )
    story.append(Paragraph(sig_text, body_style))
    
    doc.build(story)
    print(f"Successfully generated sample contract at: {os.path.abspath(filename)}")

if __name__ == "__main__":
    create_sample_contract()
