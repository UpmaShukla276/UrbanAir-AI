"""
alerts.py
Generates two kinds of text from REAL current data -- no invented
numbers, just formatting/wording logic:
  1. An "official" style report (for an official/enforcement audience)
  2. A plain Hinglish public advisory (for citizens)
Email sending is optional -- only runs if SMTP settings are present in .env.
"""

import os
import smtplib
from email.mime.text import MIMEText
from datetime import datetime, timezone


def build_official_report(location: dict, aqi, band: dict, grap_stage: dict, source_estimate: dict):
    lines = [
        f"UrbanAir AI -- Official Air Quality Report",
        f"Location: {location['name']} ({location['lat']}, {location['lon']})",
        f"Generated: {datetime.now(timezone.utc).isoformat()} UTC",
        "",
        f"Current AQI: {aqi if aqi is not None else 'N/A'} -- CPCB category: {band['category'] if band else 'N/A'}",
        f"GRAP Status: {grap_stage['label']}",
    ]
    if grap_stage["actions"]:
        lines.append("Mandated actions under current GRAP stage:")
        for a in grap_stage["actions"]:
            lines.append(f"  - {a}")
    if source_estimate and source_estimate.get("mix_percent"):
        lines.append("")
        lines.append("Estimated pollution source mix (rule-based estimate, not a direct measurement):")
        for src, pct in source_estimate["mix_percent"].items():
            lines.append(f"  - {src}: {pct}%")
    return "\n".join(lines)


def build_public_advisory_hinglish(location: dict, aqi, band: dict):
    if aqi is None:
        return f"{location['name']} ka data abhi available nahi hai. Thodi der me phir check karein."

    category = band["category"] if band else "Unknown"
    advisory = band["advisory"] if band else ""

    if aqi <= 100:
        tone = f"{location['name']} me hawa aaj thik hai (AQI {aqi}, {category}). Bahar jaana safe hai."
    elif aqi <= 200:
        tone = f"{location['name']} me AQI {aqi} hai ({category}). Bachon aur bujurgo ko zyada der bahar exercise na karne ki salah hai."
    elif aqi <= 300:
        tone = f"{location['name']} me AQI {aqi} hai ({category}) -- hawa kaafi kharab hai. Mask pehen ke nikle, bahar zyada der na rahe."
    else:
        tone = f"{location['name']} me AQI {aqi} hai ({category}) -- SEVERE. Ghar ke andar rahe, khidki band rakhe, bahar ka kaam zaroori ho tabhi jaaye."

    return f"{tone}\n\nCPCB advisory: {advisory}"


def send_email_alert(to_email: str, subject: str, body: str):
    """
    Only works if SMTP_HOST, SMTP_PORT, SMTP_USER, SMTP_PASSWORD are set
    in .env. Returns (success: bool, message: str). Never fabricates a
    "sent" result -- if config is missing, it says so plainly.
    """
    host = os.getenv("SMTP_HOST")
    port = os.getenv("SMTP_PORT")
    user = os.getenv("SMTP_USER")
    password = os.getenv("SMTP_PASSWORD")

    if not all([host, port, user, password]):
        return False, "Email not sent -- SMTP_HOST/SMTP_PORT/SMTP_USER/SMTP_PASSWORD not set in .env."

    try:
        msg = MIMEText(body)
        msg["Subject"] = subject
        msg["From"] = user
        msg["To"] = to_email

        with smtplib.SMTP(host, int(port), timeout=10) as server:
            server.starttls()
            server.login(user, password)
            server.sendmail(user, [to_email], msg.as_string())
        return True, "Email sent."
    except Exception as e:
        return False, f"Email failed: {e}"
