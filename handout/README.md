# Hangman Solver

Run with:
```
> python3 solver.py --workers 25 SILENT
```
## Arguments
***--workers*** : Number of active threads/workers to have bashing against this. Default: 25
***--long***    : Game mode to choose. Defualt: 50 Bandits mode
***--pow***     : Enables POW mode. Default: disabled.

Over time, it will log to `all_output.txt` each message. This will get messy fast.
Once found, the flag should be written into `flag2.txt`
