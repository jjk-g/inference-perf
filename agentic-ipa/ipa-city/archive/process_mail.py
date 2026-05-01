import json
import subprocess
import re

reply_content = """---
# K8s Deploy Skill

## Apply Manifest
1. Locate the manifest file.
2. Apply the manifest: 'kubectl apply -f <manifest-path>'

## Wait Healthy
1. Wait for deployment rollout: 'kubectl rollout status deployment/<deployment-name>'
2. Check health endpoint using curl:
   'kubectl proxy &'
   'curl http://localhost:8001/api/v1/namespaces/default/services/<service-name>:<port>/proxy/health'

## Cleanup Resources
1. Delete using manifest: 'kubectl delete -f <manifest-path>'
2. Manual deletion: 'kubectl delete deployment <deployment-name>' and 'kubectl delete service <service-name>'
3. Verify deletion with 'kubectl get deployment <deployment-name>' and 'kubectl get service <service-name>'
---"""

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

# 1. Get all messages
out = run_cmd("bd list -t message --format json --limit 0")
messages = json.loads(out)

# Track messages we need to archive
to_archive = set(['ic-wisp-5q2', 'ic-wisp-f5h', 'ic-wisp-ejs', 'ic-wisp-587', 'ic-wisp-pim', 'ic-wisp-buo'])

# Pre-compute threads
threads = {}
for msg in messages:
    thread_id = None
    for label in msg.get('labels', []):
        if label.startswith('thread:'):
            thread_id = label
            break
    if thread_id:
        if thread_id not in threads:
            threads[thread_id] = []
        threads[thread_id].append(msg)

for msg in messages:
    if msg.get('status') != 'open':
        continue
    
    title = msg.get('title', '').lower()
    desc = msg.get('description', '').lower()
    
    if 'k8s-deploy' in title or 'k8s-deploy' in desc:
        sender = msg.get('metadata', {}).get('from', '').lower()
        if 'librarian' in sender:
            # We also need to archive all open librarian messages that contain k8s-deploy,
            # wait, the instruction says "After replying, archive the original message and your reply."
            # So if we sent a reply, it should be archived. We will collect our own k8s-deploy messages and just archive them to be safe if they are open.
            to_archive.add(msg['id'])
            continue
            
        print(f"Found request: {msg['id']} - {msg['title']}")
        
        # Check if already replied in this thread by librarian
        already_replied = False
        thread_id = None
        for label in msg.get('labels', []):
            if label.startswith('thread:'):
                thread_id = label
                break
        
        if thread_id and thread_id in threads:
            for thread_msg in threads[thread_id]:
                t_sender = thread_msg.get('metadata', {}).get('from', '').lower()
                if 'librarian' in t_sender and thread_msg['id'] != msg['id']:
                    # Simple heuristic: if librarian sent a message in this thread
                    already_replied = True
                    break
        
        if already_replied:
            print(f"  -> Already replied to {msg['id']}")
            to_archive.add(msg['id'])
        else:
            print(f"  -> Replying to {msg['id']}...")
            
            # Using subprocess.run with list instead of shell string
            result = subprocess.run(["gc", "mail", "reply", msg['id'], "-m", reply_content], capture_output=True, text=True)
            reply_out = result.stdout.strip()
            print(f"  -> Reply output: {reply_out}")
            
            to_archive.add(msg['id'])
            # Extract new message ID
            match = re.search(r'ic-\w+-\w+', reply_out)
            if match:
                reply_id = match.group(0)
                to_archive.add(reply_id)

print(f"Archiving messages: {to_archive}")
for msg_id in to_archive:
    run_cmd(f"gc mail archive {msg_id}")

print("Done.")
