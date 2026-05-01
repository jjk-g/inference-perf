import json
import subprocess

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

out = run_cmd("bd list -t message --format json --limit 0")
messages = json.loads(out)

to_archive = set()
for msg in messages:
    if msg.get('status') == 'open':
        title = msg.get('title', '').lower()
        desc = msg.get('description', '').lower()
        sender = msg.get('metadata', {}).get('from', '').lower()
        if 'k8s-deploy' in title or 'k8s-deploy' in desc:
            to_archive.add(msg['id'])
        if 'librarian' in sender and ('k8s-deploy' in title or 'k8s-deploy' in desc):
            to_archive.add(msg['id'])
            
# Also check if ic-wisp-6bv and ic-wisp-svw are open
for msg_id in ['ic-wisp-6bv', 'ic-wisp-svw']:
    to_archive.add(msg_id)

for msg_id in to_archive:
    run_cmd(f"gc mail archive {msg_id}")

print(f"Archived {len(to_archive)} more messages.")
