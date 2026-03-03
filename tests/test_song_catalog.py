import json
from pathlib import Path


def test_alankar_catalog_unlock_chain_integrity():
    songs_dir = Path("songs")
    expected_ids = [f"alankar_{index}" for index in range(1, 11)]

    loaded = {}
    for alankar_id in expected_ids:
        file_path = songs_dir / f"{alankar_id}.json"
        assert file_path.exists(), f"Missing file: {file_path}"

        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        loaded[alankar_id] = payload

    for index, alankar_id in enumerate(expected_ids):
        payload = loaded[alankar_id]
        assert payload.get("id") == alankar_id, f"id mismatch in {alankar_id}.json"

        expected_next = expected_ids[index + 1] if index < len(expected_ids) - 1 else None
        assert payload.get("unlock_next") == expected_next, (
            f"unlock_next mismatch for {alankar_id}: "
            f"expected {expected_next}, got {payload.get('unlock_next')}"
        )
