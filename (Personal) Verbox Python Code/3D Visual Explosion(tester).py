import time
import sys
import winsound

def nuke(n):
    a = []
    for i in range(255):
        if n > 1:
            a.append(nuke(n-1))
        else:
            a.append(i)
    return a

RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
CYAN = "\033[36m"
RESET = "\033[0m"
spinner = ["|", "/", "-", "\\"]
bar_len = 67
total_steps = 100

print(CYAN + "☢️  ARMING NUCLEAR PAYLOAD...\n" + RESET)

# progress bar + beep kecil
for i in range(total_steps + 1):
    filled = int(i / total_steps * bar_len)
    bar="█"*filled+"-"*(bar_len-filled)
    spin = spinner[i % len(spinner)]

    color = GREEN if i < 70 else YELLOW if i < 90 else RED

    sys.stdout.write(f"\r{color}[{bar}] {i:3d}% {spin}{RESET}")
    sys.stdout.flush()

    # beep pendek tiap 10%
    
    if i % 10 == 0:
        winsound.Beep(1200, 80)

    time.sleep(0.04)

print("\n\n" + RED + "🚨 LAUNCH SEQUENCE INITIATED 🚨" + RESET)
time.sleep(1)

# countdown dengan suara
for t in range(5, 0, -1):
    print(YELLOW + f"💣 T-{t}..." + RESET)
    winsound.Beep(800, 300)
    time.sleep(1)

# suara final launch
winsound.Beep(2000, 700)

print("\n" + RED + "🔥🔥🔥 BOOM! EXECUTING NUKE FUNCTION 🔥🔥🔥\n" + RESET)

print(nuke(3))
