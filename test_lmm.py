from app.services.llm_client import generate_guru_feedback

dummy_result = {
    "note_accuracy": 82.5,
    "avg_pitch_error_cents": 24.3,
    "avg_timing_error_sec": 0.42,
    "mistakes": [{"expected": "Madhya Ga", "played": "Madhya Komal Ga"}]
}

response = generate_guru_feedback(dummy_result)

print("\n--- Gemini Response ---\n")
print(response)
