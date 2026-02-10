from audio.note_mapper import freq_to_sargam

print("Testing relative Sa mapping\n")

freqs = [
    440.0,   # becomes Sa
    493.88,  # ~ Re
    523.25,  # ~ Ga
    587.33,  # ~ Ma
    659.25,  # ~ Pa
]

for f in freqs:
    note, cents = freq_to_sargam(f)
    print(f"{f:7.2f} Hz -> {note:8} | {cents:6.2f} cents")
