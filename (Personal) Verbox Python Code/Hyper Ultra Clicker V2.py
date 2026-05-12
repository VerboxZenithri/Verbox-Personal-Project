"""
╔══════════════════════════════════════════════════════════════╗
║         ULTRA AUTO CLICKER - Batched SendInput Edition       ║
║    Multi-threaded + Batched Win32 API  → Target: 1M CPS      ║
╚══════════════════════════════════════════════════════════════╝

CARA PAKAI:
  pip install keyboard
  python ultra_clicker.py

TOGGLE: F6  |  STOP TOTAL: F8
"""

import ctypes
import ctypes.wintypes as wintypes
import threading
import time
import sys
import os

try:
    import tkinter as tk
    from tkinter import ttk
    HAS_TK = True
except ImportError:
    HAS_TK = False

# ─── Win32 Structures ─────────────────────────────────────────────────────────

MOUSEEVENTF_LEFTDOWN = 0x0002
MOUSEEVENTF_LEFTUP   = 0x0004
MOUSEEVENTF_MOVE     = 0x0001

INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx",          wintypes.LONG),
        ("dy",          wintypes.LONG),
        ("mouseData",   wintypes.DWORD),
        ("dwFlags",     wintypes.DWORD),
        ("time",        wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]

class _INPUT_UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [
        ("type", wintypes.DWORD),
        ("_input", _INPUT_UNION),
    ]

SendInput = ctypes.windll.user32.SendInput
SendInput.argtypes = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
SendInput.restype  = wintypes.UINT

# ─── Build a reusable batch buffer ────────────────────────────────────────────

def make_batch(n: int):
    """
    Creates an array of 2*n INPUT structs: n DOWN + n UP pairs.
    One SendInput call = n clicks.
    """
    arr = (INPUT * (2 * n))()
    for i in range(n):
        # DOWN
        arr[2*i].type        = INPUT_MOUSE
        arr[2*i]._input.mi.dwFlags = MOUSEEVENTF_LEFTDOWN
        # UP
        arr[2*i+1].type      = INPUT_MOUSE
        arr[2*i+1]._input.mi.dwFlags = MOUSEEVENTF_LEFTUP
    return arr

# ─── Shared state ─────────────────────────────────────────────────────────────

class State:
    running   = False
    total     = 0
    cps_now   = 0
    lock      = threading.Lock()

state = State()

# ─── Worker Thread ────────────────────────────────────────────────────────────

BATCH_SIZE   = 500      # clicks per SendInput call
NUM_THREADS  = 8        # parallel threads (tune to your CPU core count)

def worker(batch):
    size   = len(batch)
    sizeof = ctypes.sizeof(INPUT)
    local  = 0
    while state.running:
        sent = SendInput(size, batch, sizeof)
        if sent > 0:
            local += sent // 2      # each pair = 1 click
            with state.lock:
                state.total += sent // 2

thread_list = []

def start_clicking():
    state.running = True
    for _ in range(NUM_THREADS):
        b = make_batch(BATCH_SIZE)
        t = threading.Thread(target=worker, args=(b,), daemon=True)
        t.start()
        thread_list.append(t)

def stop_clicking():
    state.running = False
    thread_list.clear()

# ─── CPS Counter ──────────────────────────────────────────────────────────────

def cps_monitor():
    prev = 0
    while True:
        time.sleep(1.0)
        cur = state.total
        state.cps_now = cur - prev
        prev = cur

threading.Thread(target=cps_monitor, daemon=True).start()

# ─── GUI ──────────────────────────────────────────────────────────────────────

if HAS_TK:

    BG      = "#0d0d0d"
    ACCENT  = "#00ff88"
    RED     = "#ff3355"
    TEXT    = "#e0e0e0"
    PANEL   = "#141414"
    BORDER  = "#222222"

    root = tk.Tk()
    root.title("ULTRA CLICKER")
    root.configure(bg=BG)
    root.resizable(False, False)
    root.geometry("340x420")

    # ── Fonts ──
    try:
        FONT_MONO  = ("Courier New", 11, "bold")
        FONT_LARGE = ("Courier New", 28, "bold")
        FONT_LABEL = ("Courier New", 9)
    except:
        FONT_MONO  = ("Courier", 11, "bold")
        FONT_LARGE = ("Courier", 28, "bold")
        FONT_LABEL = ("Courier", 9)

    # ── Header ──
    hdr = tk.Frame(root, bg=ACCENT, height=4)
    hdr.pack(fill="x")

    title = tk.Label(root, text="⚡ ULTRA CLICKER ⚡",
                     font=("Courier New", 14, "bold"),
                     bg=BG, fg=ACCENT)
    title.pack(pady=(10, 2))

    subtitle = tk.Label(root, text="Batched SendInput  ·  Multi-Thread",
                        font=FONT_LABEL, bg=BG, fg="#555555")
    subtitle.pack()

    # ── CPS Display ──
    cps_frame = tk.Frame(root, bg=PANEL, bd=0, highlightthickness=1,
                         highlightbackground=BORDER)
    cps_frame.pack(fill="x", padx=20, pady=(16, 0))

    tk.Label(cps_frame, text="CLICKS / SECOND", font=FONT_LABEL,
             bg=PANEL, fg="#555555").pack(pady=(8,0))
    cps_var = tk.StringVar(value="0")
    cps_disp = tk.Label(cps_frame, textvariable=cps_var,
                        font=FONT_LARGE, bg=PANEL, fg=ACCENT)
    cps_disp.pack(pady=(0, 6))

    # ── Total Display ──
    tot_frame = tk.Frame(root, bg=PANEL, bd=0, highlightthickness=1,
                         highlightbackground=BORDER)
    tot_frame.pack(fill="x", padx=20, pady=(4, 0))

    tk.Label(tot_frame, text="TOTAL CLICKS", font=FONT_LABEL,
             bg=PANEL, fg="#555555").pack(pady=(6,0))
    tot_var = tk.StringVar(value="0")
    tot_disp = tk.Label(tot_frame, textvariable=tot_var,
                        font=FONT_MONO, bg=PANEL, fg=TEXT)
    tot_disp.pack(pady=(0, 6))

    # ── Status ──
    status_var = tk.StringVar(value="● IDLE")
    status_lbl = tk.Label(root, textvariable=status_var,
                          font=("Courier New", 11, "bold"),
                          bg=BG, fg="#555555")
    status_lbl.pack(pady=(10, 0))

    # ── Controls ──
    ctrl = tk.Frame(root, bg=BG)
    ctrl.pack(pady=(12, 0))

    def toggle():
        if state.running:
            stop_clicking()
            btn_toggle.config(text="▶  START  [F6]", bg=ACCENT, fg=BG)
            status_var.set("● IDLE")
            status_lbl.config(fg="#555555")
        else:
            state.total = 0
            start_clicking()
            btn_toggle.config(text="■  STOP   [F6]", bg=RED, fg="#ffffff")
            status_var.set("● RUNNING")
            status_lbl.config(fg=ACCENT)

    btn_toggle = tk.Button(ctrl, text="▶  START  [F6]",
                           font=("Courier New", 12, "bold"),
                           bg=ACCENT, fg=BG,
                           activebackground="#00cc6a",
                           relief="flat", bd=0,
                           width=18, height=2,
                           cursor="hand2",
                           command=toggle)
    btn_toggle.pack(pady=4)

    def reset():
        with state.lock:
            state.total = 0
    btn_reset = tk.Button(ctrl, text="↺  RESET COUNTER",
                          font=FONT_LABEL, bg=PANEL, fg="#555555",
                          activebackground=BORDER,
                          relief="flat", bd=0, cursor="hand2",
                          command=reset)
    btn_reset.pack(pady=2)

    # ── Config row ──
    cfg = tk.Frame(root, bg=BG)
    cfg.pack(pady=(10,0), padx=20, fill="x")

    tk.Label(cfg, text=f"Threads: {NUM_THREADS}  |  Batch: {BATCH_SIZE}  |  Press F6 to toggle",
             font=FONT_LABEL, bg=BG, fg="#333333").pack()

    # ── Footer ──
    tk.Frame(root, bg=ACCENT, height=2).pack(side="bottom", fill="x")

    # ── Keyboard shortcut (F6) ──
    root.bind("<F6>", lambda e: toggle())
    root.bind("<F8>", lambda e: (stop_clicking(), root.destroy()))

    # ── Update loop ──
    def update_ui():
        cps_val = state.cps_now
        cps_var.set(f"{cps_val:,}")
        # Color CPS based on performance
        if cps_val > 800_000:
            cps_disp.config(fg="#ff00ff")
        elif cps_val > 500_000:
            cps_disp.config(fg="#ffff00")
        elif cps_val > 100_000:
            cps_disp.config(fg=ACCENT)
        else:
            cps_disp.config(fg=TEXT if not state.running else ACCENT)
        tot_var.set(f"{state.total:,}")
        root.after(250, update_ui)

    update_ui()
    root.mainloop()
    stop_clicking()

else:
    # ─── Fallback CLI mode ────────────────────────────────────────────────────
    print("╔══════════════════════════════╗")
    print("║  ULTRA CLICKER  - CLI Mode   ║")
    print("╠══════════════════════════════╣")
    print("║  ENTER = Toggle  |  Q = Quit ║")
    print("╚══════════════════════════════╝\n")

    def cli_display():
        while True:
            time.sleep(1)
            status = "RUNNING" if state.running else "IDLE"
            print(f"\r  [{status}]  CPS: {state.cps_now:>10,}  |  Total: {state.total:>14,}   ", end="", flush=True)

    threading.Thread(target=cli_display, daemon=True).start()

    while True:
        cmd = input().strip().lower()
        if cmd == "q":
            stop_clicking()
            print("\nStopped. Bye!")
            sys.exit(0)
        else:
            if state.running:
                stop_clicking()
                print("\n[STOPPED]")
            else:
                state.total = 0
                start_clicking()
                print("\n[STARTED]")