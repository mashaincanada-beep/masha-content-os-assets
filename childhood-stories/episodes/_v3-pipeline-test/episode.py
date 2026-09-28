"""V3 PIPELINE TEST - "Through" (engine test; not for publishing)

Concept sheet
1. Main child: Ava (Grade 2, age 7)
2. Setting: family kitchen, evening
3. Relationship: daughter / mother (Elena)
4. Situation: reading her bedtime book at the kitchen table
5. Skill: decoding a tricky word ("through")                  -> READING
6. Tension: she stops, finger under the word, quiet
7. Turning point: Mom leaves the stove and sits beside her
8. Payoff: she sounds it out and reads it; a small smile
9. Parent message: sitting beside them is part of the practice
10. Final line: "Sometimes the smallest word is where confidence begins."
"""
EPISODE = {
    "title": "Through",
    "slug": "v3-pipeline-test",
    "key": "F", "bpm": 72, "seed": 23,
    "brand_line": "Small practice. Bigger moments.",
    "shots": [
        # 1 - wide: evening kitchen, Ava reading, Mom at the stove
        {"set": "kitchen", "set_kw": {"night": True}, "music": "uncertain", "amb": "kitchen", "trans": "fade", "tdur": 0.6,
         "start": 1.2, "min": 5.0,
         "cam": [[0, 540, 1000, 1.0], ["end", 520, 1030, 1.12]],
         "actors": {
             "ava": {"keys": [[0, {"x": 430, "pose": "sit", "y": 930, "expr": "focused", "hand": [478, 1242], "hand2": [360, 1244], "point": [10, -15]}],
                              ["end", {"hand": [505, 1242]}]]},
             "elena": {"keys": [[0, {"x": 820, "y": 760, "pose": "stand", "expr": "calm", "look": [0.7, 0.8], "hand": [965, 1128], "hand2": [760, 1190]}],
                                [2.6, {"look": [-1.0, 0.3], "ease": 0.4}]]},
         },
         "props": [["book", {"x": 470, "y": 1240, "word": "through"}], ["mug", {"x": 772, "y": 1248}], ["pencil", {"x": 250, "y": 1240}]],
         "script": [
             {"who": "ava", "line": "The little fox ran... |0.6|", "expr": "focused", "speed": 0.92},
         ],
         "tail": 1.2},

        # 2 - medium: stuck on a word; Mom comes to sit beside her
        {"set": "kitchen", "set_kw": {"night": True}, "music": "reflective", "amb": "kitchen", "trans": "cut",
         "start": 0.6,
         "cam": [[0, 575, 1000, 1.42], ["end", 590, 1010, 1.5]],
         "actors": {
             "ava": {"keys": [[0, {"x": 430, "pose": "sit", "y": 930, "expr": "worried", "hand": [493, 1242], "hand2": [360, 1244], "point": [10, -15], "tilt": -4}]]},
             "elena": {"keys": [[0, {"x": 820, "y": 760, "pose": "stand", "expr": "tender", "look": [-1.0, 0.4], "hand": [890, 1120], "hand2": [750, 1150]}],
                                ["L0.end", {"x": 820}],
                                ["L0.end+1.8", {"x": 700, "pose": "walk", "ease": 1.8}],
                                ["L0.end+2.6", {"pose": "sit", "y": 880, "ease": 0.8, "hand": [780, 1200], "hand2": [640, 1245]}],
                                ["L1", {"hand": [610, 1228], "point": [-18, -4], "ease": 0.6}]]},
         },
         "props": [["book", {"x": 470, "y": 1240, "word": "through"}], ["mug", {"x": 772, "y": 1248}], ["pencil", {"x": 250, "y": 1240}]],
         "script": [
             {"who": "ava", "line": "I... |0.4| don't know this word.", "expr": "worried", "speed": 0.9},
             {"pause": 3.0},
             {"who": "elena", "line": "Let's try the first sound. |0.3| Together.", "expr": "tender", "speed": 0.92},
         ],
         "sfx": [{"name": "footsteps", "t": "L0.end+0.3", "gain": 0.5}, {"name": "chair", "t": "L0.end+2.2", "gain": 0.45}],
         "tail": 0.8},

        # 3 - close two-shot: the word comes out
        {"set": "kitchen", "set_kw": {"night": True}, "music": "hopeful", "amb": "kitchen", "trans": "cut",
         "start": 0.5,
         "cam": [[0, 565, 985, 1.86], ["end", 565, 995, 2.0]],
         "actors": {
             "ava": {"keys": [[0, {"x": 430, "pose": "sit", "y": 930, "expr": "unsure", "look": [0.9, 0.0], "hand": [493, 1242], "hand2": [360, 1244], "point": [10, -15]}],
                              ["L0", {"look": [0.2, 0.9], "ease": 0.3}],
                              ["L0.end", {"hand": [540, 1242]}],
                              ["L0.end+0.4", {"expr": "happy", "look": [0.8, -0.1], "ease": 0.5}]]},
             "elena": {"keys": [[0, {"x": 700, "pose": "sit", "y": 880, "expr": "tender", "hand": [610, 1228], "hand2": [640, 1245], "point": [-18, -4]}],
                                ["L0.end+0.3", {"expr": "happy"}]]},
         },
         "props": [["book", {"x": 470, "y": 1240, "word": "through", "glow_from": "L0"}], ["mug", {"x": 772, "y": 1248}]],
         "script": [
             {"who": "ava", "line": "Th... |0.4| thr... |0.4| through!", "expr": "hopeful", "speed": 0.9},
         ],
         "fx": [["hearts", "L0.end+0.3"]],
         "tail": 2.4},
    ],
    "end": {"narration": ["Sometimes the smallest word...", "is where confidence begins."], "music": "gentle"},
    "cover": {"shot": 2, "t": "L0.end+1.2", "title": "Through"},
}
