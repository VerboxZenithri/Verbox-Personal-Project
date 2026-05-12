"""
ULTRA AUTO CLICKER v3 - FIXED
==============================
- Left / Right / Middle Click + Custom Key
- Toggle mode & Press mode
- Custom trigger key (hotkey global)
- Batched Win32 SendInput | Multi-Thread
- NO lock contention in hot loop (lock-free counter)
- Window resizable + scrollable

CARA JALANKAN:
  python ultra_clicker_v3.py
  (Python harus ada di PATH — download dari python.org)
"""

import ctypes
import ctypes.wintypes as wintypes
import threading
import time
import sys

try:
    import tkinter as tk
    from tkinter import messagebox
except ImportError:
    print("ERROR: Install Python dari python.org (centang Add to PATH)")
    sys.exit(1)

# ================================================================
#  VK CODES
# ================================================================
VK_CODES = {
    "space": 0x20, "enter": 0x0D, "backspace": 0x08,
    "tab": 0x09, "escape": 0x1B, "delete": 0x2E,
    "insert": 0x2D, "home": 0x24, "end": 0x23,
    "pageup": 0x21, "pagedown": 0x22,
    "left": 0x25, "up": 0x26, "right": 0x27, "down": 0x28,
    "f1":  0x70, "f2":  0x71, "f3":  0x72, "f4":  0x73,
    "f5":  0x74, "f6":  0x75, "f7":  0x76, "f8":  0x77,
    "f9":  0x78, "f10": 0x79, "f11": 0x7A, "f12": 0x7B,
    "num0": 0x60, "num1": 0x61, "num2": 0x62, "num3": 0x63,
    "num4": 0x64, "num5": 0x65, "num6": 0x66, "num7": 0x67,
    "num8": 0x68, "num9": 0x69,
    "shift": 0x10, "ctrl": 0x11, "alt": 0x12,
}
for _c in "abcdefghijklmnopqrstuvwxyz":
    VK_CODES[_c] = ord(_c.upper())
for _c in "0123456789":
    VK_CODES[_c] = ord(_c)

# ================================================================
#  WIN32
# ================================================================
INPUT_MOUSE    = 0
INPUT_KEYBOARD = 1

MOUSEEVENTF_LEFTDOWN   = 0x0002
MOUSEEVENTF_LEFTUP     = 0x0004
MOUSEEVENTF_RIGHTDOWN  = 0x0008
MOUSEEVENTF_RIGHTUP    = 0x0010
MOUSEEVENTF_MIDDLEDOWN = 0x0020
MOUSEEVENTF_MIDDLEUP   = 0x0040
KEYEVENTF_KEYDOWN      = 0x0000
KEYEVENTF_KEYUP        = 0x0002

class MOUSEINPUT(ctypes.Structure):
    _fields_ = [
        ("dx", wintypes.LONG), ("dy", wintypes.LONG),
        ("mouseData", wintypes.DWORD), ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD), ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]

class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD), ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD), ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(wintypes.ULONG)),
    ]

class _UNION(ctypes.Union):
    _fields_ = [("mi", MOUSEINPUT), ("ki", KEYBDINPUT)]

class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("_input", _UNION)]

_SendInput        = ctypes.windll.user32.SendInput
_GetAsyncKeyState = ctypes.windll.user32.GetAsyncKeyState
_SendInput.argtypes       = [wintypes.UINT, ctypes.POINTER(INPUT), ctypes.c_int]
_SendInput.restype        = wintypes.UINT
_GetAsyncKeyState.restype = ctypes.c_short

INPUT_SIZEOF = ctypes.sizeof(INPUT)

# ================================================================
#  BATCH BUILDERS
#  Toggle: paired DOWN+UP  → 1 full click per pair
#  Press : DOWN only       → held state (OS handles repeat)
# ================================================================

def _mouse_toggle_batch(n, dn, up):
    a = (INPUT * (2*n))()
    for i in range(n):
        a[2*i].type = INPUT_MOUSE;   a[2*i]._input.mi.dwFlags = dn
        a[2*i+1].type = INPUT_MOUSE; a[2*i+1]._input.mi.dwFlags = up
    return a

def _mouse_press_batch(n, dn):
    # Press mode: spam DOWN+UP pairs tapi CEPAT agar terasa "ditekan terus"
    # Sama seperti toggle — tapi kita stop saat key dilepas
    return _mouse_toggle_batch(n, dn, dn ^ 0x02 if dn == MOUSEEVENTF_LEFTDOWN
                                       else (MOUSEEVENTF_RIGHTUP if dn == MOUSEEVENTF_RIGHTDOWN
                                       else MOUSEEVENTF_MIDDLEUP))

def _mouse_release(up):
    a = (INPUT * 1)(); a[0].type = INPUT_MOUSE; a[0]._input.mi.dwFlags = up; return a

def _key_toggle_batch(n, vk):
    a = (INPUT * (2*n))()
    for i in range(n):
        a[2*i].type = INPUT_KEYBOARD;   a[2*i]._input.ki.wVk = vk;   a[2*i]._input.ki.dwFlags = KEYEVENTF_KEYDOWN
        a[2*i+1].type = INPUT_KEYBOARD; a[2*i+1]._input.ki.wVk = vk; a[2*i+1]._input.ki.dwFlags = KEYEVENTF_KEYUP
    return a

def _key_release(vk):
    a = (INPUT * 1)(); a[0].type = INPUT_KEYBOARD; a[0]._input.ki.wVk = vk; a[0]._input.ki.dwFlags = KEYEVENTF_KEYUP; return a

# ================================================================
#  LOCK-FREE COUNTER
#  Setiap thread punya counter lokal → dikumpulkan tiap 200 batch.
#  Tidak ada lock di hot loop → tidak ada contention → CPS max!
# ================================================================

# Shared atomic-ish counter via c_longlong (GIL melindungi simple int ops di CPython)
_total_clicks = 0
_total_lock   = threading.Lock()

def _flush_local(n):
    global _total_clicks
    # GIL membuat += atomic di CPython — tapi pakai lock untuk safety
    with _total_lock:
        _total_clicks += n

# ================================================================
#  STATE
# ================================================================

class _State:
    running       = False
    cps_now       = 0
    release_batch = None

state       = _State()
_threads    = []
trigger_vk  = [0x75]   # default F6
_alive      = True

# ================================================================
#  WORKER — LOCK FREE HOT LOOP
# ================================================================

FLUSH_EVERY = 200   # update shared counter setiap N batch

def worker(batch):
    sz      = INPUT_SIZEOF
    size    = len(batch)
    # Each batch = size/2 full clicks (down+up pairs)
    cpc     = size // 2
    local   = 0
    flush_n = 0
    while state.running:
        sent = _SendInput(size, batch, sz)
        if sent > 0:
            local   += cpc
            flush_n += 1
            if flush_n >= FLUSH_EVERY:
                _flush_local(local)
                local   = 0
                flush_n = 0
    if local:
        _flush_local(local)

# ================================================================
#  CPS MONITOR
# ================================================================

def _cps_monitor():
    prev = 0
    while True:
        time.sleep(1.0)
        cur = _total_clicks
        state.cps_now = cur - prev
        prev = cur

threading.Thread(target=_cps_monitor, daemon=True).start()

# ================================================================
#  START / STOP
# ================================================================

def _do_start(batch_fn, release_batch, n_threads, b_size):
    global _total_clicks
    _total_clicks       = 0
    state.running       = True
    state.release_batch = release_batch
    for _ in range(n_threads):
        b = batch_fn(b_size)
        t = threading.Thread(target=worker, args=(b,), daemon=True)
        t.start()
        _threads.append(t)

def _do_stop():
    state.running = False
    if state.release_batch is not None:
        _SendInput(1, state.release_batch, INPUT_SIZEOF)
        state.release_batch = None
    _threads.clear()

# ================================================================
#  GLOBAL HOTKEY MONITOR (polls ~50 Hz, no overhead on main thread)
#  Toggle: rising edge → toggle
#  Press : follow key state
# ================================================================

def _hotkey_monitor(get_mode, on_toggle, on_start, on_stop):
    last = False
    while _alive:
        vk = trigger_vk[0]
        if not vk:
            time.sleep(0.05); last = False; continue
        pressed = bool(_GetAsyncKeyState(vk) & 0x8000)
        mode    = get_mode()
        if mode == "toggle":
            if pressed and not last:
                root.after(0, on_toggle)
        else:
            if pressed and not state.running:
                root.after(0, on_start)
            elif not pressed and state.running:
                root.after(0, on_stop)
        last = pressed
        time.sleep(0.02)

# ================================================================
#  GUI CONSTANTS
# ================================================================

BG     = "#0a0a0f"
PANEL  = "#111118"
PANEL2 = "#161622"
BORDER = "#1e1e32"
ACCENT = "#00e5ff"
GREEN  = "#00ff99"
RED    = "#ff2255"
YELLOW = "#ffdd00"
TEXT   = "#d0d0e8"
MUTED  = "#404060"
DARK   = "#1e1e2e"

FT  = ("Courier New", 13, "bold")
FBG = ("Courier New", 36, "bold")
FMD = ("Courier New", 10, "bold")
FSM = ("Courier New",  9)
FXS = ("Courier New",  8)

# ================================================================
#  ROOT
# ================================================================

root = tk.Tk()
root.title("ULTRA CLICKER v3")
root.configure(bg=BG)
root.resizable(True, True)
root.minsize(440, 680)
root.geometry("490x800")

# ── Scrollable main frame ─────────────────────────────────────
_outer = tk.Frame(root, bg=BG)
_outer.pack(fill="both", expand=True)

_canvas = tk.Canvas(_outer, bg=BG, highlightthickness=0, bd=0)
_vsb    = tk.Scrollbar(_outer, orient="vertical", command=_canvas.yview)
_canvas.configure(yscrollcommand=_vsb.set)
_vsb.pack(side="right", fill="y")
_canvas.pack(side="left", fill="both", expand=True)

main = tk.Frame(_canvas, bg=BG)
_cwin = _canvas.create_window((0, 0), window=main, anchor="nw")

main.bind("<Configure>", lambda e: _canvas.configure(
    scrollregion=_canvas.bbox("all")))
_canvas.bind("<Configure>", lambda e: _canvas.itemconfig(_cwin, width=e.width))
_canvas.bind_all("<MouseWheel>",
    lambda e: _canvas.yview_scroll(int(-1*(e.delta/120)), "units"))

# ── Section helper ─────────────────────────────────────────────
def section(title, pady_top=10):
    wrap = tk.Frame(main, bg=BG)
    wrap.pack(fill="x", padx=16, pady=(pady_top, 0))
    tk.Label(wrap, text=f"  {title}", font=FXS, bg=DARK, fg=MUTED,
             anchor="w").pack(fill="x")
    inner = tk.Frame(wrap, bg=PANEL, highlightthickness=1,
                     highlightbackground=BORDER)
    inner.pack(fill="x")
    return inner

def rb(**kw):
    return dict(font=FSM, bg=PANEL2, fg=TEXT, selectcolor=ACCENT,
                indicatoron=1, activebackground=PANEL2,
                activeforeground=ACCENT, relief="flat", bd=0,
                cursor="hand2", **kw)

# ================================================================
#  HEADER
# ================================================================
tk.Frame(main, bg=ACCENT, height=3).pack(fill="x")
tk.Label(main, text="  ULTRA CLICKER  v3  ",
         font=FT, bg=BG, fg=ACCENT).pack(pady=(10, 0))
tk.Label(main,
         text="Batched Win32  |  Lock-Free Counter  |  Multi-Thread",
         font=FXS, bg=BG, fg=MUTED).pack()

# ================================================================
#  CPS DISPLAY
# ================================================================
cf = tk.Frame(main, bg=PANEL, highlightthickness=1, highlightbackground=BORDER)
cf.pack(fill="x", padx=16, pady=(12, 0))

tk.Label(cf, text="CLICKS / SECOND", font=FXS, bg=PANEL, fg=MUTED).pack(pady=(8, 0))
cps_var = tk.StringVar(value="0")
cps_lbl = tk.Label(cf, textvariable=cps_var, font=FBG, bg=PANEL, fg=GREEN)
cps_lbl.pack()
tot_var = tk.StringVar(value="TOTAL: 0")
tk.Label(cf, textvariable=tot_var, font=FXS, bg=PANEL, fg=MUTED).pack(pady=(0, 8))

# ── Status bar ─────────────────────────────────────────────────
status_var = tk.StringVar(value="  IDLE")
status_lbl = tk.Label(main, textvariable=status_var,
                      font=("Courier New", 11, "bold"), bg=BG, fg=MUTED)
status_lbl.pack(pady=(8, 0))

# ================================================================
#  SECTION: INPUT TYPE
# ================================================================
mf = section("INPUT TYPE", pady_top=14)

mode_var = tk.StringVar(value="Left Click")

mr = tk.Frame(mf, bg=PANEL2)
mr.pack(fill="x", padx=10, pady=(8, 4))
for lbl in ["Left Click", "Right Click", "Middle Click"]:
    tk.Radiobutton(mr, text=lbl, variable=mode_var, value=lbl,
                   **rb()).pack(side="left", padx=8, pady=4)

ckr = tk.Frame(mf, bg=PANEL2)
ckr.pack(fill="x", padx=10, pady=(0, 8))
tk.Radiobutton(ckr, text="Custom Key:", variable=mode_var,
               value="custom_key", **rb()).pack(side="left", padx=8)

ckey_entry = tk.Entry(ckr, font=FMD, bg=DARK, fg=ACCENT,
                      insertbackground=ACCENT, width=10,
                      relief="flat", bd=4)
ckey_entry.insert(0, "space")
ckey_entry.pack(side="left", padx=4)

def _key_help(e=None):
    messagebox.showinfo("Daftar Custom Key",
        "Ketik nama key (huruf kecil), contoh:\n\n"
        "  space, enter, backspace, tab, escape, delete\n"
        "  insert, home, end, pageup, pagedown\n"
        "  left, right, up, down\n"
        "  f1 - f12\n"
        "  num0 - num9  (numpad)\n"
        "  a-z,  0-9\n"
        "  shift, ctrl, alt")

q1 = tk.Label(ckr, text=" ? ", font=FXS, bg=DARK, fg=ACCENT, cursor="hand2")
q1.pack(side="left", padx=2)
q1.bind("<Button-1>", _key_help)

# ================================================================
#  SECTION: CLICK MODE
# ================================================================
cmf = section("CLICK MODE", pady_top=10)
cmi = tk.Frame(cmf, bg=PANEL2)
cmi.pack(fill="x", padx=10, pady=8)

click_mode_var = tk.StringVar(value="toggle")

tk.Radiobutton(cmi, text="Toggle  —  tekan trigger 1x = ON, tekan lagi = OFF",
               variable=click_mode_var, value="toggle",
               **rb()).pack(anchor="w", padx=4, pady=4)
tk.Radiobutton(cmi, text="Press   —  tahan trigger = ON, lepas = OFF",
               variable=click_mode_var, value="press",
               **rb()).pack(anchor="w", padx=4, pady=4)

# ================================================================
#  SECTION: TRIGGER KEY
# ================================================================
trf = section("TRIGGER KEY", pady_top=10)
tri = tk.Frame(trf, bg=PANEL2)
tri.pack(fill="x", padx=10, pady=8)

tk.Label(tri, text="Key:", font=FSM, bg=PANEL2, fg=TEXT).pack(side="left", padx=(0,6))

trigger_var = tk.StringVar(value="f6")
trigger_entry = tk.Entry(tri, textvariable=trigger_var, font=FMD,
                         bg=DARK, fg=YELLOW, insertbackground=YELLOW,
                         width=10, relief="flat", bd=4)
trigger_entry.pack(side="left", padx=4)

trig_status = tk.StringVar(value="  F6 aktif")
tk.Label(tri, textvariable=trig_status, font=FXS,
         bg=PANEL2, fg=GREEN).pack(side="left", padx=6)

def apply_trigger(e=None):
    raw = trigger_var.get().strip().lower()
    vk  = VK_CODES.get(raw)
    if vk is None:
        trig_status.set(f"  '{raw}' tidak valid!")
        root.after(2500, lambda: trig_status.set("  (ketik lalu Enter)"))
        return
    trigger_vk[0] = vk
    trig_status.set(f"  {raw.upper()} aktif")

trigger_entry.bind("<Return>", apply_trigger)
tk.Button(tri, text="Set", font=FXS, bg=DARK, fg=TEXT,
          relief="flat", cursor="hand2",
          command=apply_trigger).pack(side="left", padx=2)

def _trig_help(e=None):
    messagebox.showinfo("Trigger Key Help",
        "Ketik nama key lalu tekan Enter atau klik Set.\n\n"
        "Toggle mode:\n"
        "  Tekan trigger 1x  ->  mulai\n"
        "  Tekan lagi        ->  berhenti\n\n"
        "Press mode:\n"
        "  Tahan trigger  ->  aktif\n"
        "  Lepas          ->  berhenti otomatis\n\n"
        "Tips: pakai key yang tidak bentrok di game,\n"
        "contoh: f9, insert, num0, num9, dll.")

q2 = tk.Label(tri, text=" ? ", font=FXS, bg=DARK, fg=ACCENT, cursor="hand2")
q2.pack(side="left", padx=2)
q2.bind("<Button-1>", _trig_help)

# ================================================================
#  SECTION: PERFORMANCE TUNING
# ================================================================
pf  = section("PERFORMANCE TUNING", pady_top=10)
pi  = tk.Frame(pf, bg=PANEL2)
pi.pack(fill="x", padx=10, pady=6)

def _slider_row(parent, label, var, lo, hi, res=1):
    row = tk.Frame(parent, bg=PANEL2)
    row.pack(fill="x", pady=4)
    tk.Label(row, text=label, font=FXS, bg=PANEL2, fg=MUTED,
             width=12, anchor="w").pack(side="left")
    vl = tk.Label(row, text=str(var.get()), font=FSM,
                  bg=PANEL2, fg=ACCENT, width=6)
    vl.pack(side="right")
    sl = tk.Scale(row, from_=lo, to=hi, orient="horizontal",
                  variable=var, bg=PANEL2, fg=TEXT, troughcolor=DARK,
                  highlightthickness=0, showvalue=False, resolution=res,
                  command=lambda v: vl.config(text=v))
    sl.pack(side="left", fill="x", expand=True, padx=6)
    return sl

thread_var = tk.IntVar(value=8)
batch_var  = tk.IntVar(value=500)
tsl = _slider_row(pi, "Threads:", thread_var, 1, 32)
bsl = _slider_row(pi, "Batch:", batch_var, 50, 2000, 50)

tk.Label(pi,
         text="  Naikan batch untuk CPS lebih tinggi. Default 8 thread, 500 batch.",
         font=FXS, bg=PANEL2, fg=MUTED, justify="left").pack(anchor="w", pady=(0,6))

# ================================================================
#  RESOLVE BATCHES → sesuai mode
# ================================================================

def _resolve():
    m = mode_var.get()
    if m == "Left Click":
        tn = lambda n: _mouse_toggle_batch(n, MOUSEEVENTF_LEFTDOWN, MOUSEEVENTF_LEFTUP)
        rel = _mouse_release(MOUSEEVENTF_LEFTUP)
    elif m == "Right Click":
        tn = lambda n: _mouse_toggle_batch(n, MOUSEEVENTF_RIGHTDOWN, MOUSEEVENTF_RIGHTUP)
        rel = _mouse_release(MOUSEEVENTF_RIGHTUP)
    elif m == "Middle Click":
        tn = lambda n: _mouse_toggle_batch(n, MOUSEEVENTF_MIDDLEDOWN, MOUSEEVENTF_MIDDLEUP)
        rel = _mouse_release(MOUSEEVENTF_MIDDLEUP)
    elif m == "custom_key":
        raw = ckey_entry.get().strip().lower()
        vk  = VK_CODES.get(raw)
        if vk is None:
            messagebox.showerror("Key Tidak Valid",
                f"'{raw}' tidak dikenali. Klik ? untuk referensi.")
            return None
        tn  = lambda n, _vk=vk: _key_toggle_batch(n, _vk)
        rel = _key_release(vk)
    else:
        return None

    # Toggle & Press pakai batch yang SAMA (DOWN+UP pairs)
    # Bedanya hanya: press berhenti saat key dilepas, toggle berhenti saat dipencet lagi
    return tn, rel

# ================================================================
#  UI: START / STOP
# ================================================================

def _lock_ui(locked):
    st = "disabled" if locked else "normal"
    for w in [ckey_entry, trigger_entry, tsl, bsl]:
        w.config(state=st)

def do_start():
    res = _resolve()
    if res is None:
        return
    batch_fn, release = res

    m_label  = mode_var.get() if mode_var.get() != "custom_key" \
               else f"KEY[{ckey_entry.get().upper()}]"
    cm_label = click_mode_var.get().upper()

    _do_start(batch_fn, release, thread_var.get(), batch_var.get())

    status_var.set(f"  RUNNING  |  {m_label}  |  {cm_label}")
    status_lbl.config(fg=GREEN)
    btn_main.config(text="  STOP  ", bg=RED, fg="white",
                    activebackground="#cc0033")
    _lock_ui(True)

def do_stop():
    _do_stop()
    status_var.set("  IDLE")
    status_lbl.config(fg=MUTED)
    btn_main.config(text="  START  ", bg=GREEN, fg=BG,
                    activebackground="#00cc77")
    _lock_ui(False)

def do_toggle():
    if state.running:
        do_stop()
    else:
        do_start()

# ================================================================
#  BUTTONS
# ================================================================
bf = tk.Frame(main, bg=BG)
bf.pack(fill="x", padx=16, pady=14)

btn_main = tk.Button(bf, text="  START  ",
                     font=("Courier New", 16, "bold"),
                     bg=GREEN, fg=BG, activebackground="#00cc77",
                     relief="flat", bd=0, height=2,
                     cursor="hand2", command=do_toggle)
btn_main.pack(fill="x", pady=(0, 6))

tk.Button(bf, text="Reset Counter",
          font=FXS, bg=DARK, fg=MUTED, activebackground=BORDER,
          relief="flat", cursor="hand2",
          command=lambda: globals().update(_total_clicks=0)).pack(fill="x")

# ── Footer ─────────────────────────────────────────────────────
tk.Label(main, text="  Klik window target dulu sebelum Start!",
         font=FXS, bg=BG, fg="#665500").pack(pady=(4, 0))
tk.Label(main, text="  Tutup window atau tekan F8 = keluar",
         font=FXS, bg=BG, fg=MUTED).pack(pady=(2, 6))
tk.Frame(main, bg=ACCENT, height=2).pack(fill="x")

# ================================================================
#  UI UPDATE LOOP (setiap 200ms)
# ================================================================
def _update():
    cps = state.cps_now
    cps_var.set(f"{cps:,}")
    tot_var.set(f"TOTAL: {_total_clicks:,}")
    if   cps > 800_000: cps_lbl.config(fg="#ff00ff")
    elif cps > 400_000: cps_lbl.config(fg=YELLOW)
    elif cps > 100_000: cps_lbl.config(fg=GREEN)
    elif state.running:  cps_lbl.config(fg=ACCENT)
    else:                cps_lbl.config(fg=MUTED)
    root.after(200, _update)

_update()

# ================================================================
#  HOTKEY THREAD
# ================================================================
threading.Thread(
    target=_hotkey_monitor,
    args=(click_mode_var.get, do_toggle, do_start, do_stop),
    daemon=True
).start()

# ================================================================
#  EXIT
# ================================================================
def _quit(e=None):
    global _alive
    _alive = False
    _do_stop()
    root.destroy()

root.bind("<F8>", _quit)
root.protocol("WM_DELETE_WINDOW", _quit)
root.mainloop()