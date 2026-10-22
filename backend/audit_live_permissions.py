"""Supplementary real HTTP permission checks; browser lifecycle is audited separately."""
import json
from pathlib import Path
import requests

BASE = 'http://127.0.0.1:8000/api/v1'
results = []
def session(email):
    client = requests.Session()
    response = client.get(BASE+'/auth/csrf/', timeout=15)
    client.headers['X-CSRFToken'] = response.json()['csrfToken']
    response = client.post(BASE+'/auth/login/', json={'email':email,'password':'password123'}, timeout=15)
    response.raise_for_status()
    client.headers['X-CSRFToken'] = client.cookies['csrftoken']
    return client

def check(label, response, expected):
    passed = response.status_code in expected
    results.append({'step':label,'status':'PASS' if passed else 'FAIL','httpStatus':response.status_code,'expected':expected,'body':response.json() if response.content else None})

provider = session('fathima@pererahotels.lk')
recipient = session('sister.mary@graceeldercare.org')
volunteer = session('dinesh.mendis@gmail.com')
other = session('ravi.mendis@greenbites.lk')
check('Unauthenticated dashboard rejected', requests.get(BASE+'/dashboard/me/', timeout=15), [401,403])
check('Recipient admin dashboard rejected', recipient.get(BASE+'/dashboard/admin/', timeout=15), [403])
check('Volunteer food creation rejected', volunteer.post(BASE+'/resources/', json={}, timeout=15), [403])
check('Provider recipient creation rejected', provider.post(BASE+'/resource-requests/', json={}, timeout=15), [403])
check('Other provider inventory edit rejected', other.patch(BASE+'/resources/RES-0F5A7E/', json={'quantity':999}, timeout=15), [403])
check('Direct delivery state bypass rejected', volunteer.patch(BASE+'/delivery-tasks/TSK-658A5B/', json={'status':'AVAILABLE'}, timeout=15), [405])
check('Other courier completion rejected', other.post(BASE+'/delivery-tasks/TSK-658A5B/complete/', timeout=15), [403,404])
check('Repeated receipt cannot increment delivery count', recipient.post(BASE+'/delivery-tasks/TSK-658A5B/complete/', timeout=15), [400])
check('Coordinator role cannot be self assigned', requests.post(BASE+'/auth/register/', json={'email':'audit-escalation-denied@example.test','password':'password123','full_name':'Audit denied','roles':['COORDINATOR']}, timeout=15), [400])
check('Missing CSRF rejected', volunteer.post(BASE+'/delivery-tasks/TSK-658A5B/disrupt/', headers={'X-CSRFToken':''}, timeout=15), [403])
for name, client in [('provider',provider),('recipient',recipient),('volunteer',volunteer),('multi-role',other)]:
    response = client.get(BASE+'/dashboard/me/', timeout=15)
    check(name+' authorized dashboard', response, [200])
    response = client.get(BASE+'/notifications/unread_count/', timeout=15)
    check(name+' persisted unread count', response, [200])
check('Cancel only the failed audit deadline request', recipient.post(BASE+'/resource-requests/REQ-8EAFC7/cancel/', timeout=15), [200])
out = Path(__file__).resolve().parent.parent/'docs/integration-evidence/live-api-permissions.json'
out.write_text(json.dumps(results, indent=2), encoding='utf-8')
print(json.dumps([{'step':row['step'],'status':row['status'],'httpStatus':row['httpStatus']} for row in results],indent=2))
raise SystemExit(0 if all(row['status']=='PASS' for row in results) else 1)
