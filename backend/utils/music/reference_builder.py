def phrase_to_reference(phrase):
    reference = []
    current_time = 0.0

    for note in phrase:
        reference.append({
            "note": note["note"],
            "time": current_time
        })
        current_time += note["duration"]

    return reference
