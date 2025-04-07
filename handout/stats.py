import threading
import json
class SuccesfulRuns:
  succeses = {

  }
  winsTracker=0
  tracker=0
  def __init__(self):
    self._lock = threading.Lock()

  def addTrial(self, salt, word, passed: bool, strikes=None):
    with self._lock:
      self.tracker += 1
      self.winsTracker += passed
      entry = self.succeses.setdefault(word, {"passed": 0, "failed": 0, "uses": 0, "avg_strikes":0.0, "salt": None})
      entry["passed"] += passed
      entry["failed"] += not passed
      entry["uses"] += 1
      if strikes is not None:
        entry["avg_strikes"] = ((entry["avg_strikes"] * (entry["uses"] -1)) + strikes) / entry["uses"]
      # if working_salt is not None:
      if salt is not None:
        entry["salt"] = salt
  def incrIdx(self, ent, v):
    ent["count"] += v.uses
    ent["overall"] += v.passed

  def topPerformances(self, threshold=1):
    reuslts = []
    for word, stats in self.succeses.items():
      if stats["uses"] >= threshold:
        win_rate = stats["passed"] / stats["uses"]
        reuslts.append({
            "word": word,
            "win_rate": round(win_rate, 3),
            "uses": stats["uses"],
            "avg_strikes": round(stats["avg_strikes"], 2),
        })    
    reuslts.sort(key=lambda x: (-x["win_rate"], -x["uses"]))  # prioritize win rate, then usage
    return reuslts[:10]
  
  def export_json(self, filename="runs.json"):
    with open(filename, "w") as f:
      json.dump(self.succeses, f, indent=2, sort_keys=True)
  def anaylze(self):
    count = {
      "long": {
        "count": 0,
        "overall": 0,
      },
      "short": {
        "count": 0,
        "overall": 0
      },
      "medium": {
        "count": 0,
        "overall": 0
      },

    }
    for k, v in self.succeses.items():
      if len(k) < 4:
        key = "short"
      elif len(k) < 7:
        key = "medium"
      else:
        key = "long"
      self.incrIdx(count[key], v)
    # print(count)
    for key in count:
      c = count[key]
      c["rate"] = round(c["overall"] / c["count"], 2) if c["count"] else 0
    return count
  def __str__(self):
    print(self.succeses)


