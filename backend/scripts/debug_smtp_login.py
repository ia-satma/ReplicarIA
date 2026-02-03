import smtplib
import os
from dotenv import load_dotenv

# Load env from backend directory (assuming running from root)
load_dotenv('backend/.env')

SMTP_HOST = 'smtp.dreamhost.com'
SMTP_PORT = 587
PASSWORD = os.environ.get('DREAMHOST_EMAIL_PASSWORD')

if not PASSWORD:
    print("❌ DREAMHOST_EMAIL_PASSWORD not found in backend/.env")
    # Fallback to local execution
    load_dotenv('.env')
    PASSWORD = os.environ.get('DREAMHOST_EMAIL_PASSWORD')

if not PASSWORD:
    print("❌ DREAMHOST_EMAIL_PASSWORD not found in .env either")
    exit(1)

print(f"Password found: {PASSWORD}")

candidates = [
    "noreply@revisar-ia.com",
    "ia@satma.mx",
    "pmo@revisar-ia.com",
    "contacto@revisar-ia.com",
    "admin@revisar-ia.com"
]

print(f"🔌 Connecting to {SMTP_HOST}:{SMTP_PORT}...")

try:
    server = smtplib.SMTP(SMTP_HOST, SMTP_PORT)
    server.starttls()
    print("✅ Connection & TLS established")
except Exception as e:
    print(f"❌ Connection failed: {e}")
    exit(1)

for email in candidates:
    print(f"🔑 Trying login with: {email}")
    try:
        server.login(email, PASSWORD)
        print(f"✅ SUCCESS! Correct email is: {email}")
        
        # Try sending an email
        try:
            from email.mime.text import MIMEText
            msg = MIMEText("This is a test email from debug script.")
            msg['Subject'] = "Debug SMTP Test"
            msg['From'] = email
            msg['To'] = "ia@satma.mx" # Admin email
            
            server.sendmail(email, ["ia@satma.mx"], msg.as_string())
            print(f"✅ Email sent successfully to ia@satma.mx from {email}")
        except Exception as send_error:
            print(f"❌ Login worked but sending failed: {send_error}")
            
        server.quit()
        exit(0)
    except smtplib.SMTPAuthenticationError:
        print(f"❌ Authentication failed for {email}")
    except Exception as e:
        print(f"❌ Error for {email}: {e}")

print("🛑 All candidates failed.")
server.quit()
