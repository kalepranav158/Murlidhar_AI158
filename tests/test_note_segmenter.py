from audio.note_segmenter import NoteSegmenter

seg = NoteSegmenter()

fake_stream = [
    ("Sa",  5.0, 0.00),
    ("Sa", -3.0, 0.05),
    ("Sa",  2.0, 0.10),

    # Re sustained long enough
    ("Re",  4.0, 0.30),
    ("Re", -2.0, 0.45),
    ("Re",  1.0, 0.55),

    # Ga sustained
    ("Ga",  3.0, 0.70),
    ("Ga", -4.0, 0.85),
    ("Ga",  2.0, 0.95),
]

for note, cents, t in fake_stream:
    seg.process(note, cents, t)

print("Detected notes:\n")
for n in seg.get_notes():
    print(n)
