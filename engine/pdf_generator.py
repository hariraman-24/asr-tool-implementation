"""
Official Minutes of Meeting (MoM) PDF Generator for MeetBrief.
Generates institutional, formatted PDF reports using ReportLab.
"""

import os
from datetime import datetime

LOGO_PATH = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), "srm_logo.png")

def generate_mom_pdf(meeting, output_path):
    """
    Generate an official Minutes of Meeting (MoM) PDF document.
    meeting: dict returned by db.get_meeting_by_id(id)
    output_path: str destination file path
    """
    try:
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
        from reportlab.platypus import (
            SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle, PageBreak, HRFlowable, KeepTogether
        )
        from reportlab.lib.enums import TA_CENTER, TA_JUSTIFY, TA_LEFT, TA_RIGHT

        doc = SimpleDocTemplate(
            output_path,
            pagesize=letter,
            leftMargin=45,
            rightMargin=45,
            topMargin=35,
            bottomMargin=35
        )

        styles = getSampleStyleSheet()

        title_style = ParagraphStyle(
            'MOM_Title',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=18,
            leading=22,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#0f172a'),
            spaceAfter=4
        )

        inst_style = ParagraphStyle(
            'MOM_Inst',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=11,
            leading=14,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#1e3a8a'),
            spaceAfter=2
        )

        dept_style = ParagraphStyle(
            'MOM_Dept',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=10,
            leading=13,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#475569'),
            spaceAfter=10
        )

        sec_heading = ParagraphStyle(
            'MOM_SecHead',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=12,
            leading=15,
            textColor=colors.HexColor('#1e293b'),
            spaceBefore=10,
            spaceAfter=5
        )

        body_style = ParagraphStyle(
            'MOM_Body',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=10,
            leading=14,
            alignment=TA_JUSTIFY,
            spaceAfter=4
        )

        table_header = ParagraphStyle(
            'MOM_TH',
            parent=styles['Normal'],
            fontName='Times-Bold',
            fontSize=9,
            leading=12,
            alignment=TA_CENTER,
            textColor=colors.white
        )

        table_cell = ParagraphStyle(
            'MOM_TD',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=8.5,
            leading=11
        )

        table_cell_center = ParagraphStyle(
            'MOM_TD_Center',
            parent=styles['Normal'],
            fontName='Times-Roman',
            fontSize=8.5,
            leading=11,
            alignment=TA_CENTER
        )

        story = []

        # 1. Header with Logo (if available)
        if os.path.exists(LOGO_PATH):
            try:
                logo_img = RLImage(LOGO_PATH, width=110, height=26)
                story.append(logo_img)
                story.append(Spacer(1, 4))
            except Exception:
                pass

        story.append(Paragraph("SRM INSTITUTE OF SCIENCE AND TECHNOLOGY", inst_style))
        story.append(Paragraph("FACULTY OF ENGINEERING AND TECHNOLOGY • TIRUCHIRAPPALLI CAMPUS", dept_style))
        story.append(Paragraph(f"DEPARTMENT OF {meeting.get('department', 'COMPUTER SCIENCE & ENGINEERING').upper()}", dept_style))
        story.append(HRFlowable(width="100%", thickness=1.5, color=colors.HexColor('#1e3a8a'), spaceBefore=2, spaceAfter=8))

        story.append(Paragraph("MINUTES OF MEETING (MoM)", title_style))
        story.append(Paragraph(f"<b>Session Subject:</b> {meeting.get('title', 'Project Review')}", ParagraphStyle('Subj', parent=styles['Normal'], fontName='Times-Bold', fontSize=12, alignment=TA_CENTER, textColor=colors.HexColor('#2563eb'), spaceAfter=10)))

        # 2. Metadata Information Grid
        duration_sec = meeting.get('duration_seconds', 0)
        dur_str = f"{duration_sec // 60}m {duration_sec % 60}s" if duration_sec > 0 else "Recorded via Mic"
        meta_data = [
            [
                Paragraph("<b>Date:</b> " + str(meeting.get('date', 'N/A')), body_style),
                Paragraph("<b>Time:</b> " + str(meeting.get('time', 'N/A')), body_style),
                Paragraph("<b>Duration:</b> " + dur_str, body_style)
            ],
            [
                Paragraph("<b>Department:</b> " + str(meeting.get('department', 'CSE')), body_style),
                Paragraph("<b>Engine:</b> Faster-Whisper ASR", body_style),
                Paragraph("<b>Meeting ID:</b> #" + str(meeting.get('id', '1')), body_style)
            ]
        ]
        meta_table = Table(meta_data, colWidths=[170, 180, 170])
        meta_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f8fafc')),
            ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
            ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
        ]))
        story.append(meta_table)
        story.append(Spacer(1, 10))

        # 3. Attendees Section
        story.append(Paragraph("1. ATTENDEES & PARTICIPANTS", sec_heading))
        attendees = meeting.get('attendees', [])
        if attendees:
            att_str = " • ".join(attendees)
            story.append(Paragraph(f"<b>Present:</b> {att_str}", body_style))
        else:
            story.append(Paragraph("Dr. R. Baskar, Student Project Team Members", body_style))
        story.append(Spacer(1, 8))

        # 4. Executive Summary Section
        story.append(Paragraph("2. EXECUTIVE SUMMARY & DISCUSSION HIGHLIGHTS", sec_heading))
        summary = meeting.get('summary', 'No summary generated.')
        story.append(Paragraph(summary, body_style))
        story.append(Spacer(1, 8))

        # 5. Key Decisions Taken Section
        story.append(Paragraph("3. KEY DECISIONS FORMALIZED", sec_heading))
        decisions = meeting.get('decisions', [])
        if decisions:
            for idx, dec in enumerate(decisions, 1):
                story.append(Paragraph(f"<b>3.{idx}</b> {dec}", body_style))
        else:
            story.append(Paragraph("No formal decision was logged in this session.", body_style))
        story.append(Spacer(1, 8))

        # 6. Action Items & Responsibility Matrix
        story.append(Paragraph("4. ACTION ITEMS & RESPONSIBILITY MATRIX", sec_heading))
        action_items = meeting.get('action_items', [])

        if action_items:
            headers = [
                Paragraph("<b>#</b>", table_header),
                Paragraph("<b>Action Task</b>", table_header),
                Paragraph("<b>Assignee</b>", table_header),
                Paragraph("<b>Priority</b>", table_header),
                Paragraph("<b>Due Date</b>", table_header),
                Paragraph("<b>Status</b>", table_header)
            ]
            rows = [headers]

            for idx, item in enumerate(action_items, 1):
                prio = item.get('priority', 'Medium')
                status = item.get('status', 'Pending')

                prio_color = "#dc2626" if prio == "High" else ("#d97706" if prio == "Medium" else "#2563eb")
                status_color = "#16a34a" if status == "Completed" else ("#d97706" if status == "In Progress" else "#64748b")

                prio_para = Paragraph(f"<font color='{prio_color}'><b>{prio}</b></font>", table_cell_center)
                status_para = Paragraph(f"<font color='{status_color}'><b>{status}</b></font>", table_cell_center)

                rows.append([
                    Paragraph(str(idx), table_cell_center),
                    Paragraph(item.get('task', ''), table_cell),
                    Paragraph(item.get('assignee', 'Unassigned'), table_cell),
                    prio_para,
                    Paragraph(item.get('due_date', 'Not specified'), table_cell_center),
                    status_para
                ])

            action_table = Table(rows, colWidths=[25, 220, 95, 55, 65, 60])
            action_table.setStyle(TableStyle([
                ('BACKGROUND', (0,0), (-1,0), colors.HexColor('#1e3a8a')),
                ('BOX', (0,0), (-1,-1), 1, colors.HexColor('#cbd5e1')),
                ('INNERGRID', (0,0), (-1,-1), 0.5, colors.HexColor('#e2e8f0')),
                ('TOPPADDING', (0,0), (-1,-1), 4),
                ('BOTTOMPADDING', (0,0), (-1,-1), 4),
                ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ]))
            story.append(action_table)
        else:
            story.append(Paragraph("No pending action items recorded.", body_style))

        story.append(Spacer(1, 14))

        # 7. Verbatim Transcript (Collapsible / Excerpt)
        story.append(Paragraph("5. VERBATIM SPEECH TRANSCRIPTION", sec_heading))
        raw_transcript = meeting.get('raw_transcript', '')
        if len(raw_transcript) > 600:
            excerpt = raw_transcript[:600] + " ... [Full audio captured and archived securely in local SQLite database]"
        else:
            excerpt = raw_transcript
        transcript_box = Table(
            [[Paragraph(f"<i>\"{excerpt}\"</i>", ParagraphStyle('TR', parent=styles['Normal'], fontName='Times-Italic', fontSize=8.5, leading=12, textColor=colors.HexColor('#334155')))]],
            colWidths=[520]
        )
        transcript_box.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), colors.HexColor('#f1f5f9')),
            ('BOX', (0,0), (-1,-1), 0.5, colors.HexColor('#cbd5e1')),
            ('LEFTPADDING', (0,0), (-1,-1), 8),
            ('RIGHTPADDING', (0,0), (-1,-1), 8),
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
        ]))
        story.append(transcript_box)
        story.append(Spacer(1, 20))

        # 8. Signatures Block
        sig_data = [
            [
                Paragraph("<b>Prepared by:</b><br/><br/><br/>______________________<br/>Student Project Team", body_style),
                Paragraph("<b>Faculty Guide:</b><br/><br/><br/>______________________<br/>Dr. R. Baskar<br/>Asst. Professor, Dept. of CSE", body_style),
                Paragraph("<b>Approved by:</b><br/><br/><br/>______________________<br/>Head of Department<br/>SRM IST, Tiruchirappalli", body_style)
            ]
        ]
        sig_table = Table(sig_data, colWidths=[175, 175, 170])
        sig_table.setStyle(TableStyle([
            ('TOPPADDING', (0,0), (-1,-1), 5),
            ('BOTTOMPADDING', (0,0), (-1,-1), 5),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
        ]))
        story.append(KeepTogether(sig_table))

        # Footer note
        story.append(Spacer(1, 15))
        footer_style = ParagraphStyle(
            'FooterNote',
            parent=styles['Normal'],
            fontName='Times-Italic',
            fontSize=7.5,
            leading=10,
            alignment=TA_CENTER,
            textColor=colors.HexColor('#64748b')
        )
        story.append(Paragraph(f"Generated by MeetBrief Privacy-First ASR Engine • {datetime.now().strftime('%d %B %Y, %I:%M %p')} • Local On-Premise Processing", footer_style))

        doc.build(story)
        return True

    except Exception as e:
        # Fallback to plain text if reportlab has any issue
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"MINUTES OF MEETING\nTitle: {meeting.get('title')}\nDate: {meeting.get('date')}\n\n")
            f.write(f"Summary:\n{meeting.get('summary')}\n\n")
            f.write("Action Items:\n")
            for item in meeting.get('action_items', []):
                f.write(f"- {item.get('task')} (Assignee: {item.get('assignee')}, Due: {item.get('due_date')}, Priority: {item.get('priority')})\n")
        return True
