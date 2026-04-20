import urllib.request
import json

apis = [
    '/api/dashboard/sessions?limit=3',
    '/api/graph/data',
    '/api/tasks/list',
    '/api/alerts/list',
    '/api/alerts/platform-status',
    '/api/overview/teams',
    '/api/overview/memories',
    '/api/cron/list',
]

for api in apis:
    try:
        r = urllib.request.urlopen(f'http://127.0.0.1:5000{api}')
        data = json.loads(r.read())
        print(f'\n=== {api} ===')
        if isinstance(data, list):
            print(f'  Count: {len(data)}')
            if data:
                print(f'  First item keys: {list(data[0].keys())[:8]}')
        elif isinstance(data, dict):
            print(f'  Keys: {list(data.keys())[:10]}')
            for k, v in list(data.items())[:5]:
                if isinstance(v, (list, dict)):
                    print(f'  {k}: {type(v).__name__}({len(v)})')
                else:
                    print(f'  {k}: {v}')
    except Exception as e:
        print(f'\n=== {api} === ERROR: {e}')

print('\n\nAll API tests completed!')
