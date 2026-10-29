"""
Send GitHub-style signed webhooks to your local API, without GitHub.

It signs a sample "push" payload exactly like GitHub does:
    X-Hub-Signature-256: sha256=HMAC-SHA256(GITHUB_WEBHOOK_SECRET, raw body)
and sends a unique X-GitHub-Delivery ID, so you can see every case locally:

    valid         correctly signed                        -> expect 200
    duplicate     the same delivery ID sent twice         -> expect 200, then "duplicate, ignored"
    tampered      body changed after signing              -> expect 401
    unsigned      no X-Hub-Signature-256 header           -> expect 401
    wrong-prefix  right digest but "sha1=" prefix         -> expect 401

Usage (with the app running and GITHUB_WEBHOOK_SECRET set to the SAME value in both terminals):
    python example/send_signed_webhook.py                 # runs every case
    python example/send_signed_webhook.py --mode tampered
    python example/send_signed_webhook.py --url https://YOUR-NGROK-URL.ngrok-free.app/webhooks/github

Only uses the Python standard library.
"""
import argparse
import hashlib
import hmac
import json
import os
import sys
import urllib.error
import urllib.parse
import urllib.request
import uuid

DEFAULT_URL = 'http://127.0.0.1:8000/webhooks/github'

SAMPLE_PUSH = {
    'ref': 'refs/heads/main',
    'repository': {'name': 'api-webhook-test', 'full_name': 'student/api-webhook-test'},
    'pusher': {'name': 'student', 'email': 'student@example.com'},
    'commits': [
        {
            'id': 'a1b2c3d4e5f60718293a4b5c6d7e8f9012345678',
            'message': 'Test signed webhook from send_signed_webhook.py',
            'author': {'name': 'Student', 'email': 'student@example.com'},
            'timestamp': '2025-01-15T10:30:00Z'
        }
    ]
}


def sign(secret, body):
    """Return the X-Hub-Signature-256 value GitHub would send for this body."""
    return 'sha256=' + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def post(url, body, headers):
    """POST raw bytes and return (status, response text)."""
    request = urllib.request.Request(url, data=body, method='POST', headers=headers)
    host = urllib.parse.urlparse(url).hostname
    # Talk to localhost directly, even if an HTTP(S)_PROXY variable is set
    handlers = [urllib.request.ProxyHandler({})] if host in ('127.0.0.1', 'localhost') else []
    opener = urllib.request.build_opener(*handlers)
    try:
        with opener.open(request, timeout=10) as response:
            return response.status, response.read().decode('utf-8', 'replace')
    except urllib.error.HTTPError as error:
        return error.code, error.read().decode('utf-8', 'replace')


def send(url, secret, case, delivery_id=None):
    """Build, sign and send one webhook for the given case. Returns the HTTP status."""
    body = json.dumps(SAMPLE_PUSH).encode()
    headers = {
        'Content-Type': 'application/json',
        'User-Agent': 'GitHub-Hookshot/local-test',
        'X-GitHub-Event': 'push',
        'X-GitHub-Delivery': delivery_id or str(uuid.uuid4()),
    }

    if case == 'valid':
        headers['X-Hub-Signature-256'] = sign(secret, body)
    elif case == 'tampered':
        headers['X-Hub-Signature-256'] = sign(secret, body)       # sign the original...
        body = body.replace(b'student/api-webhook-test', b'attacker/evil-repo')  # ...then change it
    elif case == 'unsigned':
        pass                                                       # no signature header at all
    elif case == 'wrong-prefix':
        headers['X-Hub-Signature-256'] = sign(secret, body).replace('sha256=', 'sha1=', 1)

    status, text = post(url, body, headers)
    print(f"[{case:<12}] delivery={headers['X-GitHub-Delivery']} -> HTTP {status} {text.strip()}")
    return status


def main():
    parser = argparse.ArgumentParser(description='Send GitHub-style signed webhooks locally.')
    parser.add_argument('--url', default=DEFAULT_URL, help=f'webhook URL (default: {DEFAULT_URL})')
    parser.add_argument('--mode', default='all',
                        choices=['all', 'valid', 'duplicate', 'tampered', 'unsigned', 'wrong-prefix'])
    args = parser.parse_args()

    secret = os.environ.get('GITHUB_WEBHOOK_SECRET')
    if not secret:
        sys.exit('GITHUB_WEBHOOK_SECRET is not set. Set it in this terminal to the SAME value the app uses.')

    try:
        if args.mode in ('all', 'valid'):
            send(args.url, secret, 'valid')
        if args.mode in ('all', 'duplicate'):
            delivery_id = str(uuid.uuid4())
            send(args.url, secret, 'valid', delivery_id)
            print('   ...sending the same delivery ID again (simulating a GitHub retry):')
            send(args.url, secret, 'valid', delivery_id)
        for case in ('tampered', 'unsigned', 'wrong-prefix'):
            if args.mode in ('all', case):
                send(args.url, secret, case)
    except urllib.error.URLError as error:
        sys.exit(f'Could not reach {args.url}: {error.reason}. Is the app running?')

    if args.mode == 'all':
        print('\nExpected: valid 200, duplicate 200 then "duplicate, ignored", '
              'tampered/unsigned/wrong-prefix 401.')


if __name__ == '__main__':
    main()
