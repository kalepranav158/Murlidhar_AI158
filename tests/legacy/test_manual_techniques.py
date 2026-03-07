from backend.utils.audio.techniques import detect_techniques, compare_with_reference

def make_glide():
    # synthetic ascending glide in cents every 10ms
    pc = []
    t = 0.0
    for i in range(20):
        freq = 440.0 * (2 ** ((i*10)/1200.0))  # +10 cents per frame
        pc.append({"freq": freq, "time": t, "conf": 1.0})
        t += 0.01
    return pc

def test_detect_meend_simple():
    pc = make_glide()
    d = detect_techniques(pc)
    assert "meend" in d
    assert len(d["meend"]) >= 1

def test_compare_ref():
    pc = make_glide()
    d = detect_techniques(pc)
    ref = {"notes": [{"time":0.0},{"time":0.19}], "techniques": ["meend"]}
    score = compare_with_reference(d, ref)
    assert score["technique_score"] > 0
