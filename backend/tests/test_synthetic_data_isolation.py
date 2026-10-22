"""Prevent benchmark and demo entry points from contaminating application data."""
from types import SimpleNamespace
from unittest.mock import patch
import pytest
from django.core.management import call_command
from django.core.management.base import CommandError
from common.synthetic_data import require_synthetic_database

@pytest.mark.parametrize('name', ['neighbornet_db', 'production', 'customer_test_data'])
def test_synthetic_guard_rejects_application_database(name):
    with patch('common.synthetic_data.connection', SimpleNamespace(settings_dict={'NAME':name})):
        with pytest.raises(CommandError):
            require_synthetic_database()

@pytest.mark.parametrize('name', ['test_neighbornet_db', 'neighbornet_db_benchmark'])
def test_synthetic_guard_allows_separate_databases(name):
    with patch('common.synthetic_data.connection', SimpleNamespace(settings_dict={'NAME':name})):
        require_synthetic_database()

@pytest.mark.parametrize('command,options', [('seed_demo',{'force':True}),('seed_isolated_pilot_demo',{'force_demo':True})])
def test_force_flags_do_not_bypass_database_isolation(command,options):
    with patch('common.synthetic_data.connection', SimpleNamespace(settings_dict={'NAME':'neighbornet_db'})):
        with pytest.raises(CommandError):
            call_command(command,**options)

@pytest.mark.parametrize('module', ['evaluation_dataset','advanced_scenarios'])
def test_fixture_helpers_reject_before_creating_organizations(module):
    from importlib import import_module
    fixture=import_module('apps.intelligence.fixtures.'+module)
    with patch('common.synthetic_data.connection',SimpleNamespace(settings_dict={'NAME':'neighbornet_db'})):
        with pytest.raises(CommandError):
            fixture.get_or_create_org('EVAL-ORG-X','Fixture','NGO',True,6.7,79.8)
