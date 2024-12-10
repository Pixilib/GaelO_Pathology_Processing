import json

def body_to_dict(body :str) -> dict:
    body_unicode = body.decode('utf-8')
    dict = json.loads(body_unicode)
    return dict