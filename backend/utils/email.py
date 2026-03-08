"""Email utility for sending notifications via Resend.

Required environment variables:
  RESEND_API_KEY     - API key from https://resend.com (starts with re_)
  EMAIL_FROM_ADDRESS - Verified sender address (must match a domain
                       verified in the Resend dashboard)

Optional:
  EMAIL_FROM_NAME    - Sender display name (default: Freezer Inventory)
"""

import os
import logging

logger = logging.getLogger(__name__)

try:
    import resend
    _RESEND_AVAILABLE = True
except ImportError:
    resend = None  # type: ignore[assignment]
    _RESEND_AVAILABLE = False


def _get_config():
    """Return Resend config dict from environment variables."""
    return {
        'api_key': os.environ.get('RESEND_API_KEY', ''),
        'from_address': os.environ.get('EMAIL_FROM_ADDRESS', ''),
        'from_name': os.environ.get('EMAIL_FROM_NAME', 'Freezer Inventory'),
    }


def is_email_configured():
    """Return True when the minimum required variables are set."""
    cfg = _get_config()
    return bool(cfg['api_key'] and cfg['from_address'])


def send_email(to_addresses, subject, text_body, html_body=None):
    """Send an email via the Resend API.

    Args:
        to_addresses: str or list of str – recipient address(es).
        subject: str – email subject line.
        text_body: str – plain-text body (always included).
        html_body: str or None – optional HTML alternative body.

    Returns:
        True on success.

    Raises:
        RuntimeError: when Resend is not configured or the send fails.
    """
    cfg = _get_config()

    if not _RESEND_AVAILABLE:
        raise RuntimeError('resend package is not installed. Run: pip install "resend>=2.0.0"')
    if not cfg['api_key']:
        raise RuntimeError('RESEND_API_KEY is not configured')
    if not cfg['from_address']:
        raise RuntimeError('EMAIL_FROM_ADDRESS is not configured')

    if isinstance(to_addresses, str):
        to_addresses = [to_addresses]

    from_header = (
        f"{cfg['from_name']} <{cfg['from_address']}>"
        if cfg['from_name']
        else cfg['from_address']
    )

    resend.api_key = cfg['api_key']

    params: resend.Emails.SendParams = {
        'from': from_header,
        'to': to_addresses,
        'subject': subject,
        'text': text_body,
    }
    if html_body:
        params['html'] = html_body

    try:
        resend.Emails.send(params)
        logger.info('Email sent to %s | subject: %s', ', '.join(to_addresses), subject)
        return True

    except Exception as exc:
        logger.exception('Failed to send email to %s', ', '.join(to_addresses))
        raise RuntimeError(f'Email delivery failed: {exc}') from exc

def send_expiration_digest(to_address, items, days_before):
    """Send an expiration digest email listing items expiring soon.

    Args:
        to_address: str – recipient email address.
        items: list of item dicts (from Item.to_dict()).
        days_before: int – the configured threshold (used in subject/body).
    """
    count = len(items)
    subject = f'Freezer expiration digest – {count} item{"s" if count != 1 else ""} expiring soon'

    # Plain-text body
    lines = [f'Freezer items expiring within {days_before} day{"s" if days_before != 1 else ""}:\n']
    for item in items:
        exp = item['expiration_date'][:10] if item.get('expiration_date') else 'No date'
        cat = f' [{item["category_name"]}]' if item.get('category_name') else ''
        lines.append(f'  \u2022 {item["name"]}{cat} \u2014 expires {exp}')
    text_body = '\n'.join(lines) + '\n\nLog in to your Freezer Inventory to take action.'

    # HTML body
    rows = ''.join(
        '<tr>'
        f'<td style="padding:0.4rem 0.75rem;border-bottom:1px solid #eee">{item["name"]}</td>'
        f'<td style="padding:0.4rem 0.75rem;border-bottom:1px solid #eee">{item.get("category_name") or "\u2014"}</td>'
        f'<td style="padding:0.4rem 0.75rem;border-bottom:1px solid #eee">{item["expiration_date"][:10] if item.get("expiration_date") else "No date"}</td>'
        '</tr>'
        for item in items
    )
    html_body = (
        f'<p>You have <strong>{count} item{"s" if count != 1 else ""}</strong> '
        f'expiring within {days_before} day{"s" if days_before != 1 else ""}:</p>'
        '<table style="border-collapse:collapse;width:100%;font-size:0.9em">'
        '<thead><tr style="background:#f8f9fa;text-align:left">'
        '<th style="padding:0.4rem 0.75rem">Item</th>'
        '<th style="padding:0.4rem 0.75rem">Category</th>'
        '<th style="padding:0.4rem 0.75rem">Expires</th>'
        '</tr></thead>'
        f'<tbody>{rows}</tbody></table>'
        '<p style="margin-top:1.5rem;color:#888;font-size:0.9em">Log in to your Freezer Inventory to take action.</p>'
    )

    return send_email(to_addresses=to_address, subject=subject, text_body=text_body, html_body=html_body)


def send_verification_email(to_address, code):
    """Send a 6-digit verification code to the given address."""
    return send_email(
        to_addresses=to_address,
        subject='Verify your email – Freezer Inventory',
        text_body=(
            f'Your email verification code is: {code}\n\n'
            'Enter this code in the app to confirm your email address.\n'
            'The code expires in 30 minutes.\n\n'
            'If you did not request this, you can ignore this message.'
        ),
        html_body=(
            '<p>Your email verification code is:</p>'
            f'<h2 style="letter-spacing:0.25em;font-family:monospace;font-size:2rem">{code}</h2>'
            '<p>Enter this code in the app to confirm your email address.<br>'
            'The code expires in <strong>30 minutes</strong>.</p>'
            '<p style="color:#888;font-size:0.9em">If you did not request this, you can ignore this message.</p>'
        ),
    )
