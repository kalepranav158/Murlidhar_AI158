MIN_NOTE_DURATION = 0.15  # seconds

class NoteSegmenter:
    def __init__(self):
        self.confirmed_note = None
        self.candidate_note = None
        self.candidate_start = None
        self.notes = []

    def process(self, note, cents, time_now):
        # FIRST NOTE: initialize candidate
        if self.confirmed_note is None:
            self.confirmed_note = note
            self.notes.append({
                "note": note,
                "cents": cents,
                "time": round(time_now, 2)
            })
            return

        # Same as confirmed note → ignore (vibrato)
        if note == self.confirmed_note:
            self.candidate_note = None
            self.candidate_start = None
            return

        # New candidate note
        if self.candidate_note != note:
            self.candidate_note = note
            self.candidate_start = time_now
            return

        # Candidate is stable long enough → confirm
        if time_now - self.candidate_start >= MIN_NOTE_DURATION:
            self.confirmed_note = note
            self.candidate_note = None
            self.candidate_start = None
            self.notes.append({
                "note": note,
                "cents": cents,
                "time": round(time_now, 2)
            })

    def get_notes(self):
        return self.notes
