from dtw.aligner import dtw_align
from evaluation.scorer import evaluate

# Reference phrase (Sa Re Ga Ma)
reference = [
    {"note": "Sa", "time": 0.0},
    {"note": "Re", "time": 0.5},
    {"note": "Ga", "time": 1.0},
    {"note": "Ma", "time": 1.5},
]

# Played phrase (Re skipped, extra Ga)
played = [
    {"note": "Sa", "cents": 5, "time": 0.1},
    {"note": "Ga", "cents": -10, "time": 0.7},
    {"note": "Ga", "cents": 3, "time": 1.0},
    {"note": "Ma", "cents": 2, "time": 1.6},
]

cost, alignment = dtw_align(reference, played)
result = evaluate(alignment)

print("DTW Cost:", round(cost, 3))
print("\nAlignment:")
for ref, play in alignment:
    print(f"{ref['note']}  ←→  {play['note']}")

print("\nEvaluation:")
for k, v in result.items():
    print(f"{k}: {v}")
