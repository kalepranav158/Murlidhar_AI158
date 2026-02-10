MIN_NOTE_DURATION = 0.15  # seconds

class NoteSegmenter:
    def __init__(self):
        self.last_note = None
        self.last_change_time = None
        self.notes = []

    def process(self, note, cents, time_now):
        if note != self.last_note:
            if self.last_change_time is None:
                self.last_change_time = time_now
            elif time_now - self.last_change_time >= MIN_NOTE_DURATION:
                self.notes.append({
                    "note": note,
                    "cents": cents,
                    "time": round(time_now, 2)
                })
                self.last_note = note
                self.last_change_time = time_now
        else:
            self.last_change_time = None

    def get_notes(self):
        return self.notes
