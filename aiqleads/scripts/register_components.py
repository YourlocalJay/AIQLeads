"""Script to register existing components in the project tracking system"""

from pathlib import Path
import sys

# Add project root to path
project_root = Path(__file__).parent.parent
sys.path.append(str(project_root.parent))

from aiqleads.core.project_tracking import ProjectTracker

def register_core_components():
    """Register core project components."""
    tracker = ProjectTracker()
    
    # Core AI Components
    core_components = [
        ("core", "core/ai_lead_scoring.py", {
            "purpose": "AI-Based Lead Valuation",
            "functionality": ["lead_scoring", "valuation", "ml_pipeline"]
        }),
        ("core", "core/ai_pricing_engine.py", {
            "purpose": "AI-Powered Dynamic Pricing",
            "functionality": ["pricing", "market_analysis", "value_prediction"]
        }),
        ("core", "core/ai_recommendation.py", {
            "purpose": "AI Lead Matching & Suggestions",
            "functionality": ["matching", "recommendations", "scoring"]
        }),
        ("core", "core/ai_market_analysis.py", {
            "purpose": "Market Trends & AI Predictions",
            "functionality": ["market_analysis", "trend_prediction", "insights"]
        }),
        ("core", "core/ai_monitoring.py", {
            "purpose": "AI Performance & Debugging",
            "functionality": ["monitoring", "debugging", "metrics"]
        }),
        ("core", "core/project_tracking.py", {
            "purpose": "Project Status Management",
            "functionality": ["tracking", "status", "metrics"]
        })
    ]
    
    # API Components
    api_components = [
        ("api", "api/v1/endpoints/leads.py", {
            "purpose": "AI-driven Lead Management API",
            "functionality": ["lead_management", "scoring", "routing"]
        }),
        ("api", "api/v1/endpoints/users.py", {
            "purpose": "User Authentication & Credits API",
            "functionality": ["auth", "credits", "user_management"]
        }),
        ("api", "api/v1/endpoints/analytics.py", {
            "purpose": "AI-Powered Insights API",
            "functionality": ["analytics", "reporting", "insights"]
        }),
        ("api", "api/v1/endpoints/chatbot.py", {
            "purpose": "AI Chatbot for Lead Queries",
            "functionality": ["chatbot", "nlp", "query_handling"]
        }),
        ("api", "api/v1/endpoints/market_trends.py", {
            "purpose": "AI Market Predictions API",
            "functionality": ["market_analysis", "predictions", "trends"]
        })
    ]
    
    # Register all components
    all_components = core_components + api_components
    
    for comp_type, comp_id, comp_def in all_components:
        if tracker.register_component(comp_type, comp_id, comp_def):
            # Update initial status based on UNIVERSAL_PROMPT statuses
            if comp_type == "core":
                tracker.update_status(comp_id, "🟡 In Progress", 
                                   "Initial registration from universal prompt")
            else:
                tracker.update_status(comp_id, "🔴 Not Started",
                                   "Initial registration from universal prompt")

if __name__ == "__main__":
    register_core_components()