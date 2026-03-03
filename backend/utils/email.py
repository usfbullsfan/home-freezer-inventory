"""Email utility for sending notifications via SMTP.

Supports three connection modes, controlled by environment variables:

  Mode 1 – STARTTLS (port 587, external relay like Gmail):
    SMTP_USE_TLS=true   (default)

  Mode 2 – SSL wrapper (port 465):
    SMTP_USE_TLS=false
    SMTP_USE_SSL=true

  Mode 3 – Plain SMTP, no encryption (localhost Postfix on port 25):
    SMTP_USE_TLS=false
    SMTP_USE_SSL=false  (default when SMTP_USE_TLS is false)

Required variables for all modes:
  SMTP_SERVER        - Hostname (e.g. localhost, smtp.gmail.com)
  EMAIL_FROM_ADDRESS - Sender address shown in the From header

Optional variables:
  SMTP_PORT         - Port number (default: 25 for plain, 587 for TLS, 465 for SSL)
  SMTP_USERNAME     - Login username (not needed for localhost)
  SMTP_PASSWORD     - Login password  (not needed for localhost)
  SMTP_USE_TLS      - 'true' to use STARTTLS (default: true unless SMTP_SERVER=localhost)
  SMTP_USE_SSL      - 'true' to use SSL wrapper (default: false)
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
    server = os.environ.get('SMTP_SERVER', '')
    use_ssl = os.environ.get('SMTP_USE_SSL', 'false').lower() == 'true'

    # Default use_tls to False for localhost (no TLS needed), True otherwise
    default_tls = 'false' if server in ('localhost', '127.0.0.1', '::1') else 'true'
    use_tls = os.environ.get('SMTP_USE_TLS', default_tls).lower() == 'true'

    # Default port based on connection mode
    if use_ssl:
        default_port = 465
    elif use_tls:
        default_port = 587
    else:
        default_port = 25

    return {
        'server': server,
        'port': int(os.environ.get('SMTP_PORT', str(default_port))),
        'username': os.environ.get('SMTP_USERNAME', ''),
        'password': os.environ.get('SMTP_PASSWORD', ''),
        'use_tls': use_tls,
        'use_ssl': use_ssl,
        'from_address': os.environ.get('EMAIL_FROM_ADDRESS', ''),
        'from_name': os.environ.get('EMAIL_FROM_NAME', 'Freezer Inventory'),
    }


def is_email_configured():
    """Return True when the minimum required SMTP variables are set.

    For localhost Postfix, only SMTP_SERVER and EMAIL_FROM_ADDRESS are needed
    (no credentials required).
    """
    cfg = _get_smtp_config()
    return bool(cfg['server'] and cfg['from_address'])


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
        if cfg['use_ssl']:
            # Mode 2: SSL wrapper (port 465)
            smtp = smtplib.SMTP_SSL(cfg['server'], cfg['port'], timeout=15)
        elif cfg['use_tls']:
            # Mode 1: STARTTLS (port 587)
            smtp = smtplib.SMTP(cfg['server'], cfg['port'], timeout=15)
            smtp.starttls()
        else:
            # Mode 3: plain SMTP – used for localhost Postfix (port 25)
            smtp = smtplib.SMTP(cfg['server'], cfg['port'], timeout=15)

        if cfg['username'] and cfg['password']:
            smtp.login(cfg['username'], cfg['password'])

        smtp.sendmail(cfg['from_address'], to_addresses, msg.as_string())
        smtp.quit()

        logger.info('Email sent to %s | subject: %s', ', '.join(to_addresses), subject)
        return True

    except Exception as exc:
        logger.exception('Failed to send email to %s', ', '.join(to_addresses))
        raise RuntimeError(f'Email delivery failed: {exc}') from exc
