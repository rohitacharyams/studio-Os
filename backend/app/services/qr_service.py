"""
QR Code and PDF generation service for booking confirmations.
Generates QR codes for booking verification and creates PDF documents.
"""

import io
import os
import secrets
from datetime import datetime
from typing import Optional, Tuple

import qrcode
from PIL import Image
from reportlab.lib.pagesizes import letter
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Image as RLImage, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT
from flask import current_app

from app.services.s3_service import S3Service


class QRService:
    """Service for generating QR codes and booking confirmation PDFs."""
    
    @staticmethod
    def generate_qr_token() -> str:
        """Generate a unique, secure token for QR code verification."""
        return secrets.token_urlsafe(32)
    
    @staticmethod
    def generate_qr_code(data: str) -> io.BytesIO:
        """
        Generate a QR code image from data.
        
        Args:
            data: The data to encode in the QR code
            
        Returns:
            BytesIO buffer containing the QR code PNG image
        """
        qr = qrcode.QRCode(
            version=1,
            error_correction=qrcode.constants.ERROR_CORRECT_L,
            box_size=10,
            border=4,
        )
        qr.add_data(data)
        qr.make(fit=True)
        
        # Create image
        img = qr.make_image(fill_color="black", back_color="white")
        
        # Save to BytesIO
        buffer = io.BytesIO()
        img.save(buffer, format='PNG')
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def generate_booking_pdf(booking_data: dict) -> io.BytesIO:
        """
        Generate a PDF booking confirmation with QR code.
        
        Args:
            booking_data: Dictionary containing:
                - booking_number: Unique booking number
                - customer_name: Customer's name
                - customer_email: Customer's email
                - customer_phone: Customer's phone
                - class_name: Name of the dance class
                - session_date: Date of the session
                - session_time: Time of the session
                - studio_name: Name of the studio
                - studio_address: Studio address
                - payment_method: Payment method used
                - amount: Amount paid
                - qr_code_data: Data for QR code generation
                
        Returns:
            BytesIO buffer containing the PDF document
        """
        buffer = io.BytesIO()
        doc = SimpleDocTemplate(buffer, pagesize=letter)
        story = []
        styles = getSampleStyleSheet()
        
        # Custom styles
        title_style = ParagraphStyle(
            'CustomTitle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2563eb'),
            spaceAfter=30,
            alignment=TA_CENTER
        )
        
        heading_style = ParagraphStyle(
            'CustomHeading',
            parent=styles['Heading2'],
            fontSize=14,
            textColor=colors.HexColor('#1e40af'),
            spaceAfter=12
        )
        
        # Title
        story.append(Paragraph("🎉 Booking Confirmation", title_style))
        story.append(Spacer(1, 0.3*inch))
        
        # Studio info
        story.append(Paragraph(booking_data.get('studio_name', 'Dance Studio'), heading_style))
        if booking_data.get('studio_address'):
            story.append(Paragraph(booking_data['studio_address'], styles['Normal']))
        story.append(Spacer(1, 0.3*inch))
        
        # Booking details table
        booking_details = [
            ['Booking Number:', booking_data.get('booking_number', 'N/A')],
            ['Customer Name:', booking_data.get('customer_name', 'N/A')],
            ['Phone:', booking_data.get('customer_phone', 'N/A')],
            ['Email:', booking_data.get('customer_email', 'N/A')],
            ['', ''],
            ['Class:', booking_data.get('class_name', 'N/A')],
            ['Date:', booking_data.get('session_date', 'N/A')],
            ['Time:', booking_data.get('session_time', 'N/A')],
            ['', ''],
            ['Payment Method:', booking_data.get('payment_method', 'N/A')],
            ['Amount Paid:', f"₹{booking_data.get('amount', 0)}"],
        ]
        
        table = Table(booking_details, colWidths=[2*inch, 4*inch])
        table.setStyle(TableStyle([
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
            ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (0, -1), colors.HexColor('#374151')),
            ('TEXTCOLOR', (1, 0), (1, -1), colors.HexColor('#111827')),
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('LEFTPADDING', (0, 0), (-1, -1), 0),
            ('RIGHTPADDING', (0, 0), (-1, -1), 12),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        story.append(table)
        story.append(Spacer(1, 0.4*inch))
        
        # Generate QR code
        qr_code_data = booking_data.get('qr_code_data', '')
        if qr_code_data:
            qr_buffer = QRService.generate_qr_code(qr_code_data)
            
            # Add QR code to PDF
            story.append(Paragraph("Scan this QR code at the studio:", heading_style))
            story.append(Spacer(1, 0.2*inch))
            
            # Convert QR code buffer to ReportLab Image
            qr_image = RLImage(qr_buffer, width=3*inch, height=3*inch)
            qr_image.hAlign = 'CENTER'
            story.append(qr_image)
            story.append(Spacer(1, 0.2*inch))
        
        # Footer instructions
        footer_style = ParagraphStyle(
            'Footer',
            parent=styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#6b7280'),
            alignment=TA_CENTER
        )
        
        story.append(Spacer(1, 0.3*inch))
        story.append(Paragraph(
            "Please show this QR code at the studio entrance for verification.",
            footer_style
        ))
        story.append(Paragraph(
            "Thank you for booking with us! 💃🕺",
            footer_style
        ))
        
        # Build PDF
        doc.build(story)
        buffer.seek(0)
        
        return buffer
    
    @staticmethod
    def generate_and_upload_booking_assets(
        booking_number: str,
        qr_token: str,
        booking_data: dict,
        studio_id: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """
        Generate QR code and PDF, then upload both to S3.
        
        Args:
            booking_number: Unique booking number
            qr_token: QR verification token
            booking_data: Booking details for PDF generation
            studio_id: Studio ID for organizing files
            
        Returns:
            Tuple of (qr_code_url, pdf_url) or (None, None) if upload fails
        """
        try:
            s3_service = S3Service()
            
            # Generate QR code data (verification URL)
            base_url = current_app.config.get('FRONTEND_URL', 'https://dance-studio-os.netlify.app')
            qr_data = f"{base_url}/verify-booking?token={qr_token}"
            
            # Add QR data to booking data
            booking_data['qr_code_data'] = qr_data
            
            # Generate QR code image
            qr_buffer = QRService.generate_qr_code(qr_data)
            
            # Upload QR code to S3
            qr_filename = f"bookings/{studio_id}/{booking_number}_qr.png"
            qr_url = s3_service.upload_buffer(
                qr_buffer,
                qr_filename,
                content_type='image/png'
            )
            
            # Generate PDF
            pdf_buffer = QRService.generate_booking_pdf(booking_data)
            
            # Upload PDF to S3
            pdf_filename = f"bookings/{studio_id}/{booking_number}_confirmation.pdf"
            pdf_url = s3_service.upload_buffer(
                pdf_buffer,
                pdf_filename,
                content_type='application/pdf'
            )
            
            return qr_url, pdf_url
            
        except Exception as e:
            current_app.logger.error(f"Failed to generate/upload booking assets: {str(e)}")
            return None, None
