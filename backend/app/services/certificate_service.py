import os
import uuid
from datetime import datetime
from reportlab.lib.pagesizes import A4, landscape
from reportlab.pdfgen import canvas
from reportlab.lib.units import inch
from reportlab.lib import colors
import qrcode
from PIL import Image

class CertificateService:
    @staticmethod
    def generate_agent_certificate(agent_name: str, agent_id: uuid.UUID, agent_code: str, issue_date: datetime, expiry_date: datetime):
        """
        Generates a secure PDF certificate for a newly certified AgriTrust Agent.
        In the field, this PDF can be verified via the embedded QR code.
        """
        output_dir = "certificates"
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        filename = f"agent_{agent_id}.pdf"
        filepath = os.path.join(output_dir, filename)
        
        c = canvas.Canvas(filepath, pagesize=landscape(A4))
        width, height = landscape(A4)
        
        # --- Background / Border ---
        c.setStrokeColor(colors.darkgreen)
        c.setLineWidth(5)
        c.rect(0.2*inch, 0.2*inch, width - 0.4*inch, height - 0.4*inch)
        
        # --- Header ---
        c.setFont("Helvetica-Bold", 40)
        c.drawCentredString(width/2, height - 1.5*inch, "AGRITRUST ACADEMY")
        c.setFont("Helvetica", 20)
        c.drawCentredString(width/2, height - 2*inch, "OFFICIAL FIELD AGENT CERTIFICATION")
        
        # --- Body ---
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height - 3.5*inch, "This is to certify that")
        
        c.setFont("Helvetica-Bold", 32)
        c.drawCentredString(width/2, height - 4.2*inch, agent_name.upper())
        
        c.setFont("Helvetica", 16)
        c.drawCentredString(width/2, height - 5*inch, f"has successfully completed the 10-module training curriculum")
        c.drawCentredString(width/2, height - 5.3*inch, "and is hereby recognized as a Certified AgriTrust Agent.")
        
        # --- Details ---
        c.setFont("Helvetica-Bold", 12)
        c.drawString(1*inch, 1.5*inch, f"AGENT CODE: {agent_code}")
        c.drawString(1*inch, 1.2*inch, f"ISSUED: {issue_date.strftime('%Y-%m-%d')}")
        c.drawString(1*inch, 0.9*inch, f"EXPIRES: {expiry_date.strftime('%Y-%m-%d')}")
        
        # --- QR Code (Verification) ---
        qr_data = f"AgriTrust:AgentCert:{agent_id}:{agent_code}"
        qr = qrcode.QRCode(version=1, box_size=10, border=1)
        qr.add_data(qr_data)
        qr.make(fit=True)
        qr_img = qr.make_image(fill_color="black", back_color="white")
        
        qr_path = f"tmp_qr_{agent_id}.png"
        qr_img.save(qr_path)
        
        c.drawImage(qr_path, width - 2.5*inch, 0.8*inch, 2*inch, 2*inch)
        os.remove(qr_path) # Cleanup
        
        # --- Signatures ---
        c.line(4*inch, 1.2*inch, 6.5*inch, 1.2*inch)
        c.setFont("Helvetica", 10)
        c.drawCentredString(5.25*inch, 1*inch, "Regional Director Siganture")
        
        c.showPage()
        c.save()
        
        return f"/certificates/{filename}"

certificate_service = CertificateService()
