"""
AI-focused monitoring system with token tracking, cost analysis,
and regional performance insights.
"""
[Previous code remains the same until the decorator...]

def track_ai_operation(model_name: str, region: Optional[str] = None):
    """Decorator for tracking AI operations."""
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            start_time = datetime.now()
            operation_id = f"{model_name}_{start_time.timestamp()}"
            success = True
            error_type = None
            lead_id = kwargs.get('lead_id')
            
            try:
                result = await func(*args, **kwargs)
                
                # Extract metrics from result if available
                if isinstance(result, tuple) and len(result) == 2:
                    result, operation_metrics = result
                else:
                    operation_metrics = {}
                
                # Create metrics object
                metric = AIOperationMetrics(
                    operation_id=operation_id,
                    model_name=model_name,
                    prompt_tokens=operation_metrics.get('prompt_tokens', 0),
                    completion_tokens=operation_metrics.get('completion_tokens', 0),
                    total_tokens=operation_metrics.get('total_tokens', 0),
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    cost=operation_metrics.get('cost', 0.0),
                    success=success,
                    error_type=error_type,
                    lead_id=lead_id,
                    region=region or kwargs.get('region'),
                    prompt_chars=operation_metrics.get('prompt_chars'),
                    response_chars=operation_metrics.get('response_chars'),
                    cache_hit=operation_metrics.get('cache_hit', False)
                )
                
                # Record metrics
                await monitor.record_operation(metric)
                
                return result
                
            except Exception as e:
                success = False
                error_type = e.__class__.__name__
                
                # Record failure metrics
                metric = AIOperationMetrics(
                    operation_id=operation_id,
                    model_name=model_name,
                    prompt_tokens=0,
                    completion_tokens=0,
                    total_tokens=0,
                    duration_ms=(datetime.now() - start_time).total_seconds() * 1000,
                    cost=0.0,
                    success=success,
                    error_type=error_type,
                    lead_id=lead_id,
                    region=region or kwargs.get('region')
                )
                
                await monitor.record_operation(metric)
                raise
                
        return wrapper
    return decorator