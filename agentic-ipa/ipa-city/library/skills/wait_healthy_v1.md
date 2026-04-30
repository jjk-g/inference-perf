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
   Use `curl` or a similar tool to check the `/health` or `/v1/models` endpoint of the service.
   Example:
   ```bash
   kubectl proxy &
   PID=$!
   sleep 2
   curl http://localhost:8001/api/v1/namespaces/default/services/<service-name>:http/proxy/health
   kill $PID
   ```
   *Note: Adjust the port and path based on your environment.*
