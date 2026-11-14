"""
Activation code generation and matching.

New codes use an alphabet without look-alike characters (no 0/O, 1/I/L), so
they can be read aloud or copied by hand without ambiguity. Codes are stored
as 8 plain characters; the UI shows them grouped as ``ABCD-EFGH``.

Codes issued before this alphabet was introduced may still contain 0, O, 1,
I or L. To keep those working, and to forgive the typo that motivated the
change (reading ``O`` as ``0``), matching compares codes after folding each
group of look-alikes to a single character.
"""

import hmac
import re
import secrets

ACTIVATION_CODE_ALPHABET = 'ABCDEFGHJKMNPQRSTUVWXYZ23456789'
ACTIVATION_CODE_LENGTH = 8

# Look-alike groups collapsed to one representative for comparison only.
_AMBIGUOUS_FOLD = str.maketrans({'0': 'O', '1': 'I', 'L': 'I'})
_AMBIGUOUS_CHARS = set('0O1IL')
_SEPARATORS = re.compile(r'[\s\-]+')


def generate_activation_code():
    """Return a new random activation code from the unambiguous alphabet."""
    return ''.join(
        secrets.choice(ACTIVATION_CODE_ALPHABET)
        for _ in range(ACTIVATION_CODE_LENGTH)
    )


def normalize_activation_code(raw):
    """Strip whitespace and hyphens and uppercase the code the user typed."""
    if not isinstance(raw, str):
        return ''
    return _SEPARATORS.sub('', raw).upper()


def has_ambiguous_chars(code):
    return any(ch in _AMBIGUOUS_CHARS for ch in code)


def fold_ambiguous(code):
    """Collapse look-alike characters so 0/O and 1/I/L compare equal."""
    return code.upper().translate(_AMBIGUOUS_FOLD)


def codes_match(entered, stored):
    """Compare a normalized entered code with a stored one, tolerating look-alikes."""
    if not entered or not stored:
        return False
    return hmac.compare_digest(fold_ambiguous(entered), fold_ambiguous(stored))
