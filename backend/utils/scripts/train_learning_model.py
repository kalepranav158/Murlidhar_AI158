from backend.services.learning_engine import train_and_persist_learning_model


if __name__ == "__main__":
    artifact = train_and_persist_learning_model(limit=1000, minimum_pairs=8)
    metrics = artifact.get("metrics", {})
    print(
        {
            "status": "ok",
            "sample_pairs": metrics.get("sample_pairs"),
            "mae": metrics.get("mae"),
            "reason": metrics.get("reason"),
        }
    )

