from app.services.analytics_engine import compute_analytics

def build_analytics_context(user_id: str):

    data = compute_analytics(user_id)

    if not data:
        return ""

    return f"""
Analytics Summary:
Average Accuracy: {data['summary']['average_accuracy']}%
Average Pitch Error: {data['summary']['average_pitch_error']} cents
Average Timing Error: {data['summary']['average_timing_error']} sec

Trend: {data['trend']['classification']}
Trend Slope: {data['trend']['slope']}

Composite Skill Score: {data['indices']['composite_score']}

Pitch Stability Index: {data['indices']['pitch_index']}
Rhythm Stability Index: {data['indices']['rhythm_index']}
Consistency Index: {data['indices']['consistency_index']}

Plateau Detected: {data['flags']['plateau']}
Performance Risk Detected: {data['flags']['risk']}

Predicted Next Accuracy: {data['prediction']['next_accuracy']}%
"""
