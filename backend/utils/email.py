"""Email utility for sending notifications via SMTP.

Configuration is read from environment variables:
  SMTP_SERVER       - SMTP hostname (e.g. smtp.gmail.com)
  SMTP_PORT         - SMTP port (default: 587)
  SMTP_USERNAME     - SMTP login username
  SMTP_PASSWORD     - SMTP login password / app password
  SMTP_USE_TLS      - 'true' (default) to use STARTTLS on port 587
  EMAIL_FROM_ADDRESS - Sender address shown in From header
  EMAIL_FROM_NAME   - Sender display name (default: Freezer Inventory)
"""

import os
import smtplib
import logging
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText

logger = logging.getLogger(__name__)


def _get_smtp_config():
    """Return SMTP config dict from environment variables."""
    return {
        'server': os.environ.get('SMTP_SERVER', ''),
        'port': int(os.environ.get('SMTP_PORT', '587')),
        'username': os.environ.get('SMTP_USERNAME', ''),
        'password': os.environ.get('SMTP_PASSWORD', ''),
        'use_tls': os.environ.get('SMTP_USE_TLS', 'true').lower() == 'true',
        'from_address': os.environ.get('EMAIL_FROM_ADDRESS', ''),
        'from_name': os.environ.get('EMAIL_FROM_NAME', 'Freezer Inventory'),
    }


def is_email_configured():
    """Return True when the minimum required SMTP variables are set."""
    cfg = _get_smtp_config()
    return bool(cfg['server'] and cfg['username'] and cfg['from_address'])


def send_email(to_addresses, subject, text_body, html_body=None):
    """Send an email via SMTP.

    Args:
        to_addresses: str or list of str – recipient address(es).
        subject: str – email subject line.
        text_body: str – plain-text body (always included).
        html_body: str or None – optional HTML alternative body.

    Returns:
        True on success.

    Raises:
        RuntimeError: when SMTP is not configured or the send fails.
    """
    cfg = _get_smtp_config()

    if not cfg['server']:
        raise RuntimeError('SMTP_SERVER is not configured')
    if not cfg['from_address']:
        raise RuntimeError('EMAIL_FROM_ADDRESS is not configured')

    if isinstance(to_addresses, str):
        to_addresses = [to_addresses]

    from_header = (
        f"{cfg['from_name']} <{cfg['from_address']}>"
        if cfg['from_name']
        else cfg['from_address']
    )

    msg = MIMEMultipart('alternative')
    msg['Subject'] = subject
    msg['From'] = from_header
    msg['To'] = ', '.join(to_addresses)

    msg.attach(MIMEText(text_body, 'plain'))
    if html_body:
        msg.attach(MIMEText(html_body, 'html'))

    try:
        if cfg['use_tls']:
            smtp = smtplib.SMTP(cfg['server'], cfg['port'], timeout=15)
            smtp.starttls()
        else:
            smtp = smtplib.SMTP_SSL(cfg['server'], cfg['port'], timeout=15)

        if cfg['username'] and cfg['password']:
            smtp.login(cfg['username'], cfg['password'])

        smtp.sendmail(cfg['from_address'], to_addresses, msg.as_string())
        smtp.quit()

        logger.info('Email sent to %s | subject: %s', ', '.join(to_addresses), subject)
        return True

    except Exception as exc:
        logger.exception('Failed to send email to %s', ', '.join(to_addresses))
        raise RuntimeError(f'Email delivery failed: {exc}') from exc
