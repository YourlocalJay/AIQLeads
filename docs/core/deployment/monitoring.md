# Monitoring System Setup

## Components

### 1. Metrics Collection

#### Prometheus Configuration
```yaml
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - alertmanager:9093

rule_files:
  - /etc/prometheus/rules/*.yml

scrape_configs:
  - job_name: 'aiqleads'
    metrics_path: '/metrics'
    static_configs:
      - targets: ['localhost:8000']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['localhost:9100']

  - job_name: 'redis-exporter'
    static_configs:
      - targets: ['localhost:9121']
```

#### Alert Rules
```yaml
groups:
  - name: aiqleads_alerts
    rules:
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.05
        for: 5m
        labels:
          severity: critical
        annotations:
          summary: High error rate detected
          description: Error rate is above 5% for 5 minutes

      - alert: SlowResponses
        expr: http_request_duration_seconds{quantile="0.9"} > 1
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: Slow response times detected
          description: 90th percentile of response times is above 1 second
```

### 2. Monitoring Dashboard

#### Grafana Setup
```bash
# Install Grafana
sudo apt-get install -y software-properties-common
sudo add-apt-repository "deb https://packages.grafana.com/oss/deb stable main"
sudo apt-get update
sudo apt-get install grafana

# Start Grafana
sudo systemctl start grafana-server
sudo systemctl enable grafana-server
```

#### Dashboard Configuration
```json
{
  "dashboard": {
    "id": null,
    "title": "AIQLeads System Monitor",
    "tags": ["aiqleads"],
    "timezone": "browser",
    "panels": [
      {
        "title": "Request Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total[5m])"
          }
        ]
      },
      {
        "title": "Error Rate",
        "type": "graph",
        "datasource": "Prometheus",
        "targets": [
          {
            "expr": "rate(http_requests_total{status=~\"5..\"}[5m])"
          }
        ]
      }
    ]
  }
}
```

### 3. Alerting System

#### AlertManager Configuration
```yaml
global:
  resolve_timeout: 5m
  slack_api_url: 'https://hooks.slack.com/services/YOUR/SLACK/WEBHOOK'

route:
  group_by: ['alertname', 'instance']
  group_wait: 30s
  group_interval: 5m
  repeat_interval: 4h
  receiver: 'slack-notifications'

receivers:
  - name: 'slack-notifications'
    slack_configs:
      - channel: '#alerts'
        send_resolved: true
        icon_emoji: ':warning:'
        title: '{{ range .Alerts }}{{ .Annotations.summary }}{{ end }}'
        text: '{{ range .Alerts }}{{ .Annotations.description }}{{ end }}'
```

## Health Check Integration

### Application Health Checks
```python
@app.route('/health')
async def health_check():
    checks = {
        'database': check_database_health(),
        'redis': check_redis_health(),
        'api': check_api_health()
    }
    
    all_healthy = all(check['status'] == 'healthy' for check in checks.values())
    
    return {
        'status': 'healthy' if all_healthy else 'unhealthy',
        'checks': checks,
        'timestamp': datetime.utcnow().isoformat()
    }
```

### Monitoring Integration
```python
class SystemMonitor:
    def __init__(self):
        self.metrics = PrometheusMetrics(app)
        self.setup_metrics()

    def setup_metrics(self):
        # Request metrics
        self.metrics.info('app_info', 'Application info', version='1.0.0')
        self.metrics.counter('http_requests_total', 'Total HTTP requests',
                            labels={'status': lambda r: r.status_code})
        self.metrics.histogram('http_request_duration_seconds', 'HTTP request duration',
                              labels={'path': lambda: request.path})

        # Business metrics
        self.metrics.gauge('active_leads', 'Number of active leads')
        self.metrics.histogram('lead_processing_time', 'Lead processing duration')
        self.metrics.counter('leads_processed_total', 'Total processed leads')

        # System metrics
        self.metrics.gauge('system_memory_usage', 'System memory usage')
        self.metrics.gauge('system_cpu_usage', 'System CPU usage')
```

## Deployment Steps

1. Install Monitoring Stack
```bash
# Install Prometheus
wget https://github.com/prometheus/prometheus/releases/download/v2.30.3/prometheus-2.30.3.linux-amd64.tar.gz
tar xvf prometheus-2.30.3.linux-amd64.tar.gz
sudo mv prometheus-2.30.3.linux-amd64 /usr/local/bin/prometheus

# Install Node Exporter
wget https://github.com/prometheus/node_exporter/releases/download/v1.2.2/node_exporter-1.2.2.linux-amd64.tar.gz
tar xvf node_exporter-1.2.2.linux-amd64.tar.gz
sudo mv node_exporter-1.2.2.linux-amd64 /usr/local/bin/node_exporter

# Install AlertManager
wget https://github.com/prometheus/alertmanager/releases/download/v0.23.0/alertmanager-0.23.0.linux-amd64.tar.gz
tar xvf alertmanager-0.23.0.linux-amd64.tar.gz
sudo mv alertmanager-0.23.0.linux-amd64 /usr/local/bin/alertmanager
```

2. Configure Services
```bash
# Copy configuration files
sudo mkdir -p /etc/prometheus
sudo cp prometheus.yml /etc/prometheus/
sudo cp alertmanager.yml /etc/alertmanager/

# Create systemd services
sudo cp prometheus.service /etc/systemd/system/
sudo cp alertmanager.service /etc/systemd/system/
sudo cp node_exporter.service /etc/systemd/system/

# Start services
sudo systemctl daemon-reload
sudo systemctl start prometheus alertmanager node_exporter
sudo systemctl enable prometheus alertmanager node_exporter
```

3. Verify Installation
```bash
# Check Prometheus
curl localhost:9090/-/healthy

# Check AlertManager
curl localhost:9093/-/healthy

# Check Node Exporter
curl localhost:9100/metrics
```