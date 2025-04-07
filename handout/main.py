from pwn import *
from util import *
import subprocess
from stats import SuccesfulRuns
import os
env = os.environ.copy()
env["LD_LIBRARY_PATH"] = "/bin"
highestRound = -1

runStats = SuccesfulRuns()

def main(r:remote, trial, isPOW, words, output):
  try:
    global runStats
    pirate_salt = ""
    m = read_all_sent(r)
    print(m.decode())
    if isPOW:
      if "hashcash" in m.decode():
        c = m.decode().replace("\n","").split(" ")
        print(f"Com to send: '{c}'")
        hash_res = subprocess.run(c, capture_output=True, text=True, env=env).stdout.strip()
        r.sendline(hash_res.encode())
        m = read_all_sent(r)
        print(m.decode())
    add_if(m.decode())

    bandit_count = find_k(m.decode(), r"Bandit\s*(\d+)")
    print(f"Bandit: {bandit_count}")
    pirate_salt = find_k(m.decode(), r"Salt:\s*(\S+)")
    comparts = make_command(words)
    hash_ = make_hash(pirate_salt, comparts[0])
    print(m.decode(), hash_)
    r.sendline(hash_.encode())

    m = read_all_sent(r)
    print(m.decode(), len(comparts[1]))
    add_if(m.decode())

    r.sendline(str(len(comparts[1])).encode())
    m = r.recvline()
    print(m.decode())
    add_if(m.decode())
    letter_numbers = {}
    for c in comparts[1]:
      if c not in letter_numbers:
        letter_numbers[c] = list(findall(comparts[1], c))
    strikes = 0
    global highestRound
    while True:
      m = r.recv()
      s = m.decode()
      # print(s, end="")
      add_if(s)

      guess = find_k(s ,r"Where is '(\S+)' in.*")
      if "Yeehaw!" in s:
        # print(":(")
        runStats.addTrial(None, comparts[1], False, strikes)
        if highestRound == trial:
          print("Reseting highest round :(")
          highestRound = 0
        r.close()
        return -1

      elif "Blast" in s:
        r.sendline(comparts[1].encode())
      elif "salt" in s:
        r.sendline(comparts[2].encode())
        output.append([comparts[1], comparts[2]])
        if trial > highestRound:
          highestRound = trial
          print(f'New highest round: {highestRound}')
        break
      if guess != "":
        if guess in comparts[1]:
          if len(letter_numbers[guess]) != 0:
            l_ = str(letter_numbers[guess].pop()+1)
            r.sendline(l_.encode())
          else:
            r.sendline(b"")
        else:
          strikes += 1
          r.sendline(b"")
    runStats.addTrial(comparts[2], comparts[1], True, strikes)
  except EOFError:
    r.close()
    return -1
  return main(r, trial+1, isPOW, words, output)

def run_fight_bandits(ispow, long, words, output):
  # load_dic()
  url = "hangman.chal.pwni.ng"
  # url = "hangman1"
  if ispow:
    url = "hangman2.chal.pwni.ng"
    # url = "hangman2"
  port = 6001
  if long:
    port = 6002
  r = remote(url, port)
  # r = process([url, "../dictionary.txt", "../flag2.txt"], env=env, cwd="./bin/")
  r.level = "error"
  return main(r, 0, ispow,words, output)
  
# if __name__ == "__main__":
#   run_fight_bandits()
#   print("Updating stats...")
#   runStats.export_json()
