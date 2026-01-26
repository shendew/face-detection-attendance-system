from reportlab.lib import colors
from reportlab.lib.pagesizes import letter
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet
from datetime import datetime

class PDFGenerator:
    @staticmethod
    def generate_attendance_pdf(session_data, attendance_records, student_map, output_path):
        try:
            doc = SimpleDocTemplate(output_path, pagesize=letter)
            elements = []
            styles = getSampleStyleSheet()
            
            # Styles
            title_style = styles['Title']
            title_style.textColor = colors.HexColor("#2C3E50")
            header_style = styles['Heading2']
            header_style.textColor = colors.HexColor("#34495E")

            # Header
            elements.append(Paragraph("Attendance Report", title_style))
            elements.append(Spacer(1, 12))

            # Session Info Table
            sess_details = [
                ["Session Title:", session_data.get('lecTitle', 'Unknown')],
                ["Date:", session_data.get('lecDate', '-')],
                ["Department:", session_data.get('lecDept', '-')],
                ["Total Present:", str(len(attendance_records))]
            ]
            details_table = Table(sess_details, colWidths=[120, 380])
            details_table.setStyle(TableStyle([
                ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
            ]))
            elements.append(details_table)
            elements.append(Spacer(1, 20))

            # Attendance Table
            data = [["Student ID", "Name", "Time Recorded"]]
            sorted_records = sorted(attendance_records, key=lambda x: str(x.get('timestamp', '')))

            for record in sorted_records:
                uid = record.get('userId', '-')
                name = student_map.get(uid, "Unknown")
                ts = record.get('timestamp')
                
                # Robust time formatting
                if isinstance(ts, datetime):
                    time_str = ts.strftime("%H:%M:%S")
                else:
                    time_str = str(ts).split(' ')[-1] if ts else "-"
                
                data.append([uid, name, time_str])

            # Apply Table Styling
            table = Table(data, colWidths=[100, 250, 150])
            table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#2980B9")),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
                ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.whitesmoke, colors.HexColor("#ECF0F1")]),
            ]))
            
            elements.append(table)
            doc.build(elements)
            return True
        except Exception as e:
            print(f"Final PDF Error: {e}")
            return False