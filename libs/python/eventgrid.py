import json
import uuid
import requests
from datetime import datetime

def trigger_event(endpoint, accesskey, typestr, subject, data={}):
    id = str(uuid.uuid4())
    timestamp = datetime.utcnow()

    events=[
            {
                'id' : id,
                'subject' : subject,
                'data': data,
                'eventType': typestr,
                'eventTime': timestamp.isoformat(),
                'dataVersion': 1
            }
        ]
    
    headers = { 'aeg-sas-key' : accesskey, 'Content-Type' : 'application/json' }
    r = requests.post(endpoint, headers=headers, data=json.dumps(events))
    
    if not 200 >= r.status_code < 300:
        raise Exception(r.content)