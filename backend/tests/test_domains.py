"""Tests for utils/domains.py (domain configuration)."""

import pytest
from utils import domains


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ('APP_DOMAIN', 'APP_DEV_DOMAIN', 'RP_ID', 'FLASK_ENV'):
        monkeypatch.delenv(var, raising=False)


def test_defaults():
    assert domains.get_app_domain() == 'freezer.wetpaws.dev'
    assert domains.get_dev_domain() == 'dfreezer.wetpaws.dev'
    assert domains.get_rp_id() == 'freezer.wetpaws.dev'
    assert domains.get_base_url() == 'https://freezer.wetpaws.dev'


def test_dev_base_url(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'development')
    assert domains.get_base_url() == 'https://dfreezer.wetpaws.dev'


def test_env_overrides(monkeypatch):
    monkeypatch.setenv('APP_DOMAIN', 'example.com')
    monkeypatch.setenv('APP_DEV_DOMAIN', 'dev.example.com')
    assert domains.get_app_domain() == 'example.com'
    assert domains.get_dev_domain() == 'dev.example.com'
    assert domains.get_rp_id() == 'example.com'
    assert domains.get_base_url() == 'https://example.com'
    monkeypatch.setenv('RP_ID', 'dev.example.com')
    assert domains.get_rp_id() == 'dev.example.com'


def test_values_are_normalized(monkeypatch):
    monkeypatch.setenv('APP_DOMAIN', '  Freezer.WetPaws.dev ')
    assert domains.get_app_domain() == 'freezer.wetpaws.dev'


@pytest.mark.parametrize('url,expected', [
    ('https://freezer.wetpaws.dev', 'https://freezer.wetpaws.dev'),
    ('https://freezer.wetpaws.dev/settings?x=1', 'https://freezer.wetpaws.dev'),
    ('https://dfreezer.wetpaws.dev/login', 'https://dfreezer.wetpaws.dev'),
    ('http://localhost:3000/login#a', 'http://localhost:3000'),
    # Lookalike and retired hosts fall back to prod, so WebAuthn rejects them
    ('https://evil-freezer.wetpaws.dev', 'https://freezer.wetpaws.dev'),
    ('https://thefreezer.xyz', 'https://freezer.wetpaws.dev'),
    ('', 'https://freezer.wetpaws.dev'),
])
def test_origin_mapping(url, expected):
    assert domains.origin_for_request_url(url) == expected
