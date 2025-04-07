import json
import numpy
from pwnlib.tubes import remote
import secrets
import random
import subprocess
import logging
import re
import os
import sys

env = os.environ.copy()
env["LD_LIBRARY_PATH"] = os.path.abspath("bin/")
dic = []
logging.basicConfig(filename='all_output.log', level=logging.DEBUG,
                    format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)



def sort_entry(e):
  return dict(sorted(e.items(), key=lambda x: x[1]['passed'], reverse=True))

"""
  toast, apr6. seed_data
  Add in various words (if not already present in the current dataset)
  and update the stored dataset for future runs
"""
def seed_data(old):
  uniques = {}
  with open("dictionary.txt", "r") as f:
    d = f.readlines()
    d = [l_.replace("\n", "", -1) for l_ in d]
    for l in d:
      c = len(numpy.unique(list(l)))
      if str(c) not in uniques:
        uniques[str(c)] = 1
      else:
        uniques[str(c)] +=1
      
      if c >= 7 or len(l) < 5:
        if not l in old:
          old[l] = {
            "salt": None,
            "avg_strikes": numpy.random.randint(0,10),
            "passed": numpy.random.randint(0,10)
          }
  with open("runsmixed.json", "w") as f:
    json.dump(old, f, indent=2, sort_keys=True) 
shouldSeed = False

"""
  toast, apr5. load_words
  pull in data based on a condition
"""
def load_words():
  w = {}
  high_words = []
  global shouldSeed
  with open("soleSuccesses1.json", "r") as f:
    w = json.load(f)
    sorted_data_desc = sort_entry(w)
    for word, stats in sorted_data_desc.items():
      high_words.append([word, stats["salt"]])
    if shouldSeed:
      seed_data(w)
  return high_words

def generate_salt(length=16):
  return secrets.token_hex(length)

def load_dic():
  global dic
  dic = load_words()
  # with open("dictionary.txt", "r") as f:
  #   dic = f.readlines()
  #   dic = [d.replace("\n", "") for d in dic]
  
def make_command(words):
  # global dic
  word = words.pop(random.randint(0, len(words)-1))
  salt = generate_salt()
  if word[1] != None:
    salt = word[1]
  # print()
  # shuffle(dic)
  sep_ = b"\x00"
  command = (word[0].encode() + b"\x00" + bytes.fromhex(salt)).hex()
  return [command, word[0], salt]
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
def add_if(s):
  if "You saved the town" in s:
    with open("flag2.txt", "w") as f:
      f.write(s)
def next_idx(w, c):
  return [m.start() for m in re.finditer(c, w)]

def make_hash(ps, com):
  return subprocess.run(["./hash", ps, com], cwd="bin/", env=env, capture_output=True, text=True).stdout.strip()


class StreamToLogger(object):
    """Fake file-like stream object that redirects writes to a logger instance."""
    def __init__(self, logger, log_level=logging.INFO):
        self.logger = logger
        self.log_level = log_level
        self.linebuf = ''

    def write(self, buf):
        for line in buf.rstrip().splitlines():
            self.logger.log(self.log_level, line.rstrip())

    def flush(self):
        pass

stdout_redirection = StreamToLogger(logger, logging.INFO)
sys.stdout = stdout_redirection

if __name__ == "__main__":
  shouldSeed = True
  l = load_words()
  print(len(l))
