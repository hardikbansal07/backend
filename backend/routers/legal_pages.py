"""
Legal Pages Router
Serves Privacy Policy, Terms of Service, and Data Deletion pages.
Required by Facebook App Review for OAuth integration.
"""

from fastapi import APIRouter
from fastapi.responses import HTMLResponse

router = APIRouter(tags=["legal"])


def _page_wrapper(title: str, content: str) -> str:
    """Wrap content in a clean, styled HTML page."""
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{title} — Cerebr00</title>
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; }}
        body {{
            font-family: 'Segoe UI', system-ui, -apple-system, sans-serif;
            background: #0a0a0a;
            color: #e0e0e0;
            line-height: 1.8;
            padding: 40px 20px;
        }}
        .container {{
            max-width: 800px;
            margin: 0 auto;
            background: #141414;
            border-radius: 16px;
            padding: 48px;
            border: 1px solid #222;
        }}
        h1 {{
            font-size: 2rem;
            background: linear-gradient(135deg, #f5a623, #f7c948);
            -webkit-background-clip: text;
            -webkit-text-fill-color: transparent;
            margin-bottom: 8px;
        }}
        .subtitle {{
            color: #888;
            font-size: 0.9rem;
            margin-bottom: 32px;
        }}
        h2 {{
            color: #f5a623;
            font-size: 1.2rem;
            margin: 28px 0 12px 0;
        }}
        p, li {{
            color: #ccc;
            margin-bottom: 12px;
        }}
        ul {{ padding-left: 24px; }}
        a {{ color: #f7c948; text-decoration: none; }}
        a:hover {{ text-decoration: underline; }}
        .footer {{
            text-align: center;
            margin-top: 40px;
            padding-top: 20px;
            border-top: 1px solid #222;
            color: #666;
            font-size: 0.85rem;
        }}
    </style>
</head>
<body>
    <div class="container">
        {content}
        <div class="footer">
            © 2024-2026 Cerebr00 (Astrocareai). All rights reserved.<br>
            <a href="mailto:cerebr00hb@gmail.com">cerebr00hb@gmail.com</a>
        </div>
    </div>
</body>
</html>"""


@router.get("/privacy-policy", response_class=HTMLResponse)
async def privacy_policy():
    content = """
    <h1>Privacy Policy</h1>
    <p class="subtitle">Last updated: April 6, 2026</p>

    <h2>1. Information We Collect</h2>
    <p>When you use Cerebr00, we may collect the following information:</p>
    <ul>
        <li><strong>Account Information:</strong> Your name, email address, and profile picture when you sign in via Google or Facebook OAuth.</li>
        <li><strong>Usage Data:</strong> Pages visited, features used, and interaction timestamps to improve our services.</li>
        <li><strong>Birth Details:</strong> Date, time, and place of birth that you voluntarily provide for astrological calculations.</li>
    </ul>

    <h2>2. How We Use Your Information</h2>
    <ul>
        <li>To provide personalized astrological insights and reports.</li>
        <li>To authenticate your account and maintain your session.</li>
        <li>To improve our AI models and service quality.</li>
        <li>To communicate service updates and notifications.</li>
    </ul>

    <h2>3. Data Sharing</h2>
    <p>We do <strong>not</strong> sell, rent, or share your personal data with third parties, except:</p>
    <ul>
        <li>When required by law or legal process.</li>
        <li>With service providers who assist in operating our platform (e.g., cloud hosting, database).</li>
    </ul>

    <h2>4. Data Security</h2>
    <p>We use industry-standard security measures including encryption (TLS/SSL), secure database storage, and access controls to protect your data.</p>

    <h2>5. Third-Party Login (OAuth)</h2>
    <p>When you log in via Google or Facebook, we only access your basic profile information (name, email, profile picture). We do not post on your behalf or access your contacts.</p>

    <h2>6. Data Retention</h2>
    <p>Your data is retained as long as your account is active. You may request deletion at any time (see <a href="/data-deletion">Data Deletion</a>).</p>

    <h2>7. Your Rights</h2>
    <p>You have the right to access, correct, or delete your personal data. Contact us at <a href="mailto:cerebr00hb@gmail.com">cerebr00hb@gmail.com</a>.</p>

    <h2>8. Changes to This Policy</h2>
    <p>We may update this policy from time to time. Changes will be posted on this page with an updated date.</p>

    <h2>9. Contact Us</h2>
    <p>For any questions about this Privacy Policy, contact us at:<br>
    <a href="mailto:cerebr00hb@gmail.com">cerebr00hb@gmail.com</a></p>
    """
    return HTMLResponse(content=_page_wrapper("Privacy Policy", content))


@router.get("/terms", response_class=HTMLResponse)
async def terms_of_service():
    content = """
    <h1>Terms of Service</h1>
    <p class="subtitle">Last updated: April 6, 2026</p>

    <h2>1. Acceptance of Terms</h2>
    <p>By accessing or using Cerebr00 ("the Service"), you agree to be bound by these Terms of Service. If you do not agree, please do not use the Service.</p>

    <h2>2. Description of Service</h2>
    <p>Cerebr00 is an AI-powered Vedic astrology platform that provides personalized astrological insights, compatibility reports, and spiritual guidance.</p>

    <h2>3. User Accounts</h2>
    <ul>
        <li>You must provide accurate information when creating an account.</li>
        <li>You are responsible for maintaining the security of your account credentials.</li>
        <li>You must be at least 13 years old to use the Service.</li>
    </ul>

    <h2>4. Acceptable Use</h2>
    <p>You agree not to:</p>
    <ul>
        <li>Use the Service for any unlawful purpose.</li>
        <li>Attempt to reverse-engineer or exploit the platform.</li>
        <li>Share your account credentials with others.</li>
        <li>Use automated tools to scrape or extract data from the Service.</li>
    </ul>

    <h2>5. Disclaimer</h2>
    <p>Astrological insights provided by Cerebr00 are for <strong>entertainment and educational purposes only</strong>. They should not be considered as professional advice for medical, legal, financial, or other decisions.</p>

    <h2>6. Limitation of Liability</h2>
    <p>Cerebr00 shall not be liable for any indirect, incidental, or consequential damages arising from your use of the Service.</p>

    <h2>7. Termination</h2>
    <p>We reserve the right to suspend or terminate your account for violation of these terms.</p>

    <h2>8. Changes to Terms</h2>
    <p>We may modify these terms at any time. Continued use of the Service constitutes acceptance of the updated terms.</p>

    <h2>9. Contact</h2>
    <p>Questions? Contact us at <a href="mailto:cerebr00hb@gmail.com">cerebr00hb@gmail.com</a>.</p>
    """
    return HTMLResponse(content=_page_wrapper("Terms of Service", content))


@router.get("/data-deletion", response_class=HTMLResponse)
async def data_deletion():
    content = """
    <h1>Data Deletion Instructions</h1>
    <p class="subtitle">Last updated: April 6, 2026</p>

    <h2>How to Delete Your Data</h2>
    <p>Cerebr00 respects your right to control your personal data. If you wish to delete your account and all associated data, you can do so in the following ways:</p>

    <h2>Option 1: Email Request</h2>
    <p>Send an email to <a href="mailto:cerebr00hb@gmail.com">cerebr00hb@gmail.com</a> with the subject line <strong>"Data Deletion Request"</strong> and include:</p>
    <ul>
        <li>The email address associated with your account</li>
        <li>Your full name (as registered on the platform)</li>
    </ul>
    <p>We will process your request within <strong>7 business days</strong> and send you a confirmation email once your data has been deleted.</p>

    <h2>Option 2: In-App Deletion</h2>
    <p>Navigate to <strong>Settings → Account → Delete Account</strong> in the app to permanently remove all your data.</p>

    <h2>What Data Gets Deleted?</h2>
    <ul>
        <li>Your profile information (name, email, profile picture)</li>
        <li>All astrological data (birth details, reports, chat history)</li>
        <li>Session tokens and authentication data</li>
        <li>Any referral or payment records</li>
    </ul>

    <h2>What Happens After Deletion?</h2>
    <ul>
        <li>Your account will be permanently deactivated.</li>
        <li>All personal data will be removed from our active databases.</li>
        <li>Backup copies may take up to 30 days to be fully purged.</li>
        <li>This action is <strong>irreversible</strong>.</li>
    </ul>

    <h2>Facebook Data</h2>
    <p>If you signed up using Facebook Login, deleting your data on Cerebr00 does not affect your Facebook account. To manage Facebook's data, visit <a href="https://www.facebook.com/settings?tab=applications" target="_blank">Facebook App Settings</a>.</p>

    <h2>Contact</h2>
    <p>For questions about data deletion, contact: <a href="mailto:cerebr00hb@gmail.com">cerebr00hb@gmail.com</a></p>
    """
    return HTMLResponse(content=_page_wrapper("Data Deletion Instructions", content))
