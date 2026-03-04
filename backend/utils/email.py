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
import resend

logger = logging.getLogger(__name__)


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
