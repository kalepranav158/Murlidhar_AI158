from app.services.llm.feedback_llm import _normalize_llm_feedback


def test_llm_feedback_normalization():
    feedback = {
        "pitch_stability_score": 50,
        "rhythm_stability_score": 25,
        "other": "irrelevant"
    }
    normalized = _normalize_llm_feedback(feedback.copy())
    assert normalized["pitch_stability_score"] == 0.5
    assert normalized["rhythm_stability_score"] == 0.25
    # other keys should remain untouched
    assert normalized["other"] == "irrelevant"
