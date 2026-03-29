import requests

def notify_discord(webhook, message):
    if not webhook:
        return
    requests.post(webhook, json={"content": message})

def notify_slack(webhook, message):
    if not webhook:
        return
    requests.post(webhook, json={"text": message})
