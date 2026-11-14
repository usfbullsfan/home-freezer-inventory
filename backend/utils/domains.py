"""
Public domain configuration.

All public hostnames the app knows about come from here, so moving to a new
domain is a configuration change (environment variables) rather than a code
change.

Environment variables:
    APP_DOMAIN      Production hostname (default: freezer.wetpaws.dev)
    APP_DEV_DOMAIN  Dev hostname (default: dfreezer.wetpaws.dev)
    RP_ID           WebAuthn relying-party ID (default: APP_DOMAIN). Passkeys
                    are bound to this value; changing it invalidates every
                    passkey registered under the old value.
"""

import os
from urllib.parse import urlparse

DEFAULT_APP_DOMAIN = 'freezer.wetpaws.dev'
DEFAULT_DEV_DOMAIN = 'dfreezer.wetpaws.dev'

LOCAL_HOSTNAMES = ('localhost', '127.0.0.1')


def get_app_domain():
    return os.environ.get('APP_DOMAIN', DEFAULT_APP_DOMAIN).strip().lower()


def get_dev_domain():
    return os.environ.get('APP_DEV_DOMAIN', DEFAULT_DEV_DOMAIN).strip().lower()


def get_rp_id():
    return os.environ.get('RP_ID', get_app_domain()).strip().lower()


def get_prod_origin():
    return f'https://{get_app_domain()}'


def get_dev_origin():
    return f'https://{get_dev_domain()}'


def get_base_url():
    """Base URL for QR codes and links, based on FLASK_ENV."""
    if os.environ.get('FLASK_ENV') == 'development':
        return get_dev_origin()
    return get_prod_origin()


def origin_for_request_url(url):
    """Map a browser Origin/Referer URL to the WebAuthn origin we expect.

    Matches on the exact hostname. Local development URLs are returned as-is
    (minus query/fragment). Anything unrecognised falls back to production.
    """
    if not url:
        return get_prod_origin()

    hostname = (urlparse(url).hostname or '').lower()

    if hostname == get_dev_domain():
        return get_dev_origin()
    if hostname == get_app_domain():
        return get_prod_origin()
    if hostname in LOCAL_HOSTNAMES:
        parsed = urlparse(url)
        return f'{parsed.scheme}://{parsed.netloc}'
    return get_prod_origin()
