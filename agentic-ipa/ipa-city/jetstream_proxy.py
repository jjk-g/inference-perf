
import json
import http.server
import urllib.request

class ProxyHandler(http.server.BaseHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/v1/models':
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({"data": [{"id": "llama-3"}]}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_POST(self):
        if self.path == '/v1/completions':
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            data = json.loads(post_data)
            
            jetstream_data = {
                "prompt": data.get("prompt"),
                "max_tokens": data.get("max_tokens", 100),
            }
            
            req = urllib.request.Request(
                "http://localhost:8004/generate",
                data=json.dumps(jetstream_data).encode(),
                headers={"Content-Type": "application/json"},
                method='POST'
            )
            
            with urllib.request.urlopen(req) as response:
                resp_data = json.loads(response.read().decode())
                
            openai_resp = {
                "choices": [{"text": resp_data.get("response")}],
                "usage": {"prompt_tokens": 0, "completion_tokens": 0, "total_tokens": 0}
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(openai_resp).encode())
        else:
            self.send_response(404)
            self.end_headers()

if __name__ == '__main__':
    server = http.server.HTTPServer(('localhost', 8003), ProxyHandler)
    print("Proxy running on port 8003")
    server.serve_forever()
