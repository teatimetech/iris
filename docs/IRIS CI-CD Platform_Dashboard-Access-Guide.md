# Dashboard Access Guide - IRIS CI/CD Platform

Complete guide for accessing all monitoring, observability, and GitOps dashboards.

## Quick Reference

| Dashboard | Default Port | URL | Username | Password Command |
|-----------|--------------|-----|----------|------------------|
| **Argo CD** | 8080 | https://localhost:8080 | admin | See below |
| **Grafana** | 3000 | http://localhost:3000 | admin | See below |
| **Prometheus** | 9090 | http://localhost:9090 | - | No auth |
| **Alertmanager** | 9093 | http://localhost:9093 | - | No auth |

---

## 1. Argo CD Dashboard

Argo CD provides GitOps continuous delivery and application management.

### Access Steps

#### Step 1: Get Admin Password

```powershell
# Windows PowerShell
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

```bash
# macOS/Linux
kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath="{.data.password}" | base64 -d
echo
```

**Save this password** - you'll need it to log in.

#### Step 2: Port Forward

```bash
# Forward Argo CD server to localhost
kubectl port-forward svc/argocd-server -n argocd 8080:443
```

**Keep this terminal open** - closing it will stop the port forward.

#### Step 3: Access UI

1. Open browser: **https://localhost:8080**
2. **Accept security warning** (self-signed certificate)
   - Chrome: Click "Advanced" → "Proceed to localhost (unsafe)"
   - Firefox: Click "Advanced" → "Accept the Risk and Continue"
   - Edge: Click "Advanced" → "Continue to localhost (unsafe)"
3. Login:
   - **Username**: `admin`
   - **Password**: (from Step 1)

### What You'll See

- **Applications**: All deployed IRIS services (5 applications)
- **Projects**: IRIS project with RBAC policies
- **Settings**: Repository connections, clusters, accounts
- **User Info**: Current user and RBAC permissions

### Key Features

#### View Application Details
1. Click on an application (e.g., `iris-api-gateway-dev`)
2. See:
   - Sync status (Synced/OutOfSync)
   - Health status (Healthy/Progressing/Degraded)
   - Resources (Deployments, Services, Pods, etc.)
   - Git commit info

#### Manual Sync
1. Click "SYNC" button
2. Select sync options (Prune, Dry Run, etc.)
3. Click "SYNCHRONIZE"

#### View Deployment History
1. Click application
2. Go to "History and Rollback" tab
3. See all previous deployments
4. Rollback to any previous version

#### View Logs
1. Click on a Pod resource
2. Click "LOGS" tab
3. Stream real-time logs

### Troubleshooting

**Can't access UI:**
- Check port forward is running
- Try different port: `kubectl port-forward svc/argocd-server -n argocd 8081:443`
- Access at https://localhost:8081

**Forgot password:**
```bash
# Reset to initial password
kubectl -n argocd delete secret argocd-initial-admin-secret
# Restart argocd-server pod to regenerate
kubectl -n argocd delete pod -l app.kubernetes.io/name=argocd-server
```

---

## 2. Grafana Dashboard

Grafana provides visualization and dashboards for metrics from Prometheus.

### Access Steps

#### Step 1: Get Admin Password

```powershell
# Windows PowerShell
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | ForEach-Object { [System.Text.Encoding]::UTF8.GetString([System.Convert]::FromBase64String($_)) }
```

```bash
# macOS/Linux
kubectl get secret -n monitoring prometheus-grafana -o jsonpath="{.data.admin-password}" | base64 -d
echo
```

#### Step 2: Port Forward

```bash
# Forward Grafana to localhost
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80
```

#### Step 3: Access UI

1. Open browser: **http://localhost:3000**
2. Login:
   - **Username**: `admin`
   - **Password**: (from Step 1)

### Pre-installed Dashboards

The Prometheus stack comes with many pre-configured dashboards:

#### Kubernetes Dashboards
1. **Kubernetes / Compute Resources / Cluster**
   - Overall cluster CPU, Memory, Network usage
   - Node resource utilization

2. **Kubernetes / Compute Resources / Namespace (Pods)**
   - Per-namespace resource usage
   - Select namespace: `iris-dev`, [argocd](file:///c:/ai_IRIS/IRIS/scripts/deploy-argocd.py#117-161), `monitoring`

3. **Kubernetes / Compute Resources / Pod**
   - Per-pod metrics
   - Container CPU/Memory usage

4. **Kubernetes / Networking / Cluster**
   - Network I/O across the cluster
   - Packet rates, bandwidth

#### System Dashboards
5. **Node Exporter / Nodes**
   - Detailed node metrics (CPU, disk, network)
   
6. **AlertManager Overview**
   - Active alerts
   - Alert history

### Creating Custom Dashboards

#### For IRIS Applications

1. Go to **Dashboards** → **New** → **New Dashboard**
2. Add Panel
3. Query Prometheus data:
   ```promql
   # CPU usage for iris-api-gateway
   rate(container_cpu_usage_seconds_total{namespace="iris-dev",pod=~"iris-api-gateway.*"}[5m])
   
   # Memory usage
   container_memory_working_set_bytes{namespace="iris-dev",pod=~"iris-api-gateway.*"}
   
   # HTTP request rate (if metrics exposed)
   rate(http_requests_total{namespace="iris-dev"}[5m])
   ```

4. **Save dashboard** (give it a name like "IRIS Services")

### Exploring Metrics

1. Click **Explore** (compass icon)
2. Select **Prometheus** as data source
3. Use **Metrics browser** to find available metrics
4. Build queries visually or write PromQL

### Alert Configuration

1. Go to **Alerting** → **Alert rules**
2. Create new alert rule
3. Example: Alert if pod is down
   ```promql
   kube_pod_status_phase{namespace="iris-dev",phase!="Running"} == 1
   ```

---

## 3. Prometheus Dashboard

Prometheus provides the metrics database and query interface.

### Access Steps

#### Port Forward

```bash
# Forward Prometheus to localhost
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

#### Access UI

1. Open browser: **http://localhost:9090**
2. **No authentication required**

### Key Features

#### Query Metrics (Graph Tab)

1. Go to **Graph** tab
2. Enter PromQL query:
   ```promql
   # All metrics for iris-dev namespace
   {namespace="iris-dev"}
   
   # CPU usage
   rate(container_cpu_usage_seconds_total{namespace="iris-dev"}[5m])
   
   # Memory usage
   container_memory_usage_bytes{namespace="iris-dev"}
   
   # Pod count
   count(kube_pod_info{namespace="iris-dev"})
   ```

3. Click **Execute**
4. View as **Graph** or **Table**

#### Explore Available Metrics

1. Click **Insert metric at cursor** (dropdown)
2. Browse all available metrics
3. Prometheus auto-discovers metrics from:
   - Kubernetes components
   - Node exporters
   - Any pods with `/metrics` endpoint
   - ServiceMonitor resources

#### View Targets

1. Go to **Status** → **Targets**
2. See all scrape targets:
   - Kubernetes API server
   - Kubelets
   - ServiceMonitors (including IRIS services if configured)
   - Status (UP/DOWN)

#### Service Discovery

1. Go to **Status** → **Service Discovery**
2. See discovered services and pods
3. Verify IRIS services are discovered

### Common Queries for IRIS

```promql
# Pods running in iris-dev
count(kube_pod_info{namespace="iris-dev"})

# Containers restarting
increase(kube_pod_container_status_restarts_total{namespace="iris-dev"}[1h])

# Network receive bytes
rate(container_network_receive_bytes_total{namespace="iris-dev"}[5m])

# Disk usage
kubelet_volume_stats_used_bytes{namespace="iris-dev"}

# API server requests
rate(apiserver_request_total{namespace="iris-dev"}[5m])
```

---

## 4. Alertmanager Dashboard

Alertmanager handles alerts from Prometheus and routes them to receivers.

### Access Steps

#### Port Forward

```bash
# Forward Alertmanager to localhost
kubectl port-forward -n monitoring svc/alertmanager-prometheus-kube-prometheus-alertmanager 9093:9093
```

#### Access UI

1. Open browser: **http://localhost:9093**
2. **No authentication required**

### Features

#### View Active Alerts

1. Main page shows all **active alerts**
2. Filter by:
   - Severity (critical, warning, info)
   - Alertname
   - Labels

#### Silence Alerts

1. Click **New Silence**
2. Set:
   - Duration (1h, 2h, 1d, etc.)
   - Matchers (which alerts to silence)
   - Comment (reason for silencing)
3. Create silence

#### Alert Groups

1. Alerts are grouped by:
   - Cluster
   - Namespace
   - Alertname

---

## 5. Port Forwarding Management

### Running Multiple Dashboards Simultaneously

**Option 1: Multiple Terminal Windows**

Open separate terminal windows for each:

```bash
# Terminal 1: Argo CD
kubectl port-forward svc/argocd-server -n argocd 8080:443

# Terminal 2: Grafana
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Terminal 3: Prometheus
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090

# Terminal 4: Alertmanager
kubectl port-forward -n monitoring svc/alertmanager-prometheus-kube-prometheus-alertmanager 9093:9093
```

**Option 2: Background Processes (Linux/macOS)**

```bash
# Start all in background
kubectl port-forward svc/argocd-server -n argocd 8080:443 &
kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 &
kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 &
kubectl port-forward -n monitoring svc/alertmanager-prometheus-kube-prometheus-alertmanager 9093:9093 &

# List background jobs
jobs

# Kill specific job
kill %1  # Kill job number 1

# Kill all
killall kubectl
```

**Option 3: PowerShell (Windows)**

```powershell
# Start in background jobs
Start-Job -ScriptBlock { kubectl port-forward svc/argocd-server -n argocd 8080:443 }
Start-Job -ScriptBlock { kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80 }
Start-Job -ScriptBlock { kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090 }
Start-Job -ScriptBlock { kubectl port-forward -n monitoring svc/alertmanager-prometheus-kube-prometheus-alertmanager 9093:9093 }

# List jobs
Get-Job

# Stop job
Stop-Job -Name Job1

# Remove completed jobs
Remove-Job *
```

### Using Ingress Instead (Advanced)

For permanent access without port-forwarding, configure Kubernetes Ingress:

```yaml
# Example: argocd-ingress.yaml
apiVersion: networking.k8s.io/v1
kind: Ingress
metadata:
  name: argocd-server
  namespace: argocd
spec:
  rules:
  - host: argocd.local
    http:
      paths:
      - path: /
        pathType: Prefix
        backend:
          service:
            name: argocd-server
            port:
              number: 443
```

Then add to `/etc/hosts` (macOS/Linux) or [C:\Windows\System32\drivers\etc\hosts](file:///Windows/System32/drivers/etc/hosts) (Windows):
```
127.0.0.1 argocd.local grafana.local prometheus.local
```

---

## 6. Accessing IRIS Application Services

Once IRIS applications are deployed:

### Web UI

```bash
kubectl port-forward -n iris-dev svc/iris-web-ui 3001:3000
# Access: http://localhost:3001
```

### API Gateway

```bash
kubectl port-forward -n iris-dev svc/iris-api-gateway 8081:8080
# Access: http://localhost:8081

# Test
curl http://localhost:8081/health
```

### Agent Router

```bash
kubectl port-forward -n iris-dev svc/iris-agent-router 8001:8000
# Access: http://localhost:8001
```

---

## 7. Makefile Shortcuts

Add to your [Makefile](file:///c:/ai_IRIS/IRIS/Makefile) for easy access:

```makefile
# Port forward to Argo CD
.PHONY: argocd-ui
argocd-ui:
	@echo "Argo CD UI: https://localhost:8080"
	@echo "Username: admin"
	@echo "Password: $$(kubectl -n argocd get secret argocd-initial-admin-secret -o jsonpath='{.data.password}' | base64 -d)"
	kubectl port-forward svc/argocd-server -n argocd 8080:443

# Port forward to Grafana
.PHONY: grafana-ui
grafana-ui:
	@echo "Grafana UI: http://localhost:3000"
	@echo "Username: admin"
	@echo "Password: $$(kubectl get secret -n monitoring prometheus-grafana -o jsonpath='{.data.admin-password}' | base64 -d)"
	kubectl port-forward -n monitoring svc/prometheus-grafana 3000:80

# Port forward to Prometheus
.PHONY: prometheus-ui
prometheus-ui:
	@echo "Prometheus UI: http://localhost:9090"
	kubectl port-forward -n monitoring svc/prometheus-kube-prometheus-prometheus 9090:9090
```

Then use:
```bash
make argocd-ui
make grafana-ui  
make prometheus-ui
```

---

## 8. Troubleshooting

### Port Already in Use

```bash
# Find process using port 8080
netstat -ano | findstr :8080  # Windows
lsof -i :8080  # macOS/Linux

# Kill process
taskkill /PID <pid> /F  # Windows
kill -9 <pid>  # macOS/Linux

# Or use different port
kubectl port-forward svc/argocd-server -n argocd 8081:443
```

### Connection Refused

1. Check pod is running:
   ```bash
   kubectl get pods -n argocd
   kubectl get pods -n monitoring
   ```

2. Check service exists:
   ```bash
   kubectl get svc -n argocd
   kubectl get svc -n monitoring
   ```

3. Restart port-forward

### Can't Access from Browser

1. Check port-forward is running (terminal should show "Forwarding from...")
2. Try `127.0.0.1` instead of `localhost`
3. Clear browser cache
4. Try different browser

---

## Summary

You now have access to:
- ✅ **Argo CD**: GitOps application deployment and management
- ✅ **Grafana**: Metrics visualization and dashboards
- ✅ **Prometheus**: Metrics database and queries
- ✅ **Alertmanager**: Alert management and routing

All running locally via port-forwarding to your Kubernetes cluster!
