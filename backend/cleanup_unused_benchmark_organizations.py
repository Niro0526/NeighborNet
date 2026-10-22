"""Remove only exact, unreferenced benchmark fixture organizations after isolation."""
import os, json, hashlib
from pathlib import Path
os.environ.setdefault('DJANGO_SETTINGS_MODULE','config.settings.development')
import django
django.setup()
from django.db import transaction
from django.db.models.deletion import Collector
from django.core.serializers.json import DjangoJSONEncoder
from django.apps import apps
from apps.organizations.models import Organization
root = Path(__file__).resolve().parent.parent
backup = root/'backups/cleanup-20261022-071517'
manifest=json.loads((backup/'manifest.json').read_text())
assert hashlib.sha256(Path(manifest['path']).read_bytes()).hexdigest()==manifest['sha256']
inventory=json.loads((backup/'inventory.json').read_text())
expected={r['id']:r['name'] for r in inventory['organizations.Organization'] if r['id'].startswith(('EVAL-ORG-','ADV-ORG-'))}
assert len(expected)==10
targets=Organization.objects.filter(pk__in=expected)
assert {o.pk:o.name for o in targets}==expected
collector=Collector(using='default')
collector.collect(targets)
assert all(model is Organization for model in collector.data), 'Referenced organizations must be preserved.'
assert all(not qs.exists() for qs in collector.fast_deletes), 'Organization has dependent rows.'
protected_labels=['accounts.User','accounts.UserRoleAssignment','organizations.OrganizationMembership','volunteers.Volunteer']
def digest():
    return {label:hashlib.sha256(json.dumps(list(apps.get_model(label).objects.order_by('pk').values()),cls=DjangoJSONEncoder,sort_keys=True).encode()).hexdigest() for label in protected_labels}
before=digest()
remaining=list(Organization.objects.exclude(pk__in=expected).order_by('pk').values())
with transaction.atomic():
    count, models=collector.delete()
    assert digest()==before
    assert list(Organization.objects.order_by('pk').values())==remaining
report={'backup':manifest['path'],'deletedOrganizations':expected,'deletedCount':count,'byModel':models,'protectedBefore':before,'protectedAfter':digest(),'retainedOrganizations':[{'id':o['id'],'name':o['name']} for o in remaining],'provenance':'Exact primary keys and names in intelligence/fixtures/evaluation_dataset.py and advanced_scenarios.py; no dependent rows; recreated using those fixtures in neighbornet_db_benchmark.'}
(root/'docs/cleanup-evidence/benchmark-organization-cleanup.json').write_text(json.dumps(report,indent=2),encoding='utf-8')
print(json.dumps({'deleted':count,'retainedOrganizations':len(remaining)},indent=2))
