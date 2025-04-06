from pwn import *
from main2 import *
# Well, howdy there, partner! You rolled in at just the right time! Now, 'round these parts,
#    we got ourselves an old, peculiar law—says any no-good outlaw can try their hand at bestin' the sheriff in a word-guessin' game. 
#     If they win, well, they ride off scot-free. Back in the old days, losin' meant a one-way ticket to Boot Hill, but we ain't 
#     that uncivilized no more.

# I just rounded up a whole gang of low-down bandits, and their day in court's comin' up fast. We can't have any of 'em 
#   slippin' through the cracks. So, what do ya say? You fixin' to help me keep this town safe?

# I gave you a dictionary and a hashin' utility to help you out. To play the game, you'll need to do the followin':
#   1. Pick a word from the dictionary, and a random salt.  The word you pick can't be one you've used before.
#   2. The bandit'll give you another salt. Compute the hash using the utility, like so:
#      ./hash <bandit-salt-hex> <hex(your word + "\x00" + your salt)>
#   3. Reveal the length of your word to the bandit.
#   4. The bandit will guess letters in your word. If they guess a letter that's in your word, you reveal all occurences of that letter.
#   5. If the bandit guesses a letter that's not in your word, you reveal nothing, and the bandit gets a strike.
#   6. If the bandit reveals all the letters in your word, they win.
#   7. If the bandit gets 5 strikes, you reveal your word and salt to ensure there's no funny business, and if it all checks out, you win.

# There's 50 of the varmints, so you best get to it! Good luck!

# Bandit 1 approaches!
# Salt: 68842fa0c5971f2ba7fa9ea9f2bd6f0c
# Your hash: 

# 1. pick a word from dictionary, and a random salt
import json
import subprocess
# 68842fa0c5971f2ba7fa9ea9f2bd6f0c
import secrets
import os

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = os.path.abspath("bin/")
dic = []

class SuccesfulRuns:
  succeses = {

  }
  tracker=0
  def __init__(self):
    pass

  def addTrial(self, salt, word, passed: bool, strikes=None):
    self.tracker += 1
    entry = self.succeses.setdefault(word, {"passed": 0, "failed": 0, "uses": 0, "avg_strikes":0.0})
    entry["passed"] += passed
    entry["failed"] += not passed
    entry["uses"] += 1
    if strikes is not None:
      entry["avg_strikes"] = ((entry["avg_strikes"] * (entry["uses"] -1)) + strikes) / entry["uses"]
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

runStats = SuccesfulRuns()
def generate_salt(length=16):
  return secrets.token_hex(length)

def load_dic():
  global dic
  dic = load_words()
  
def make_command():
  global dic
  word = dic.pop(random.randint(0, len(dic)-1))
  shuffle(dic)
  salt = generate_salt()
  sep_ = b"\x00"
  command = (word.encode() + b"\x00" + bytes.fromhex(salt)).hex()
  return [command, word, salt]
def find_k(msg, f):
  # d = rem.recv().decode("utf-8")
  # print(d)
  match = re.search(f, msg)
  if match:
    # print(f"Salt: {match.group(1)}")
    return match.group(1)
  return ""

def read_all_sent(rem: remote):
  m = b""
  while True:
    try:
      chunk = rem.recv(timeout=.2)
      if not chunk:
        break
      m += chunk
    except EOFError:
      break
  return m
def next_idx(w, c):
  return [m.start() for m in re.finditer(c, w)]
def main(r:remote, trial):
  global runStats
  print(f"=========================================\nTrial #{trial}\n==================================================")
  pirate_salt = ""
  if trial >= 50:
    print("yo?")
    return 1
  m = read_all_sent(r)
  print(m.decode())
  pirate_salt = find_k(m.decode(), r"Salt:\s*(\S+)")
  print(f"Bandit salt: {pirate_salt}")
  comparts = make_command()
  sep_ = f"{'==='*5}\n"
  hash_ = subprocess.run(["./hash", pirate_salt, comparts[0]], cwd="bin/", env=env, capture_output=True, text=True).stdout.strip()
  print(f"My hash? {hash_}")
  r.sendline(hash_.encode())

  m = read_all_sent(r)
  print(m.decode())
  r.sendline(str(len(comparts[1])).encode()  )
  print(f"Sent {len(comparts[1])}")
  m = r.recvline()
  print(m.decode())
  letter_numbers = {}
  for c in comparts[1]:
    if c not in letter_numbers:
      letter_numbers[c] = list(findall(comparts[1], c))
  # letters_to_numbers = {chr(i): list(findall(comparts[1], chr(i))) for i in range(97, 123)} 
  strikes = 0
  while True:
    m = r.recv()
    s = m.decode()
    # print(s, end="")
    guess = find_k(s ,r"Where is '(\S+)' in.*")
    if "Yeehaw!" in s:
      print(":(")
      runStats.addTrial(comparts[2], comparts[1], False, strikes)
      return -1

    elif "Blast" in s:
      print(comparts[1])
      r.sendline(comparts[1].encode())
    elif "salt" in s:
      print(f"salt was:'{comparts[2]}'")
      r.sendline(comparts[2].encode())
      break
    if guess != "":
      # print(f"Guess: {guess}")
      if guess in comparts[1]:
        if len(letter_numbers[guess]) != 0:
          r.sendline(str(letter_numbers[guess].pop()+1).encode())
        else:
          r.sendline(b"")
      else:
        strikes += 1
        r.sendline(b"")
  
  # print("Out of loop")
  # s = r.recv()
  # print(s.decode())
  runStats.addTrial(comparts[2], comparts[1], True, strikes)
  return main(r, trial+1)

def run_fight_bandits():
  try:
    load_dic()
    r = remote("hangman.chal.pwni.ng",  6001)
    if main(r, 0) == -1:
      r = None
      run_fight_bandits()  
  except KeyboardInterrupt:
    return
  
if __name__ == "__main__":
  # runStats
  run_fight_bandits()
  runStats.export_json()
  # print(runStats)
