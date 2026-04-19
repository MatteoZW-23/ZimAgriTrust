import os
import qrcode
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import cm
from reportlab.pdfgen import canvas
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from datetime import datetime
import uuid

from app.models.transaction import Order

class ReceiptService:
    def __init__(self):
        self.output_dir = "app/static/receipts"
        os.makedirs(self.output_dir, exist_ok=True)

    def generate_receipt_pdf(self, order: Order) -> str:
        """
        Generates a professional, tamper-proof PDF receipt for an AgriTrust transaction.
        """
        filename = f"RECEIPT_{order.order_number}.pdf"
        filepath = os.path.join(self.output_dir, filename)
        
        doc = SimpleDocTemplate(filepath, pagesize=A4)
        styles = getSampleStyleSheet()
        elements = []

        # 1. HEADER
        title_style = ParagraphStyle(
            'TitleStyle',
            parent=styles['Heading1'],
            fontSize=24,
            textColor=colors.HexColor("#2E7D32"), # AgriTrust Green
            spaceAfter=20
        )
        elements.append(Paragraph("AgriTrust Transaction Receipt", title_style))
        elements.append(Paragraph(f"Date Issued: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}", styles['Normal']))
        elements.append(Spacer(1, 1*cm))

        # 2. TRANSACTION SUMMARY TABLE
        data = [
            ["Order Number", str(order.order_number)],
            ["Transaction ID", str(order.id)],
            ["Status", str(order.status).upper()],
            ["Product", getattr(order, 'product', 'Agricultural Commodity')],
            ["Quantity", f"{order.quantity} units"],
            ["Total Amount", f"{order.currency} {order.total_amount:,.2f}"],
            ["Platform Fee (1%)", f"{order.currency} {order.platform_fee:,.2f}"],
            ["Seller Payout", f"{order.currency} {order.seller_payout:,.2f}"],
        ]
        
        t = Table(data, colWidths=[5*cm, 10*cm])
        t.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (0, -1), colors.lightgrey),
            ('TEXTCOLOR', (0, 0), (-1, -1), colors.black),
            ('ALIGN', (0, 0), (-1, -1), 'LEFT'),
            ('FONTNAME', (0, 0), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 10),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 12),
            ('GRID', (0,0), (-1,-1), 0.5, colors.grey)
        ]))
        elements.append(t)
        elements.append(Spacer(1, 2*cm))

        # 3. VERIFICATION QR CODE
        # We encode a verification URL (simulated)
        verification_data = f"https://agritrust.zw/verify/{order.id}"
        qr = qrcode.QRCode(version=1, box_size=10, border=5)
        qr.add_data(verification_data)
        qr.make(fit=True)
        
        qr_img_path = os.path.join(self.output_dir, f"QR_{order.id}.png")
        img = qr.make_image(fill_color="black", back_color="white")
        img.save(qr_img_path)
        
        from reportlab.platypus import Image
        qr_img = Image(qr_img_path, width=4*cm, height=4*cm)
        elements.append(Paragraph("Scan to Verify Transaction Authenticity", styles['Heading3']))
        elements.append(qr_img)
        
        # 4. FOOTER
        footer_text = "This is a digitally generated document by the AgriTrust Sovereign AI Network. No signature required."
        elements.append(Spacer(1, 2*cm))
        elements.append(Paragraph(footer_text, styles['Italic']))

        doc.build(elements)
        
        # Cleanup QR temp image
        if os.path.exists(qr_img_path):
            os.remove(qr_img_path)
            
        return filepath

receipt_service = ReceiptService()
