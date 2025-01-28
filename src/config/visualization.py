# Tile configuration
TILE_SIZE = 256  # Standard tile size in pixels
MAX_ZOOM_LEVEL = 18  # Maximum zoom level for tile generation

# Heatmap configuration
DEFAULT_GRID_SIZE = 1000  # Default grid size in meters
HEATMAP_COLOR_STOPS = [
    {'value': 0, 'color': '#93C5FD'},  # Light blue
    {'value': 0.2, 'color': '#60A5FA'},
    {'value': 0.4, 'color': '#3B82F6'},
    {'value': 0.6, 'color': '#2563EB'},
    {'value': 0.8, 'color': '#1E40AF'}  # Dark blue
]

# Cluster configuration
DEFAULT_CLUSTER_RADIUS = 5000  # Default cluster radius in meters
MIN_CLUSTER_SIZE = 5  # Minimum points to form a cluster
CLUSTER_COLORS = [
    '#3B82F6',  # blue
    '#EF4444',  # red
    '#10B981',  # green
    '#F59E0B',  # yellow
    '#8B5CF6',  # purple
    '#EC4899',  # pink
    '#14B8A6',  # teal
    '#F97316',  # orange
    '#6366F1',  # indigo
    '#06B6D4'   # cyan
]

# Cache configuration
DEFAULT_CACHE_TTL = 3600  # 1 hour
CACHE_KEY_PREFIX = 'geospatial'

# Performance tuning
MAX_POINTS_PER_TILE = 1000  # Maximum points to render per tile
SIMPLIFICATION_TOLERANCE = 0.0001  # Tolerance for polygon simplification

# Predictive analysis configuration
DEFAULT_PREDICTION_WINDOW = 30  # days
MIN_CONFIDENCE_THRESHOLD = 0.7  # Minimum R-squared value for predictions
MIN_DATA_POINTS = 14  # Minimum number of data points for prediction

# Competitor analysis configuration
DEFAULT_COMPETITOR_RADIUS = 5000  # meters
MAX_COMPETITORS_PER_LEAD = 10  # Maximum number of competitors to track per lead

# WebSocket configuration
WS_UPDATE_INTERVAL = 30  # seconds
BATCH_SIZE = 100  # Number of updates to batch

# Layer configuration
AVAILABLE_LAYERS = {
    'density': {
        'name': 'Lead Density',
        'description': 'Shows concentration of leads in the area',
        'default_enabled': True,
        'update_frequency': 300  # 5 minutes
    },
    'clusters': {
        'name': 'Lead Clusters',
        'description': 'Groups of leads in close proximity',
        'default_enabled': True,
        'update_frequency': 600  # 10 minutes
    },
    'competitors': {
        'name': 'Competitor Analysis',
        'description': 'Shows competitor locations and influence',
        'default_enabled': False,
        'update_frequency': 900  # 15 minutes
    },
    'predictions': {
        'name': 'Predictive Trends',
        'description': 'Future density predictions based on historical data',
        'default_enabled': False,
        'update_frequency': 3600  # 1 hour
    }
}

# Monitoring configuration
METRICS_LABELS = [
    'region',
    'visualization_type',
    'grid_size',
    'zoom_level'
]

PERFORMANCE_THRESHOLDS = {
    'heatmap_generation': 2.0,  # seconds
    'cluster_generation': 1.5,  # seconds
    'cache_hit_rate': 0.8,  # minimum acceptable rate
    'query_time': 1.0  # seconds
}