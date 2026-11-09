"""
Resume Export Service.
Generates ATS-optimized PDF and DOCX files for generated candidate resumes.
Supports 'classic' and 'modern' visual styling in strict single-column layouts.
"""

import os
from typing import Dict, Any, List
from docx import Document
from docx.shared import Pt, Inches, RGBColor
from docx.enum.text import WD_ALIGN_PARAGRAPH

from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, HRFlowable
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors


def export_resume_docx(resume_doc: Dict[str, Any], output_path: str) -> str:
    """
    Exports a resume document to a clean ATS-friendly single-column DOCX.
    Supports template styling ('classic' or 'modern').
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    doc = Document()

    # Set standard 0.6 inch margins for optimal ATS resume density
    sections = doc.sections
    for section in sections:
        section.top_margin = Inches(0.6)
        section.bottom_margin = Inches(0.6)
        section.left_margin = Inches(0.6)
        section.right_margin = Inches(0.6)

    template = resume_doc.get("template", "modern")
    content = resume_doc.get("content", {})
    personal = content.get("personal", {})
    target_role = resume_doc.get("target_role", "")

    # Theme colors and font selection
    is_classic = (template == "classic")
    font_name = "Times New Roman" if is_classic else "Calibri"
    header_color = RGBColor(0x1E, 0x29, 0x3B) if is_classic else RGBColor(0x0F, 0x17, 0x2A)
    accent_color = RGBColor(0x33, 0x41, 0x55) if is_classic else RGBColor(0x25, 0x63, 0xEB)

    # Base font setup
    style_normal = doc.styles['Normal']
    style_normal.font.name = font_name
    style_normal.font.size = Pt(10)
    style_normal.font.color.rgb = RGBColor(0x1F, 0x29, 0x37)

    def add_section_heading(title: str):
        p = doc.add_paragraph()
        p.paragraph_format.space_before = Pt(8)
        p.paragraph_format.space_after = Pt(2)
        p.paragraph_format.keep_with_next = True
        run = p.add_run(title.upper())
        run.bold = True
        run.font.name = font_name
        run.font.size = Pt(11)
        run.font.color.rgb = accent_color
        # Border under section heading via paragraph bottom border or underscore
        p_border = doc.add_paragraph()
        p_border.paragraph_format.space_before = Pt(0)
        p_border.paragraph_format.space_after = Pt(4)
        run_line = p_border.add_run("―" * 65 if is_classic else "―" * 65)
        run_line.font.size = Pt(6)
        run_line.font.color.rgb = RGBColor(0xCB, 0xD5, 0xE1)

    # 1. Header (Name, Role, Contact info)
    p_name = doc.add_paragraph()
    p_name.paragraph_format.space_before = Pt(0)
    p_name.paragraph_format.space_after = Pt(2)
    p_name.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_classic else WD_ALIGN_PARAGRAPH.LEFT

    name_run = p_name.add_run(personal.get("full_name") or "Candidate Name")
    name_run.bold = True
    name_run.font.name = font_name
    name_run.font.size = Pt(18)
    name_run.font.color.rgb = header_color

    if target_role:
        p_role = doc.add_paragraph()
        p_role.paragraph_format.space_before = Pt(0)
        p_role.paragraph_format.space_after = Pt(4)
        p_role.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_classic else WD_ALIGN_PARAGRAPH.LEFT
        role_run = p_role.add_run(target_role)
        role_run.bold = True
        role_run.font.name = font_name
        role_run.font.size = Pt(11)
        role_run.font.color.rgb = accent_color

    # Contact line
    contact_parts: List[str] = []
    if personal.get("email"):
        contact_parts.append(personal["email"])
    if personal.get("phone"):
        contact_parts.append(personal["phone"])
    if personal.get("location"):
        contact_parts.append(personal["location"])
    if personal.get("linkedin_url"):
        contact_parts.append(personal["linkedin_url"])
    if personal.get("github_url"):
        contact_parts.append(personal["github_url"])

    if contact_parts:
        p_contact = doc.add_paragraph()
        p_contact.paragraph_format.space_before = Pt(0)
        p_contact.paragraph_format.space_after = Pt(6)
        p_contact.alignment = WD_ALIGN_PARAGRAPH.CENTER if is_classic else WD_ALIGN_PARAGRAPH.LEFT
        contact_run = p_contact.add_run("  |  ".join(contact_parts))
        contact_run.font.name = font_name
        contact_run.font.size = Pt(9)
        contact_run.font.color.rgb = RGBColor(0x4B, 0x55, 0x63)

    # 2. Professional Summary
    summary = content.get("summary", "").strip()
    if summary:
        add_section_heading("Professional Summary")
        p_sum = doc.add_paragraph()
        p_sum.paragraph_format.space_before = Pt(0)
        p_sum.paragraph_format.space_after = Pt(4)
        sum_run = p_sum.add_run(summary)
        sum_run.font.name = font_name
        sum_run.font.size = Pt(9.5)

    # 3. Technical Skills
    skills_cats = content.get("skills", [])
    if skills_cats:
        add_section_heading("Technical Skills")
        for cat in skills_cats:
            cat_name = cat.get("category", "Skills")
            items = cat.get("items", [])
            if not items:
                continue
            p_cat = doc.add_paragraph()
            p_cat.paragraph_format.space_before = Pt(0)
            p_cat.paragraph_format.space_after = Pt(2)
            c_run = p_cat.add_run(f"• {cat_name}: ")
            c_run.bold = True
            c_run.font.name = font_name
            c_run.font.size = Pt(9.5)
            items_run = p_cat.add_run(", ".join(items))
            items_run.font.name = font_name
            items_run.font.size = Pt(9.5)

    # 4. Projects
    projects = content.get("projects", [])
    if projects:
        add_section_heading("Key Projects")
        for proj in projects:
            p_proj = doc.add_paragraph()
            p_proj.paragraph_format.space_before = Pt(4)
            p_proj.paragraph_format.space_after = Pt(1)
            t_run = p_proj.add_run(proj.get("title", "Project"))
            t_run.bold = True
            t_run.font.name = font_name
            t_run.font.size = Pt(10)

            tech_list = proj.get("tech_stack", [])
            if tech_list:
                tech_run = p_proj.add_run(f"  [{', '.join(tech_list)}]")
                tech_run.font.name = font_name
                tech_run.font.size = Pt(9)
                tech_run.font.color.rgb = accent_color

            if proj.get("link"):
                link_run = p_proj.add_run(f"  |  {proj['link']}")
                link_run.font.name = font_name
                link_run.font.size = Pt(8.5)
                link_run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

            # Description bullets
            for b in proj.get("description_bullets", []):
                p_b = doc.add_paragraph(style='List Bullet')
                p_b.paragraph_format.space_before = Pt(0)
                p_b.paragraph_format.space_after = Pt(1)
                b_run = p_b.add_run(b)
                b_run.font.name = font_name
                b_run.font.size = Pt(9)

    # 5. Internships & Work Experience
    internships = content.get("internships", [])
    work_exp = content.get("work_experience", [])
    all_experience = []
    for it in internships:
        all_experience.append({**it, "type": "Internship"})
    for w in work_exp:
        all_experience.append({**w, "type": "Experience"})

    if all_experience:
        add_section_heading("Experience & Internships")
        for exp in all_experience:
            p_exp = doc.add_paragraph()
            p_exp.paragraph_format.space_before = Pt(4)
            p_exp.paragraph_format.space_after = Pt(1)
            role_run = p_exp.add_run(exp.get("role", "Role"))
            role_run.bold = True
            role_run.font.name = font_name
            role_run.font.size = Pt(10)

            comp_run = p_exp.add_run(f"  |  {exp.get('company', '')}")
            comp_run.font.name = font_name
            comp_run.font.size = Pt(9.5)
            comp_run.font.color.rgb = RGBColor(0x33, 0x41, 0x55)

            date_str = ""
            if exp.get("start_date") or exp.get("end_date"):
                date_str = f" ({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})"
                d_run = p_exp.add_run(date_str)
                d_run.font.name = font_name
                d_run.font.size = Pt(8.5)
                d_run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

            for b in exp.get("description_bullets", []):
                p_b = doc.add_paragraph(style='List Bullet')
                p_b.paragraph_format.space_before = Pt(0)
                p_b.paragraph_format.space_after = Pt(1)
                b_run = p_b.add_run(b)
                b_run.font.name = font_name
                b_run.font.size = Pt(9)

    # 6. Education
    education = content.get("education", [])
    if education:
        add_section_heading("Education")
        for edu in education:
            p_edu = doc.add_paragraph()
            p_edu.paragraph_format.space_before = Pt(3)
            p_edu.paragraph_format.space_after = Pt(1)
            deg_run = p_edu.add_run(edu.get("degree", ""))
            deg_run.bold = True
            deg_run.font.name = font_name
            deg_run.font.size = Pt(9.5)

            inst_run = p_edu.add_run(f", {edu.get('institution', '')}")
            inst_run.font.name = font_name
            inst_run.font.size = Pt(9.5)

            details = []
            if edu.get("graduation_year"):
                details.append(f"Graduation: {edu['graduation_year']}")
            if edu.get("score") is not None:
                st = "CGPA" if edu.get("score_type") == "cgpa" else "%"
                details.append(f"{st}: {edu['score']}")
            if details:
                det_run = p_edu.add_run(f"  [{', '.join(details)}]")
                det_run.font.name = font_name
                det_run.font.size = Pt(8.5)
                det_run.font.color.rgb = RGBColor(0x64, 0x74, 0x8B)

    # 7. Certifications & Achievements
    certs = content.get("certifications", [])
    achievements = content.get("achievements", [])
    if certs or achievements:
        add_section_heading("Certifications & Achievements")
        for cert in certs:
            p_c = doc.add_paragraph(style='List Bullet')
            p_c.paragraph_format.space_before = Pt(0)
            p_c.paragraph_format.space_after = Pt(1)
            c_name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            year = cert.get("year", "")
            line = c_name
            if issuer:
                line += f" — {issuer}"
            if year:
                line += f" ({year})"
            c_run = p_c.add_run(line)
            c_run.font.name = font_name
            c_run.font.size = Pt(9)

        for ach in achievements:
            if isinstance(ach, str) and ach.strip():
                p_a = doc.add_paragraph(style='List Bullet')
                p_a.paragraph_format.space_before = Pt(0)
                p_a.paragraph_format.space_after = Pt(1)
                a_run = p_a.add_run(ach.strip())
                a_run.font.name = font_name
                a_run.font.size = Pt(9)

    doc.save(output_path)
    return output_path


def export_resume_pdf(resume_doc: Dict[str, Any], output_path: str) -> str:
    """
    Exports a resume document to a clean ATS-friendly single-column PDF via ReportLab.
    Supports template styling ('classic' or 'modern').
    """
    os.makedirs(os.path.dirname(output_path), exist_ok=True)

    template = resume_doc.get("template", "modern")
    content = resume_doc.get("content", {})
    personal = content.get("personal", {})
    target_role = resume_doc.get("target_role", "")

    is_classic = (template == "classic")
    font_name = "Times-Roman" if is_classic else "Helvetica"
    font_bold = "Times-Bold" if is_classic else "Helvetica-Bold"

    header_col = colors.HexColor("#1E293B") if is_classic else colors.HexColor("#0F172A")
    accent_col = colors.HexColor("#334155") if is_classic else colors.HexColor("#2563EB")
    subtext_col = colors.HexColor("#4B5563")
    body_col = colors.HexColor("#1F2937")
    line_col = colors.HexColor("#E2E8F0")

    doc = SimpleDocTemplate(
        output_path,
        pagesize=letter,
        leftMargin=36,   # 0.5 inch
        rightMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom styles
    align_mode = 1 if is_classic else 0  # 1: Center, 0: Left

    title_style = ParagraphStyle(
        'DocTitle',
        fontName=font_bold,
        fontSize=18,
        leading=22,
        textColor=header_col,
        alignment=align_mode,
        spaceAfter=2
    )

    role_style = ParagraphStyle(
        'TargetRole',
        fontName=font_bold,
        fontSize=11,
        leading=14,
        textColor=accent_col,
        alignment=align_mode,
        spaceAfter=4
    )

    contact_style = ParagraphStyle(
        'ContactLine',
        fontName=font_name,
        fontSize=8.5,
        leading=11,
        textColor=subtext_col,
        alignment=align_mode,
        spaceAfter=8
    )

    heading_style = ParagraphStyle(
        'SectionHeading',
        fontName=font_bold,
        fontSize=10.5,
        leading=13,
        textColor=accent_col,
        spaceBefore=8,
        spaceAfter=2
    )

    body_style = ParagraphStyle(
        'BodyTextCustom',
        fontName=font_name,
        fontSize=9,
        leading=12,
        textColor=body_col,
        spaceAfter=3
    )

    bullet_style = ParagraphStyle(
        'BulletCustom',
        fontName=font_name,
        fontSize=8.5,
        leading=11,
        textColor=body_col,
        leftIndent=14,
        firstLineIndent=-10,
        spaceAfter=1.5
    )

    subheading_style = ParagraphStyle(
        'SubHeading',
        fontName=font_bold,
        fontSize=9.5,
        leading=12,
        textColor=header_col,
        spaceBefore=3,
        spaceAfter=1
    )

    story = []

    # 1. Header
    name_text = personal.get("full_name") or "Candidate Name"
    story.append(Paragraph(name_text, title_style))

    if target_role:
        story.append(Paragraph(target_role, role_style))

    contact_parts: List[str] = []
    if personal.get("email"):
        contact_parts.append(personal["email"])
    if personal.get("phone"):
        contact_parts.append(personal["phone"])
    if personal.get("location"):
        contact_parts.append(personal["location"])
    if personal.get("linkedin_url"):
        contact_parts.append(personal["linkedin_url"])
    if personal.get("github_url"):
        contact_parts.append(personal["github_url"])

    if contact_parts:
        story.append(Paragraph(" &nbsp;|&nbsp; ".join(contact_parts), contact_style))

    def add_section(title: str):
        story.append(Paragraph(title.upper(), heading_style))
        story.append(HRFlowable(width="100%", thickness=0.75, color=line_col, spaceBefore=1, spaceAfter=4))

    # 2. Professional Summary
    summary = content.get("summary", "").strip()
    if summary:
        add_section("Professional Summary")
        story.append(Paragraph(summary, body_style))

    # 3. Technical Skills
    skills_cats = content.get("skills", [])
    if skills_cats:
        add_section("Technical Skills")
        for cat in skills_cats:
            cat_name = cat.get("category", "Skills")
            items = cat.get("items", [])
            if not items:
                continue
            cat_html = f"<b>• {cat_name}:</b> {', '.join(items)}"
            story.append(Paragraph(cat_html, body_style))

    # 4. Key Projects
    projects = content.get("projects", [])
    if projects:
        add_section("Key Projects")
        for proj in projects:
            title = proj.get("title", "Project")
            tech_list = proj.get("tech_stack", [])
            tech_str = f" <font color='{accent_col.hexval()}'>[{', '.join(tech_list)}]</font>" if tech_list else ""
            link_str = f" <font color='#64748B'>| {proj['link']}</font>" if proj.get("link") else ""
            story.append(Paragraph(f"<b>{title}</b>{tech_str}{link_str}", subheading_style))

            for b in proj.get("description_bullets", []):
                story.append(Paragraph(f"• {b}", bullet_style))

    # 5. Internships & Experience
    internships = content.get("internships", [])
    work_exp = content.get("work_experience", [])
    all_experience = []
    for it in internships:
        all_experience.append({**it, "type": "Internship"})
    for w in work_exp:
        all_experience.append({**w, "type": "Experience"})

    if all_experience:
        add_section("Experience & Internships")
        for exp in all_experience:
            role = exp.get("role", "Role")
            company = exp.get("company", "")
            date_str = ""
            if exp.get("start_date") or exp.get("end_date"):
                date_str = f" <font color='#64748B'>({exp.get('start_date', '')} - {exp.get('end_date', 'Present')})</font>"
            story.append(Paragraph(f"<b>{role}</b> | {company}{date_str}", subheading_style))

            for b in exp.get("description_bullets", []):
                story.append(Paragraph(f"• {b}", bullet_style))

    # 6. Education
    education = content.get("education", [])
    if education:
        add_section("Education")
        for edu in education:
            deg = edu.get("degree", "")
            inst = edu.get("institution", "")
            details = []
            if edu.get("graduation_year"):
                details.append(f"Graduation: {edu['graduation_year']}")
            if edu.get("score") is not None:
                st = "CGPA" if edu.get("score_type") == "cgpa" else "%"
                details.append(f"{st}: {edu['score']}")
            det_str = f" <font color='#64748B'>[{', '.join(details)}]</font>" if details else ""
            story.append(Paragraph(f"<b>{deg}</b>, {inst}{det_str}", body_style))

    # 7. Certifications & Achievements
    certs = content.get("certifications", [])
    achievements = content.get("achievements", [])
    if certs or achievements:
        add_section("Certifications & Achievements")
        for cert in certs:
            c_name = cert.get("name", "")
            issuer = cert.get("issuer", "")
            year = cert.get("year", "")
            line = f"<b>{c_name}</b>"
            if issuer:
                line += f" — {issuer}"
            if year:
                line += f" ({year})"
            story.append(Paragraph(f"• {line}", bullet_style))

        for ach in achievements:
            if isinstance(ach, str) and ach.strip():
                story.append(Paragraph(f"• {ach.strip()}", bullet_style))

    doc.build(story)
    return output_path


def export_resume_pdf_and_docx(
    user_id: str,
    resume_id: str,
    content: Optional[Dict[str, Any]] = None,
    template: str = "modern",
    resume_doc: Optional[Dict[str, Any]] = None
) -> Tuple[str, str]:
    """
    Exports both ATS-friendly PDF and DOCX files to the user's private storage.
    """
    base_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "private_storage", str(user_id), "resumes"))
    os.makedirs(base_dir, exist_ok=True)
    pdf_path = os.path.join(base_dir, f"{resume_id}_{template}.pdf")
    docx_path = os.path.join(base_dir, f"{resume_id}_{template}.docx")

    doc_data = resume_doc or {
        "_id": resume_id,
        "user_id": user_id,
        "template": template,
        "content": content or {}
    }
    export_resume_pdf(doc_data, pdf_path)
    export_resume_docx(doc_data, docx_path)
    return pdf_path, docx_path


