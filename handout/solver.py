from main import run_fight_bandits, runStats,highestRound
from util import load_words
import threading
import argparse
from stats import SuccesfulRuns
import time
import random
# stats2 = SuccesfulRuns()
# idx = 0
bestOutputLength = 2
bestOutput = []

def worker(result_list, stop_flag, thread_lock, ispow, short, w, output):
    try:
        # currentThreadStats = SuccesfulRuns()
        global highestRound, bestOutputLength, bestOutput
        # global idx 
        r = run_fight_bandits(ispow, short, w, output)
        if stop_flag.is_set():
          return
        if r == -1:
            result_list.append("loss")
            if len(output) > bestOutputLength:
                bestOutput = output
                bestOutputLength = len(output)
            # if currentThreadStats.winsTracker >= 5 and currentThreadStats.winsTracker >= highestRound -3:
                # currentThreadStats.export_json(f"threadedRunsLogs/run{idx}.json")
                # idx += 1
            return
        else:
            print("We got a survivor?")
            result_list.append("win")
            stop_flag.set()
            return
    except KeyboardInterrupt:
        stop_flag.set()
        return -1

def manage_trials(ispow, short, workers):
    results_list = []
    threads = []
    num_trials = 50
    trials_run = 0
    wins = 0
    stop_flag = threading.Event()
    thread_lock = threading.Lock()  # Used to ensure thread-safe operations when modifying threads
    global bestOutput
    global runStats
    dic = load_words()
    try:
      def monitor_and_respawn():
          nonlocal trials_run, wins, dic
          while not stop_flag.is_set():
              if len(threads) < workers:  # Maintain up to 5 concurrent workers
                  if (len(dic) -102) < 0:
                      dic = load_words()
                  idx = random.randint(0, len(dic)-102)
                  slic_ = dic[idx:idx+102]
                  if len(bestOutput) > 0:
                      slic_.extend(bestOutput)
                  t = threading.Thread(target=worker, args=(results_list, stop_flag, thread_lock, ispow, short, slic_, []))
                  threads.append(t)
                  t.start()
                  trials_run += 1
              else:
                  time.sleep(5)  # Briefly wait before checking again

              # Clean up finished threads
              new_threads = []
              for t in threads:
                  if t.is_alive():
                      new_threads.append(t)
              threads[:] = new_threads

              # Process results
              while results_list:
                  result = results_list.pop(0)
                  if result == "win":
                      wins += 1
                      stop_flag.set()
                      break
                  elif result == "loss":
                      pass
                      # stop_flag.set()
                      # break  # Stop if a loss occurs

              if stop_flag.is_set():
                  break

          # Wait for all remaining threads to finish
          for t in threads:
              t.join()

          if not stop_flag.is_set():
              print("1 (50 of 50 trials passed)")
      monitor_thread = threading.Thread(target=monitor_and_respawn)
      monitor_thread.start()
      monitor_thread.join()
    except KeyboardInterrupt:
      print("Got ctrl c")
      stop_flag.set()        
    newStats = SuccesfulRuns()
    for ent in bestOutput:
        log_ = runStats.succeses.get(ent[0], None)
        if log_ is not None:
            log_["salt"] = ent[1]
            newStats.succeses[ent[0]] = log_
    newStats.export_json("soleSuccesses.json")
    runStats.export_json()

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--pow", type=bool, required=False, help="Salt")
    parser.add_argument("--long", type=bool, required=False, help="100 or 50 rounds")
    parser.add_argument("--workers", type=int, required=False, help="Number of threads to have up at any time")

    args = parser.parse_args()

    manage_trials(args.pow or False, args.long or False, args.workers or 20)
