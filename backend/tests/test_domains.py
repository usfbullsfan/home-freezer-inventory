"""Tests for utils/domains.py (domain configuration)."""

import pytest
from utils import domains


@pytest.fixture(autouse=True)
def clean_env(monkeypatch):
    for var in ('APP_DOMAIN', 'APP_DEV_DOMAIN', 'RP_ID', 'FLASK_ENV'):
        monkeypatch.delenv(var, raising=False)


def test_defaults_match_current_domain():
    assert domains.get_app_domain() == 'thefreezer.xyz'
    assert domains.get_dev_domain() == 'dev.thefreezer.xyz'
    assert domains.get_rp_id() == 'thefreezer.xyz'
    assert domains.get_base_url() == 'https://thefreezer.xyz'


def test_dev_base_url(monkeypatch):
    monkeypatch.setenv('FLASK_ENV', 'development')
    assert domains.get_base_url() == 'https://dev.thefreezer.xyz'


def test_new_domain_via_env(monkeypatch):
    monkeypatch.setenv('APP_DOMAIN', 'freezer.wetpaws.dev')
    assert domains.get_dev_domain() == 'dev.freezer.wetpaws.dev'
    assert domains.get_rp_id() == 'freezer.wetpaws.dev'
    assert domains.get_base_url() == 'https://freezer.wetpaws.dev'
    monkeypatch.setenv('FLASK_ENV', 'development')
    assert domains.get_base_url() == 'https://dev.freezer.wetpaws.dev'


def test_explicit_overrides(monkeypatch):
    monkeypatch.setenv('APP_DOMAIN', 'freezer.wetpaws.dev')
    monkeypatch.setenv('APP_DEV_DOMAIN', 'freezer-dev.wetpaws.dev')
    monkeypatch.setenv('RP_ID', 'wetpaws.dev')
    assert domains.get_dev_domain() == 'freezer-dev.wetpaws.dev'
    assert domains.get_rp_id() == 'wetpaws.dev'


@pytest.mark.parametrize('url,expected', [
    ('https://thefreezer.xyz', 'https://thefreezer.xyz'),
    ('https://thefreezer.xyz/settings?x=1', 'https://thefreezer.xyz'),
    ('https://dev.thefreezer.xyz', 'https://dev.thefreezer.xyz'),
    ('http://localhost:3000/login#a', 'http://localhost:3000'),
    ('https://evil-thefreezer.xyz', 'https://thefreezer.xyz'),
    ('', 'https://thefreezer.xyz'),
])
def test_origin_mapping_default(url, expected):
    assert domains.origin_for_request_url(url) == expected


def test_origin_mapping_new_domain(monkeypatch):
    monkeypatch.setenv('APP_DOMAIN', 'freezer.wetpaws.dev')
    assert domains.origin_for_request_url('https://dev.freezer.wetpaws.dev/x') == 'https://dev.freezer.wetpaws.dev'
    assert domains.origin_for_request_url('https://freezer.wetpaws.dev') == 'https://freezer.wetpaws.dev'
    # Old domain is no longer the expected origin once switched
    assert domains.origin_for_request_url('https://thefreezer.xyz') == 'https://freezer.wetpaws.dev'


def test_wetpaws_layout(monkeypatch):
    """Planned production layout: dev is a sibling host with its own RP ID."""
    monkeypatch.setenv('APP_DOMAIN', 'freezer.wetpaws.dev')
    monkeypatch.setenv('APP_DEV_DOMAIN', 'dfreezer.wetpaws.dev')
    assert domains.origin_for_request_url('https://dfreezer.wetpaws.dev/login') == 'https://dfreezer.wetpaws.dev'
    assert domains.origin_for_request_url('https://freezer.wetpaws.dev/') == 'https://freezer.wetpaws.dev'
    monkeypatch.setenv('FLASK_ENV', 'development')
    assert domains.get_base_url() == 'https://dfreezer.wetpaws.dev'
