"""
Fake company ki Digital Lending Policy — sample data (Impact Agent + upload
feature demo ke liye).

Deliberately purani hai (2023 tak ke circulars se likhi hai) — 2025 Directions
ke naye requirements (cooling-off period, CIMS reporting, multi-lender LSP
display, stricter data-repatriation timeline) isme MISSING hain jaan-boojhkar.
Yehi genuine gaps hain jo Impact Agent (Phase 5) ko dhoondhne hain.
"""

from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import cm
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, PageBreak,
)

OUT_PATH = "FinTrust_Digital_Lending_Policy_v2.1.pdf"

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="PolicyTitle", fontSize=18, leading=22, spaceAfter=6, textColor=colors.HexColor("#1a2b4a")))
styles.add(ParagraphStyle(name="PolicySubtitle", fontSize=10, textColor=colors.grey, spaceAfter=20))
styles.add(ParagraphStyle(name="SectionHeading", fontSize=13, leading=16, spaceBefore=16, spaceAfter=6, textColor=colors.HexColor("#1a2b4a")))
styles.add(ParagraphStyle(name="ClauseNo", fontSize=10.5, leading=15, spaceAfter=4))
styles.add(ParagraphStyle(name="BodyText2", fontSize=10.5, leading=15, spaceAfter=8))

story = []

story.append(Paragraph("FinTrust Consumer Finance Limited", styles["PolicyTitle"]))
story.append(Paragraph(
    "Board-Approved Policy on Digital Lending &amp; Lending Service Provider (LSP) Arrangements"
    "<br/>Policy Version: 2.1&nbsp;&nbsp;|&nbsp;&nbsp;Effective Date: October 15, 2023"
    "&nbsp;&nbsp;|&nbsp;&nbsp;Next Scheduled Review: October 2025"
    "<br/>Classification: Internal &mdash; Compliance &amp; Risk Management",
    styles["PolicySubtitle"],
))

sections = [
    ("1. Purpose and Scope",
     "This Policy sets out FinTrust Consumer Finance Limited's ('the Company') framework for "
     "digital lending operations conducted directly or through Lending Service Providers (LSPs) "
     "and Digital Lending Apps (DLAs), in line with RBI circular RBI/2022-23/111 dated September 2, "
     "2022 (Guidelines on Digital Lending) and related instructions. This Policy applies to all "
     "digital lending products sourced, disbursed, or serviced by the Company."),

    ("2. Definitions",
     "For the purposes of this Policy: 'Digital Lending' means a remote and automated lending "
     "process using digital technologies for customer acquisition, credit assessment, loan "
     "approval, disbursement, recovery, and associated customer service. 'LSP' means an agent of "
     "the Company carrying out one or more of the lender's functions in customer acquisition, "
     "underwriting support, or loan recovery, in conformity with extant outsourcing guidelines."),

    ("3. Due Diligence on Lending Service Providers",
     "The Company shall conduct enhanced due diligence on every LSP prior to onboarding, covering "
     "technical capability, data privacy standards, fair-practice conduct, and financial soundness. "
     "LSP arrangements shall be governed by a Board-approved contractual agreement clearly defining "
     "roles, responsibilities, and grievance-handling obligations. The Company remains fully liable "
     "for the acts and omissions of its LSPs, consistent with extant outsourcing guidelines."),

    ("4. Borrower Onboarding and Creditworthiness Assessment",
     "Prior to sanctioning any digital loan, the Company shall collect and record the borrower's "
     "economic profile (age, occupation, and income) to assess creditworthiness, and shall maintain "
     "such records for audit purposes. Automatic enhancement of a borrower's credit limit shall not "
     "be undertaken without the borrower's explicit, recorded consent."),

    ("5. Disclosures to Borrowers",
     "The Company shall furnish a Key Fact Statement (KFS) to every borrower prior to loan execution, "
     "in the format prescribed by RBI. The Company's website shall list all digital lending products "
     "and associated DLAs, particulars of engaged LSPs, and grievance-redressal contact details, in "
     "conformity with RBI/2022-23/111 dated September 2, 2022."),

    ("6. Loan Disbursal and Servicing",
     "All loan disbursals shall be made directly into the borrower's bank account, without pass-through "
     "of funds via any LSP or third-party account, except where a co-lending arrangement or statutory "
     "mandate requires otherwise. Repayments shall similarly flow directly to the Company's account. "
     "LSP fees shall be borne by the Company and shall not be charged to the borrower."),

    ("7. Data Collection, Storage, and Privacy",
     "Data collection from borrowers shall be need-based and undertaken only with explicit, recorded "
     "consent. LSPs shall store only such borrower data as is minimally necessary for their engagement "
     "scope. The Company shall make reasonable efforts to ensure borrower data is stored within India "
     "and shall maintain a comprehensive, publicly accessible privacy policy."),

    ("8. Grievance Redressal",
     "The Company shall designate a nodal Grievance Redressal Officer for digital lending complaints. "
     "Contact details shall be prominently displayed on the Company's website and within the KFS. "
     "The Company shall endeavour to resolve borrower grievances within a reasonable timeframe."),

    ("9. Default Loss Guarantee (DLG) Arrangements",
     "Where the Company enters into a Default Loss Guarantee arrangement with an LSP, in conformity "
     "with RBI circular RBI/2023-24/41 dated June 8, 2023, the aggregate DLG cover on any specified "
     "loan portfolio shall not exceed 5% of the amount disbursed under that portfolio at any point in "
     "time. DLG shall not be treated as a substitute for the Company's own credit appraisal, and DLG "
     "shall be invoked no later than 120 days past due on the underlying loan."),

    ("10. Technology and Cybersecurity Standards",
     "All digital lending platforms and LSP-operated DLAs shall comply with the Company's information "
     "security standards and applicable RBI cybersecurity guidance in force at the time of deployment."),

    ("11. Policy Review",
     "This Policy shall be placed before the Board for review on a periodic basis, and earlier if "
     "warranted by material changes in the applicable regulatory framework."),
]

for heading, body in sections:
    story.append(Paragraph(heading, styles["SectionHeading"]))
    story.append(Paragraph(body, styles["BodyText2"]))

story.append(PageBreak())
story.append(Paragraph("Annex A: Regulatory References Underlying This Policy", styles["SectionHeading"]))
ref_data = [
    ["Reference", "Date", "Subject"],
    ["RBI/2019-20/258", "June 24, 2020", "Loans Sourced over Digital Lending Platforms"],
    ["RBI/2022-23/111", "Sep 2, 2022", "Guidelines on Digital Lending"],
    ["RBI/2023-24/41", "Jun 8, 2023", "Guidelines on Default Loss Guarantee (DLG)"],
]
table = Table(ref_data, colWidths=[4.5 * cm, 3 * cm, 8.5 * cm])
table.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1a2b4a")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 9.5),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f2f4f8")]),
    ("TOPPADDING", (0, 0), (-1, -1), 6),
    ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
]))
story.append(Spacer(1, 8))
story.append(table)

doc = SimpleDocTemplate(
    OUT_PATH, pagesize=A4,
    leftMargin=2.2 * cm, rightMargin=2.2 * cm, topMargin=2 * cm, bottomMargin=2 * cm,
)
doc.build(story)
print(f"Wrote {OUT_PATH}")
