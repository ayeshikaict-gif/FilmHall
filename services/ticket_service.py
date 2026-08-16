import os
import io
from models.booking import Booking
from config import Config

class TicketService:
    @staticmethod
    def generate_ticket_pdf(booking_id):
        import qrcode
        from reportlab.lib.pagesizes import letter
        from reportlab.lib import colors
        from reportlab.lib.units import inch
        from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, Image, HRFlowable
        from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

        booking = Booking.get_by_id(booking_id)
        if not booking:
            raise ValueError("Booking not found.")

        buffer = io.BytesIO()
        doc = SimpleDocTemplate(
            buffer,
            pagesize=letter,
            rightMargin=36,
            leftMargin=36,
            topMargin=36,
            bottomMargin=36
        )

        elements = []
        styles = getSampleStyleSheet()

        # Custom Palette
        CHARCOAL = colors.HexColor('#0B0B0F')
        GOLD = colors.HexColor('#D4AF6A')
        BURGUNDY = colors.HexColor('#5B1018')
        WHITE = colors.HexColor('#FFFFFF')
        LIGHT_BG = colors.HexColor('#F8F9FA')

        title_style = ParagraphStyle(
            'HeaderTitle',
            parent=styles['Heading1'],
            fontName='Helvetica-Bold',
            fontSize=24,
            textColor=GOLD,
            alignment=1, # Center
            spaceAfter=4
        )

        subtitle_style = ParagraphStyle(
            'HeaderSubtitle',
            parent=styles['Normal'],
            fontName='Helvetica-Oblique',
            fontSize=10,
            textColor=colors.white,
            alignment=1,
            spaceAfter=12
        )

        section_title = ParagraphStyle(
            'SectionTitle',
            parent=styles['Heading2'],
            fontName='Helvetica-Bold',
            fontSize=14,
            textColor=GOLD,
            spaceAfter=8
        )

        body_style = ParagraphStyle(
            'Body',
            parent=styles['Normal'],
            fontName='Helvetica',
            fontSize=10,
            textColor=colors.HexColor('#212529')
        )

        bold_style = ParagraphStyle(
            'BoldBody',
            parent=body_style,
            fontName='Helvetica-Bold'
        )

        # Header Block Data
        header_text = f"<b>CEYLON CINEPLEX</b><br/><font size=8 color='#D4AF6A'>{Config.CINEMA_TAGLINE}</font>"
        header_p = Paragraph(header_text, title_style)
        
        header_table = Table([[header_p]], colWidths=[540])
        header_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), CHARCOAL),
            ('ALIGN', (0,0), (-1,-1), 'CENTER'),
            ('VALIGN', (0,0), (-1,-1), 'MIDDLE'),
            ('TOPPADDING', (0,0), (-1,-1), 16),
            ('BOTTOMPADDING', (0,0), (-1,-1), 16),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 15))

        # Generate QR Code buffer
        qr_data = f"CEYLON-CINEPLEX|REF:{booking['booking_ref']}|BOOKING_ID:{booking['id']}|STATUS:{booking['booking_status']}"
        qr_img = qrcode.make(qr_data)
        qr_buffer = io.BytesIO()
        qr_img.save(qr_buffer, format='PNG')
        qr_buffer.seek(0)
        qr_image = Image(qr_buffer, width=1.5*inch, height=1.5*inch)

        # Main Info Grid
        ref_text = f"<font color='#5B1018'><b>BOOKING REF:</b></font> <font color='#D4AF6A'><b>{booking['booking_ref']}</b></font>"
        status_text = f"<b>STATUS:</b> <font color='green'>{booking['booking_status']}</font>"
        
        movie_info = f"""
        <b>Movie:</b> {booking['movie_title']}<br/>
        <b>Language / Duration:</b> {booking['language']} | {booking['duration_mins']} Mins<br/>
        <b>Hall:</b> {booking['hall_name']}<br/>
        <b>Date & Time:</b> {booking['show_date']} at {booking['start_time'][:5]}<br/>
        <b>Customer:</b> {booking['customer_name']} ({booking['customer_phone']})<br/>
        <b>Payment Method:</b> {booking['payment_method'] or 'ONLINE'} ({booking['booking_source']})
        """

        info_p = Paragraph(movie_info, body_style)
        ref_p = Paragraph(f"{ref_text}<br/>{status_text}", ParagraphStyle('RefStyle', parent=body_style, fontSize=12, spaceAfter=8))

        left_col = [ref_p, Spacer(1, 6), info_p]
        
        main_table = Table([[left_col, qr_image]], colWidths=[380, 160])
        main_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,-1), LIGHT_BG),
            ('VALIGN', (0,0), (-1,-1), 'TOP'),
            ('PADDING', (0,0), (-1,-1), 12),
            ('BOX', (0,0), (-1,-1), 1, GOLD),
        ]))
        elements.append(main_table)
        elements.append(Spacer(1, 15))

        # Seats Table
        elements.append(Paragraph("SEAT ASSIGNMENTS & BREAKDOWN", section_title))
        
        seats_data = [["Seat No.", "Seat Type", "Price (LKR)"]]
        for s in booking.get('seats', []):
            seats_data.append([
                s['seat_number'],
                s['seat_type_name'],
                f"Rs. {float(s['price_lkr']):,.2f}"
            ])
        
        seats_data.append(["TOTAL AMOUNT", "", f"Rs. {float(booking['total_amount_lkr']):,.2f}"])

        seats_table = Table(seats_data, colWidths=[150, 230, 160])
        seats_table.setStyle(TableStyle([
            ('BACKGROUND', (0,0), (-1,0), BURGUNDY),
            ('TEXTCOLOR', (0,0), (-1,0), WHITE),
            ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
            ('ALIGN', (0,0), (-1,-1), 'LEFT'),
            ('ALIGN', (2,0), (2,-1), 'RIGHT'),
            ('BOTTOMPADDING', (0,0), (-1,0), 8),
            ('BACKGROUND', (0,1), (-1,-2), colors.white),
            ('GRID', (0,0), (-1,-2), 0.5, colors.lightgrey),
            ('BACKGROUND', (0,-1), (-1,-1), CHARCOAL),
            ('TEXTCOLOR', (0,-1), (-1,-1), GOLD),
            ('FONTNAME', (0,-1), (-1,-1), 'Helvetica-Bold'),
            ('PADDING', (0,-1), (-1,-1), 10),
        ]))
        elements.append(seats_table)
        elements.append(Spacer(1, 20))

        # Footer Terms
        terms_text = f"""
        <b>Cinema Terms & Instructions:</b><br/>
        1. Please present this E-Ticket (printed or on mobile screen) at the cinema usher desk.<br/>
        2. Doors open 15 minutes before the scheduled showtime.<br/>
        3. Outside food and beverages are not permitted inside the cinema halls.<br/>
        <b>Ceylon Cineplex:</b> {Config.CINEMA_ADDRESS} | Helpline: {Config.CINEMA_PHONE}
        """
        terms_p = Paragraph(terms_text, ParagraphStyle('Terms', parent=body_style, fontSize=8, textColor=colors.HexColor('#6C757D')))
        elements.append(terms_p)

        doc.build(elements)
        buffer.seek(0)
        return buffer.getvalue()
