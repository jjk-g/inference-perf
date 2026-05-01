import subprocess
import json
import os
import re

def run_cmd(cmd):
    result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
    return result.stdout.strip()

def get_open_messages():
    output = run_cmd("bd list -t message --limit 0")
    # Output format: ○ ic-wisp-0u4s ● P2 Checkin: k8s-deploy
    ids = []
    for line in output.split('\n'):
        if line.startswith('○ ') or line.startswith('◐ '):
            parts = line.split()
            if len(parts) >= 2:
                ids.append(parts[1])
    return ids

def process_messages():
    ids = get_open_messages()
    processed_count = 0
    catalog_updates = []
    
    for bead_id in ids:
        show_output = run_cmd(f"bd show {bead_id}")
        
        # Parse title and description
        title_line = ""
        description = ""
        in_desc = False
        
        for line in show_output.split('\n'):
            if line.startswith('○ ' + bead_id) or line.startswith('◐ ' + bead_id):
                # Extract title, which is everything after '○ ic-wisp-id · ' and before ' ['
                match = re.search(r'· (.*?)   \[', line)
                if match:
                    title_line = match.group(1).strip()
            elif line.startswith('DESCRIPTION'):
                in_desc = True
                description = ""
            elif in_desc and line.startswith('LABELS:'):
                in_desc = False
            elif in_desc:
                description += line + "\n"
        
        title_line = title_line.strip()
        
        print(f"Processing {bead_id}: {title_line}")
        
        is_request = False
        content_to_send = ""
        request_type = ""
        request_name = ""
        
        # Determine request type
        if "Checkout:" in title_line or "Checkout:" in description:
            is_request = True
            request_type = "Skill Checkout"
            
            # Extract skill name
            match = re.search(r'Checkout:\s*([a-zA-Z0-9_\-]+)', title_line)
            if not match:
                match = re.search(r'Checkout:\s*([a-zA-Z0-9_\-]+)', description)
            
            if match:
                skill_name = match.group(1)
                request_name = skill_name
                print(f"  Skill requested: {skill_name}")
                
                # Special case handling for k8s-deploy based on instructions
                if skill_name == "k8s-deploy":
                    skill_files = ["apply_manifest_v1.md", "wait_healthy_v1.md", "cleanup_resources_v1.md"]
                    combined_content = ""
                    for f in skill_files:
                        path = f"library/skills/{f}"
                        if os.path.exists(path):
                            with open(path, 'r') as file:
                                combined_content += f"# {f}\n" + file.read() + "\n\n"
                    if combined_content:
                        content_to_send = combined_content
                    else:
                        content_to_send = f"Could not find skill files for {skill_name}."
                else:
                    # Look for the skill file
                    possible_files = [f"{skill_name}.md", f"{skill_name}_v1.md"]
                    found = False
                    for f in possible_files:
                        path = f"library/skills/{f}"
                        if os.path.exists(path):
                            with open(path, 'r') as file:
                                content_to_send = file.read()
                            found = True
                            break
                    if not found:
                        content_to_send = f"Could not find skill file for {skill_name}."
            else:
                content_to_send = "Could not parse skill name from the request."
                
        elif "Research:" in title_line or "Research:" in description:
            is_request = True
            request_type = "Research Request"
            
            # Find the research topic
            match = re.search(r'Research:\s*(.*)', title_line)
            if not match:
                match = re.search(r'Research:\s*(.*)', description)
                
            if match:
                topic = match.group(1).strip()
                request_name = topic
                print(f"  Research requested: {topic}")
                
                # Simple heuristic search in library/knowledge
                # First check if it's a direct path
                if topic.startswith("library/knowledge/"):
                    path = topic
                    if os.path.exists(path):
                        with open(path, 'r') as file:
                            content_to_send = file.read()
                    else:
                        content_to_send = f"File {path} not found."
                else:
                    # Grep in library/knowledge
                    # Search specifically for model deployment manifests or task ids
                    if "manifest" in topic.lower() or "deployment" in topic.lower() or "jetstream" in topic.lower() or "vllm" in topic.lower() or "gemma" in topic.lower():
                        # We try to find related manifests
                        cmd = f"grep -ri '{topic.split()[0]}' library/knowledge/manifests/"
                        res = run_cmd(cmd)
                        
                        # Fallback: find any file that matches the topic keywords in the filename
                        keywords = topic.replace("-", " ").replace("_", " ").split()
                        best_match = None
                        best_match_score = 0
                        
                        for root, dirs, files in os.walk("library/knowledge/"):
                            for file in files:
                                score = sum(1 for k in keywords if k.lower() in file.lower())
                                if score > best_match_score:
                                    best_match_score = score
                                    best_match = os.path.join(root, file)
                        
                        if best_match:
                            with open(best_match, 'r') as f:
                                content_to_send = f.read()
                        else:
                            content_to_send = f"Could not find specific research for: {topic}. Returning empty."
                    else:
                        content_to_send = f"Could not find specific research for: {topic}."
            else:
                content_to_send = "Could not parse research topic from the request."
        
        if is_request and content_to_send:
            # We must reply and close
            print(f"  Replying and closing {bead_id}...")
            
            # Escape content for bash
            escaped_content = content_to_send.replace('"', '\\"').replace('$', '\\$').replace('`', '\\`')
            
            reply_cmd = f'gc mail reply {bead_id} -m "{escaped_content}"'
            reply_result = run_cmd(reply_cmd)
            
            close_cmd = f'bd close {bead_id} --reason "Request fulfilled"'
            close_result = run_cmd(close_cmd)
            
            catalog_updates.append(f"- Fulfilled {request_type}: {request_name} for {bead_id}")
            processed_count += 1
            
    print(f"\nProcessed {processed_count} requests.")
    
    with open("catalog_updates.txt", "w") as f:
        f.write("\n".join(catalog_updates))

if __name__ == "__main__":
    process_messages()
