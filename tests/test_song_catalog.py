import json
from pathlib import Path

from music.song_loader import infer_content_type


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


def test_melody_catalog_unlock_chain_integrity():
    songs_dir = Path("songs")
    expected_ids = [f"melody_{index}" for index in range(1, 4)]

    loaded = {}
    for melody_id in expected_ids:
        file_path = songs_dir / f"{melody_id}.json"
        assert file_path.exists(), f"Missing file: {file_path}"

        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        loaded[melody_id] = payload

    for index, melody_id in enumerate(expected_ids):
        payload = loaded[melody_id]
        assert payload.get("id") == melody_id, f"id mismatch in {melody_id}.json"
        assert payload.get("type") == "melody", f"type mismatch in {melody_id}.json"

        expected_next = expected_ids[index + 1] if index < len(expected_ids) - 1 else None
        assert payload.get("unlock_next") == expected_next, (
            f"unlock_next mismatch for {melody_id}: "
            f"expected {expected_next}, got {payload.get('unlock_next')}"
        )


def test_melody_catalog_content_type_inference():
    songs_dir = Path("songs")
    melody_files = sorted(songs_dir.glob("melody_*.json"))
    assert melody_files, "Expected at least one melody JSON file"

    for file_path in melody_files:
        with file_path.open("r", encoding="utf-8") as handle:
            payload = json.load(handle)

        content_id = payload.get("id")
        assert infer_content_type(payload, content_id) == "melody", (
            f"inferred content type mismatch in {file_path.name}"
        )
