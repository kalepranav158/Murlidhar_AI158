from backend.services.analytics_engine import compute_analytics

def build_dashboard(user_id: str):
    return compute_analytics(user_id)

