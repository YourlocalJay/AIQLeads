# Schema Validation Monitoring System

## Overview
The schema validation monitoring system provides real-time visibility into validation performance, cache efficiency, and error rates. This documentation covers system setup, configuration, and maintenance procedures.

## Key Components

### Metrics Collection
The system tracks three primary metric categories:

1. Validation Performance
   - Processing duration (target: <10ms)
   - Error rates by endpoint and type
   - Schema version tracking

2. Cache Performance
   - Hit ratio (target: >85%)
   - Operation counts by type
   - Cache efficiency metrics

3. System Health
   - Resource utilization
   - Alert status
   - Integration health

## Implementation Guide

### Prerequisites
```python
pip install prometheus_client
pip install grafana-client
```

### Basic Setup
1. Initialize the metrics collector:
   ```python
   from monitoring.schema_monitoring import SchemaMetrics
   
   metrics = SchemaMetrics()
   ```

2. Implement the monitoring decorator:
   ```python
   @monitor_schema_validation(endpoint='/api/v1/leads')
   async def validate_lead_schema(data: Dict[str, Any]):
       # Validation logic here
       pass
   ```

### Dashboard Configuration

1. Import the provided dashboard:
   - Navigate to Grafana UI
   - Import dashboard from `config/monitoring/grafana-dashboard.json`
   - Set data source to your Prometheus instance

2. Configure alerts:
   - Apply alert rules from `config/monitoring/alert-rules.yaml`
   - Verify PagerDuty and Slack integrations
   - Test notification routing

## Performance Tuning

### Cache Optimization
1. Monitor cache hit ratio:
   - Review `Cache Hit Ratio` panel in Grafana
   - Investigate if ratio drops below 85%
   - Adjust cache size or TTL as needed

2. Validation Performance:
   - Track duration metrics by endpoint
   - Investigate endpoints exceeding 10ms threshold
   - Optimize validation logic where needed

## Alert Management

### Critical Alerts
Immediate action required for:
- Validation latency >10ms for 5 minutes
- Cache hit rate <85% for 10 minutes
- Error rate exceeding 100/5min

### Warning Alerts
Monitor and investigate:
- Validation latency spikes
- Declining cache performance
- Increased error rates

## Maintenance Procedures

### Daily Tasks
1. Review dashboard metrics
2. Verify alert configurations
3. Check integration status

### Weekly Tasks
1. Analyze performance trends
2. Review and update thresholds
3. Validate backup systems

### Monthly Tasks
1. Comprehensive performance review
2. Update documentation as needed
3. Test disaster recovery procedures

## Troubleshooting Guide

### Common Issues

1. High Validation Latency
   ```python
   # Check validation time distribution
   rate(schema_validation_duration_seconds_sum[5m]) / 
   rate(schema_validation_duration_seconds_count[5m])
   ```
   - Review validation logic complexity
   - Check system resources
   - Verify cache performance

2. Low Cache Hit Rate
   ```python
   # Monitor cache operations
   sum(rate(schema_cache_operations_total{status="hit"}[5m])) / 
   sum(rate(schema_cache_operations_total[5m]))
   ```
   - Verify cache configuration
   - Review cache invalidation logic
   - Check memory allocation

3. High Error Rates
   - Review error patterns in logs
   - Check schema version consistency
   - Verify client request formats

## Best Practices

### Development Guidelines
1. Always use the monitoring decorator
2. Maintain test coverage for metrics
3. Document performance impacts
4. Version control configuration

### Operational Guidelines
1. Regular metric review
2. Proactive threshold adjustment
3. Consistent alert response
4. Performance trend analysis

## Integration Points

### Prometheus
- Metric collection endpoint: `/metrics`
- Scrape interval: 15s
- Retention period: 15d

### Grafana
- Dashboard refresh: 10s
- Default time range: 1h
- Alert evaluation interval: 1m

### Alert Routing
- Critical: PagerDuty
- Warning: Slack
- Info: Logging system

## Version Control
All monitoring configurations are version controlled:
- `src/monitoring/` - Core implementation
- `config/monitoring/` - Configuration files
- `tests/monitoring/` - Test suite

## Support and Escalation

### Level 1 Support
- Monitor dashboard
- Respond to warnings
- Basic troubleshooting

### Level 2 Support
- Performance optimization
- Alert tuning
- Integration issues

### Level 3 Support
- System architecture
- Custom implementations
- Capacity planning