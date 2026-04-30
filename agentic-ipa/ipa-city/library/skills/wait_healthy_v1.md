# Wait Healthy Skill

This skill describes how to wait for a deployed model server to be healthy and ready.

## Prerequisites
- `kubectl` configured.
- The name of the deployment or service to check.

## Process
1. **Wait for deployment rollout**:
   ```bash
   kubectl rollout status deployment/<deployment-name>
   ```

2. **Check health endpoint**:
   Use `curl` or a similar tool to check the health endpoint (usually `/health` or `/v1/models`).

   **Port naming**: If the service does not have a named port (e.g., `http`), use the port number directly in the proxy URL. **Avoid using port 8001** as it is frequently in use; instead, use a unique port like `8002` or `8003`.

   Example:
   ```bash
   kubectl proxy --port=8002 &
   PID=$!
   sleep 2
   # Using port name 'http'
   curl http://localhost:8002/api/v1/namespaces/default/services/<service-name>:http/proxy/health
   # OR using port number 8000
   curl http://localhost:8002/api/v1/namespaces/default/services/<service-name>:8000/proxy/health
   # Alternative endpoint
   curl http://localhost:8002/api/v1/namespaces/default/services/<service-name>:8000/proxy/v1/models
   kill $PID
   ```
   *Note: Adjust the port and path based on your environment. Some health endpoints may return 200 OK with an empty body; check the status code.*
