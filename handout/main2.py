import json

def load_words():
  w = {}
  high_words = []
  with open("runs.json", "r") as f:
    w = json.load(f)
    for word, stats in w.items():
      if stats["avg_strikes"] >= 4:
        high_words.append(word)
    return high_words
