
from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

class PDFGenerator:
    @staticmethod
    def generate_attendance_pdf(session_data, attendance_records, student_map, output_path):
        """
        Generates a PDF report for session attendance.
        session_data: dict containing session info (Title, Date, etc.)
        attendance_records: list of attendance dicts
        student_map: dict {studentId: studentName} to resolve names
        output_path: file path to save PDF
        """
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Custom Styles
            title_style = styles['Title']
            title_style.textColor = colors.HexColor("#2C3E50")
            
            header_style = styles['Heading2']
            header_style.textColor = colors.HexColor("#34495E")
            header_style.spaceAfter = 12

            # --- Header Section ---
            # Title
            title = f"Attendance Report"
            elements.append(Paragraph(title, title_style))
            elements.append(Spacer(1, 10))

            # Session Details Table (Professional Look)
            # Using a table for layout instead of plain paragraphs
            sess_details = [
                ["Session Title:", session_data.get('lecTitle', 'Unknown')],
                ["Session ID:", session_data.get('lecId', '-')],
                ["Date:", session_data.get('lecDate', '-')],
                ["Department:", session_data.get('lecDept', '-')],
                ["Total Attendance:", str(len(attendance_records))]
            ]
            
            details_table = Table(sess_details, colWidths=[120, 380])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor("#2C3E50")),
                ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(details_table)
            elements.append(Spacer(1, 20))

            # --- Attendance Table ---
            elements.append(Paragraph("Attendance List", header_style))

            data = [["Student ID", "Name", "Time Recorded"]]
            
            sorted_records = sorted(attendance_records, key=lambda x: x.get('timestamp', ''))

            for record in sorted_records:
                uid = record.get('userId', '-')
                name = student_map.get(uid, "Unknown")
                
                # Format time
                ts = record.get('timestamp')
                time_str = "-"
                if isinstance(ts, datetime):
                    time_str = ts.strftime("%H:%M:%S")
                elif isinstance(ts, str): # Fallback if string
                    time_str = ts 
                
                data.append([uid, name, time_str])

            if len(data) == 1:
                data.append(["No attendance records found", "-", "-"])

            # Table Style
            table = Table(data, colWidths=[100, 250, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2980B9")), # Blue Header
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, 0), 12),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                # Alternating Row Colors
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#ECF0F1")]),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor("#BDC3C7")),
                ('ALIGN', (1, 1), (1, -1), 'LEFT'), # Left align names for readability
                ('PADDING', (0, 0), (-1, -1), 6),
            ]))
            
            elements.append(table)
            
            # Build
            doc.build(elements)
            return True
        except Exception as e:
            print(f"Error generating PDF: {e}")
            return False
