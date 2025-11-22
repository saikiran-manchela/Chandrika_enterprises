from reportlab.lib.pagesizes import letter, A4
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer, Image
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch, mm
from reportlab.lib import colors
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT
from datetime import datetime
import os

class InvoicePDFGenerator:
    def __init__(self, company_info=None):
        """Initialize PDF generator with company information"""
        self.company_info = company_info or {
            'name': 'Chandrika Enterprises',
            'address': 'D.no: 18-1-69, Estate Road, Near Mehar Complex, SriRam Nagar, Samalkot, Andhra Pradesh - 533440',
            'phone': '+91 9441942122',
            'email': 'chandrikaenterprisessamalkot@gmail.com',
            'gstin': '37ESVPM9846R1Z1'
        }
        
        self.styles = getSampleStyleSheet()
        self._create_custom_styles()
    
    def _create_custom_styles(self):
        """Create custom paragraph styles"""
        # Company name style
        self.company_name_style = ParagraphStyle(
            'CompanyName',
            parent=self.styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor('#2E3440'),
            alignment=TA_CENTER,
            spaceAfter=6
        )
        
        # Company details style
        self.company_details_style = ParagraphStyle(
            'CompanyDetails',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor("#CA6826"),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Invoice title style
        self.invoice_title_style = ParagraphStyle(
            'InvoiceTitle',
            parent=self.styles['Heading2'],
            fontSize=18,
            textColor=colors.HexColor('#CA6826'),
            alignment=TA_CENTER,
            spaceAfter=20
        )
        
        # Section heading style
        self.section_heading_style = ParagraphStyle(
            'SectionHeading',
            parent=self.styles['Heading3'],
            fontSize=12,
            textColor=colors.HexColor('#CA6826'),
            spaceBefore=10,
            spaceAfter=6
        )
        
        # Normal text style
        self.normal_style = ParagraphStyle(
            'CustomNormal',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2E3440')
        )
        
        # Right aligned style
        self.right_align_style = ParagraphStyle(
            'RightAlign',
            parent=self.styles['Normal'],
            fontSize=10,
            textColor=colors.HexColor('#2E3440'),
            alignment=TA_RIGHT
        )
    
    def generate_invoice_pdf(self, invoice_data, filename=None):
        """Generate PDF invoice"""
        if not filename:
            filename = f"invoice_{invoice_data['invoice_number']}.pdf"
        
        # Create PDF document
        doc = SimpleDocTemplate(
            filename,
            pagesize=A4,
            rightMargin=20*mm,
            leftMargin=20*mm,
            topMargin=20*mm,
            bottomMargin=20*mm
        )
        
        # Build content
        story = []
        
        # Company header
        story.extend(self._create_company_header())
        
        # Invoice title and number
        story.extend(self._create_invoice_header(invoice_data))
        
        # Customer information
        story.extend(self._create_customer_section(invoice_data))
        
        # Invoice items table
        story.extend(self._create_items_table(invoice_data))
        
        # Totals section
        story.extend(self._create_totals_section(invoice_data))
        
        # Footer
        story.extend(self._create_footer())
        
        # Build PDF
        doc.build(story)
        return filename
    
    def _create_company_header(self):
        """Create company header section"""
        content = []
        
        # Company name
        company_name = Paragraph(self.company_info['name'], self.company_name_style)
        content.append(company_name)
        
        # Company details
        details_text = f"""
        {self.company_info['address']}<br/>
        Phone: {self.company_info['phone']} | Email: {self.company_info['email']}<br/>
        GSTIN: {self.company_info['gstin']}
        """
        company_details = Paragraph(details_text, self.company_details_style)
        content.append(company_details)
        
        # Separator line
        content.append(Spacer(1, 10*mm))
        
        return content
    
    def _create_invoice_header(self, invoice_data):
        """Create invoice header with number and date"""
        content = []
        
        # Invoice title
        invoice_title = Paragraph("INVOICE", self.invoice_title_style)
        content.append(invoice_title)
        
        # Invoice details table
        invoice_details_data = [
            ['Invoice Number:', invoice_data['invoice_number']],
            ['Date:', f"{invoice_data['date']} {invoice_data['time']}"],
        ]
        
        invoice_details_table = Table(
            invoice_details_data,
            colWidths=[3*inch, 3*inch]
        )
        
        invoice_details_table.setStyle(TableStyle([
            ('ALIGN', (0, 0), (0, -1), 'RIGHT'),
            ('ALIGN', (1, 0), (1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.HexColor('#2E3440')),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ]))
        
        content.append(invoice_details_table)
        content.append(Spacer(1, 10*mm))
        
        return content
    
    def _create_customer_section(self, invoice_data):
        """Create customer information section"""
        content = []
        
        # Bill to section
        bill_to_heading = Paragraph("Bill To:", self.section_heading_style)
        content.append(bill_to_heading)
        
        customer_info = f"""
        <b>{invoice_data['customer_name']}</b><br/>
        {invoice_data['customer_address']}<br/>
        Phone: {invoice_data['customer_phone']}
        """
        
        customer_paragraph = Paragraph(customer_info, self.normal_style)
        content.append(customer_paragraph)
        content.append(Spacer(1, 8*mm))
        
        return content
    
    def _create_items_table(self, invoice_data):
        """Create items table"""
        content = []
        
        # Table header
        table_data = [
            ['S.No.', 'Product Name', 'Quantity', 'Unit Price (₹)', 'Total (₹)']
        ]
        
        # Add items
        for i, item in enumerate(invoice_data['items'], 1):
            table_data.append([
                str(i),
                item['product_name'],
                str(item['quantity']),
                f"₹{item['unit_price']:,.2f}",
                f"₹{item['total_price']:,.2f}"
            ])
        
        # Create table
        items_table = Table(
            table_data,
            colWidths=[0.8*inch, 3*inch, 1*inch, 1.5*inch, 1.5*inch]
        )
        
        # Table styling
        items_table.setStyle(TableStyle([
            # Header styling
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#5E81AC')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.whitesmoke),
            ('ALIGN', (0, 0), (-1, 0), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, 0), 11),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 0), (-1, 0), 12),
            
            # Data styling
            ('ALIGN', (0, 1), (0, -1), 'CENTER'),  # S.No.
            ('ALIGN', (1, 1), (1, -1), 'LEFT'),    # Product name
            ('ALIGN', (2, 1), (2, -1), 'CENTER'),  # Quantity
            ('ALIGN', (3, 1), (3, -1), 'RIGHT'),   # Unit price
            ('ALIGN', (4, 1), (4, -1), 'RIGHT'),   # Total
            
            ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
            ('FONTSIZE', (0, 1), (-1, -1), 10),
            ('TEXTCOLOR', (0, 1), (-1, -1), colors.HexColor('#2E3440')),
            
            # Grid and borders
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#D8DEE9')),
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F8F9FA')]),
            ('BOTTOMPADDING', (0, 1), (-1, -1), 8),
            ('TOPPADDING', (0, 1), (-1, -1), 8),
        ]))
        
        content.append(items_table)
        content.append(Spacer(1, 8*mm))
        
        return content
    
    def _create_totals_section(self, invoice_data):
        """Create totals section"""
        content = []
        
        # Totals table data (no GST since included in prices)
        totals_data = [
            ['Subtotal:', f"₹{invoice_data['subtotal']:,.2f}"],
            ['', ''],  # Empty row for spacing
            ['Total Amount:', f"₹{invoice_data['total_amount']:,.2f}"]
        ]
        
        # Create totals table
        totals_table = Table(
            totals_data,
            colWidths=[2*inch, 1.5*inch],
            hAlign='RIGHT'
        )
        
        # Totals table styling
        totals_table.setStyle(TableStyle([
            # Regular rows
            ('ALIGN', (0, 0), (0, 2), 'RIGHT'),
            ('ALIGN', (1, 0), (1, 2), 'RIGHT'),
            ('FONTNAME', (0, 0), (-1, 2), 'Helvetica'),
            ('FONTSIZE', (0, 0), (-1, 2), 10),
            ('TEXTCOLOR', (0, 0), (-1, 2), colors.HexColor('#2E3440')),
            ('BOTTOMPADDING', (0, 0), (-1, 2), 4),
            
            # Total row styling
            ('ALIGN', (0, 4), (-1, 4), 'RIGHT'),
            ('FONTNAME', (0, 4), (-1, 4), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 4), (-1, 4), 12),
            ('TEXTCOLOR', (0, 4), (-1, 4), colors.HexColor('#5E81AC')),
            ('TOPPADDING', (0, 4), (-1, 4), 8),
            ('BOTTOMPADDING', (0, 4), (-1, 4), 8),
            
            # Border for total row
            ('LINEABOVE', (0, 4), (-1, 4), 2, colors.HexColor('#5E81AC')),
        ]))
        
        content.append(totals_table)
        content.append(Spacer(1, 15*mm))
        
        return content
    
    def _create_footer(self):
        """Create invoice footer"""
        content = []
        
        # Thank you message
        thank_you_style = ParagraphStyle(
            'ThankYou',
            parent=self.styles['Normal'],
            fontSize=12,
            textColor=colors.HexColor('#5E81AC'),
            alignment=TA_CENTER,
            spaceBefore=10,
            spaceAfter=10
        )
        
        thank_you = Paragraph("Thank you for your business!", thank_you_style)
        content.append(thank_you)
        
        # Terms and conditions
        terms_style = ParagraphStyle(
            'Terms',
            parent=self.styles['Normal'],
            fontSize=8,
            textColor=colors.HexColor('#4C566A'),
            alignment=TA_CENTER
        )
        
        terms_text = """
        Terms & Conditions: Payment is due within 30 days. 
        Late payments may incur additional charges.
        """
        
        terms = Paragraph(terms_text, terms_style)
        content.append(terms)
        
        return content

if __name__ == "__main__":
    # Test PDF generation
    pdf_generator = InvoicePDFGenerator()
    
    # Sample invoice data
    sample_invoice = {
        'invoice_number': 'INV-20241020123456-ABC123',
        'customer_name': 'John Doe',
        'customer_phone': '9876543210',
        'customer_address': '123 Main Street\nCity, State - 12345',
        'date': '2024-10-20',
        'time': '14:30:00',
        'items': [
            {'product_name': 'Laptop', 'quantity': 1, 'unit_price': 45000.00, 'total_price': 45000.00},
            {'product_name': 'Mouse', 'quantity': 2, 'unit_price': 500.00, 'total_price': 1000.00},
            {'product_name': 'Keyboard', 'quantity': 1, 'unit_price': 1500.00, 'total_price': 1500.00}
        ],
        'subtotal': 47500.00,
        'cgst_rate': 9.0,
        'sgst_rate': 9.0,
        'cgst_amount': 4275.00,
        'sgst_amount': 4275.00,
        'total_amount': 56050.00
    }
    
    # Generate PDF
    filename = pdf_generator.generate_invoice_pdf(sample_invoice, "sample_invoice.pdf")
    print(f"Invoice PDF generated: {filename}")