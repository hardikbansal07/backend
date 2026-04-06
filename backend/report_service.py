import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from reportlab.lib.pagesizes import letter
from reportlab.pdfgen import canvas
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from io import BytesIO
from supabase import acreate_client, create_client, Client
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# Supabase Config
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")
SUPABASE_BUCKET = "reports"  # Assume a bucket named 'reports' exists

# Email Config
EMAIL_HOST = os.getenv("EMAIL_HOST", "smtp.gmail.com")
EMAIL_PORT = int(os.getenv("EMAIL_PORT", 587))
EMAIL_USER = os.getenv("EMAIL_USER")
EMAIL_PASSWORD = os.getenv("EMAIL_PASSWORD")

# Cached async client
_async_supabase_client = None

async def get_async_supabase_client():
    """Get or create an async Supabase client for use in FastAPI async context."""
    global _async_supabase_client
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not found.")
        logger.warning(f"  SUPABASE_URL set: {bool(SUPABASE_URL)}")
        logger.warning(f"  SUPABASE_KEY set: {bool(SUPABASE_KEY)}")
        return None
    if _async_supabase_client is None:
        logger.info(f"Creating async Supabase client for URL: {SUPABASE_URL}")
        _async_supabase_client = await acreate_client(SUPABASE_URL, SUPABASE_KEY)
    return _async_supabase_client

def get_supabase_client() -> Client:
    """Legacy sync client - kept for backward compatibility."""
    if not SUPABASE_URL or not SUPABASE_KEY:
        logger.warning("Supabase credentials not found.")
        return None
    return create_client(SUPABASE_URL, SUPABASE_KEY)

def generate_pdf_report(user_name: str, report_type: str, content_data: dict) -> bytes:
    """
    Generates a PDF report using ReportLab.
    """
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)
    styles = getSampleStyleSheet()
    story = []

    # Title
    title_style = styles['Title']
    title_style.textColor = colors.darkblue
    story.append(Paragraph(f"AJ's Cosmic Report", title_style))
    story.append(Paragraph(f"{report_type}", styles['Heading2']))
    story.append(Spacer(1, 12))

    # User Info
    normal_style = styles['Normal']
    story.append(Paragraph(f"<b>Prepared for:</b> {user_name}", normal_style))
    story.append(Paragraph(f"<b>Date:</b> {datetime.now().strftime('%B %d, %Y')}", normal_style))
    story.append(Spacer(1, 16))
    
    # Separator
    story.append(Paragraph("_" * 60, normal_style))
    story.append(Spacer(1, 24))

    # Helper for bold replacement
    def parse_bold(text):
        # Replace **text** with <b>text</b> using regex to match pairs
        # Non-greedy match for content between **
        import re
        return re.sub(r'\*\*(.*?)\*\*', r'<b>\1</b>', text)

    # --- Markdown Parsing Logic ---
    lines = content_data.split('\n')
    
    in_table = False
    table_data = []
    
    for line in lines:
        line = line.strip()
        if not line:
            if in_table and table_data:
                # Render table
                t = Table(table_data, colWidths=[120, 150, 180]) # Auto-adjust based on content if possible, but fixed is safer
                # Basic styling
                style_cmds = [
                    ('BACKGROUND', (0,0), (-1,0), colors.lightgrey),
                    ('TEXTCOLOR', (0,0), (-1,0), colors.whitesmoke),
                    ('ALIGN', (0,0), (-1,-1), 'LEFT'),
                    ('FONTNAME', (0,0), (-1,0), 'Helvetica-Bold'),
                    ('BOTTOMPADDING', (0,0), (-1,0), 12),
                    ('BACKGROUND', (0,1), (-1,-1), colors.beige),
                    ('GRID', (0,0), (-1,-1), 0.5, colors.grey),
                    ('VALIGN', (0,0), (-1,-1), 'TOP'),
                ]
                t.setStyle(TableStyle(style_cmds))
                story.append(t)
                story.append(Spacer(1, 12))
                table_data = []
                in_table = False
            continue

        # Headlines
        if line.startswith('# '): # H1
            h1 = styles['Heading1']
            h1.textColor = colors.darkblue
            story.append(Paragraph(line[2:], h1))
            story.append(Spacer(1, 12))
        elif line.startswith('## '): # H2 (Numbering usually handled by text)
            h2 = styles['Heading2']
            h2.textColor = colors.purple
            story.append(Paragraph(line[3:], h2))
            story.append(Spacer(1, 10))
        elif line.startswith('### '): # H3
            h3 = styles['Heading3']
            h3.textColor = colors.teal
            story.append(Paragraph(line[4:], h3))
            story.append(Spacer(1, 8))
        
        # Blockquotes / Tips
        elif line.startswith('> [!Tip]') or line.startswith('>'):
             # Tip box style
             text = line.replace('> [!Tip]', '').replace('>', '').strip()
             if text:
                 text = parse_bold(text)
                 # Create a table for the box effect
                 tip_style = ParagraphStyle('Tip', parent=styles['Normal'], backColor=colors.lightcyan, borderColor=colors.blue, borderWidth=1, borderPadding=10, textColor=colors.darkblue)
                 story.append(Paragraph(f"<b>TIP:</b> {text}", tip_style))
                 story.append(Spacer(1, 12))

        # Tables (Simple Pipe Table Parser)
        elif line.startswith('|'):
            in_table = True
            # Parse row
            cells = [c.strip() for c in line.split('|') if c.strip()]
            
            # Check if it's a separator row (e.g. | :--- | :--- |)
            if '---' in line:
                continue
            
            # Clean md formatting slightly from cells
            cleaned_cells = []
            for c in cells:
                c = parse_bold(c)
                cleaned_cells.append(Paragraph(c, styles['Normal']))
                
            if cleaned_cells:
                table_data.append(cleaned_cells)

        # List Items
        elif line.startswith('* ') or line.startswith('- '):
             bullet_text = line[2:]
             bullet_text = parse_bold(bullet_text)
             story.append(Paragraph(f"• {bullet_text}", styles['Normal'], bulletText='•'))
             story.append(Spacer(1, 4))
        
        elif line.startswith('1. ') or line.startswith('2. ') or line.startswith('3. '): # Simple numeric check
             list_text = line[3:]
             list_text = parse_bold(list_text)
             # Keep the number
             story.append(Paragraph(f"{line[:3]} {list_text}", styles['Normal']))
             story.append(Spacer(1, 4))

        # Normal Text
        else:
            text = parse_bold(line)
            story.append(Paragraph(text, styles['Normal']))
            story.append(Spacer(1, 6))

    # Flush any remaining table
    if in_table and table_data:
         t = Table(table_data)
         t.setStyle(TableStyle([('GRID', (0,0), (-1,-1), 1, colors.black)]))
         story.append(t)

        
    # Footer
    story.append(Spacer(1, 36))
    footer_style = styles['Italic']
    story.append(Paragraph("Generated by AstroCare AI - Your Cosmic Compass", footer_style))

    doc.build(story)
    pdf_bytes = buffer.getvalue()
    buffer.close()
    return pdf_bytes

async def upload_to_supabase(pdf_bytes: bytes, filename: str) -> str:
    """
    Uploads bytes to Supabase Storage and returns the public URL.
    Uses async client for proper FastAPI compatibility.
    """
    logger.info(f"[SUPABASE] Starting upload for file: {filename} ({len(pdf_bytes)} bytes)")
    
    try:
        supabase = await get_async_supabase_client()
        if not supabase:
            logger.error("[SUPABASE] Async client is not available — check SUPABASE_URL and SUPABASE_KEY env vars")
            return None

        file_path = f"generated/{filename}"
        logger.info(f"[SUPABASE] Uploading to bucket='{SUPABASE_BUCKET}', path='{file_path}'")
        
        # Upload using async client
        response = await supabase.storage.from_(SUPABASE_BUCKET).upload(
            path=file_path,
            file=pdf_bytes,
            file_options={"content-type": "application/pdf", "upsert": "true"}
        )
        
        logger.info(f"[SUPABASE] Upload response: {response}")
        
        # Validate upload response
        # supabase-py returns the path on success, or raises on error
        if response and hasattr(response, 'path'):
            logger.info(f"[SUPABASE] Upload successful, path: {response.path}")
        elif response:
            logger.info(f"[SUPABASE] Upload returned: {type(response)} = {response}")
        
        # Get Public URL
        # get_public_url might be sync or async depending on SDK version
        public_url_result = supabase.storage.from_(SUPABASE_BUCKET).get_public_url(file_path)
        
        # Handle case where it's a coroutine (async client)
        import asyncio
        if asyncio.iscoroutine(public_url_result):
            public_url = await public_url_result
        else:
            public_url = public_url_result
        
        # Fallback: construct URL manually if we got a coroutine object string
        if not isinstance(public_url, str) or 'coroutine' in str(public_url):
            public_url = f"{SUPABASE_URL}/storage/v1/object/public/{SUPABASE_BUCKET}/{file_path}"
            logger.warning(f"[SUPABASE] get_public_url returned non-string, using manual URL: {public_url}")
        
        logger.info(f"[SUPABASE] Public URL generated: {public_url}")
        
        return public_url

    except Exception as e:
        logger.error(f"[SUPABASE] Upload FAILED: {type(e).__name__}: {e}", exc_info=True)
        return None

def send_report_email(to_email: str, user_name: str, report_url: str):
    """
    Sends the report link via email.
    """
    if not EMAIL_USER or not EMAIL_PASSWORD:
        logger.warning("Email credentials not set. Skipping email.")
        return False

    try:
        msg = MIMEMultipart()
        msg['From'] = EMAIL_USER
        msg['To'] = to_email
        msg['Subject'] = "Your Astrology Report is Ready!"

        body = f"""
        Hello {user_name},

        Your astrology report has been successfully generated.
        
        You can download it here:
        {report_url}

        Thank you for using AstroCare AI.
        
        Warm regards,
        The AstroCare Team
        """
        msg.attach(MIMEText(body, 'plain'))

        server = smtplib.SMTP(EMAIL_HOST, EMAIL_PORT)
        server.starttls()
        server.login(EMAIL_USER, EMAIL_PASSWORD)
        text = msg.as_string()
        server.sendmail(EMAIL_USER, to_email, text)
        server.quit()
        logger.info(f"Email sent to {to_email}")
        return True
    except Exception as e:
        logger.error(f"Failed to send email: {e}")
        return False
