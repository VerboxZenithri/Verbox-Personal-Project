"""DisGO Map Predictor - GUI edition."""
import json, os
from collections import defaultdict
from tkinter import messagebox
import customtkinter as ctk

CS_MP = ["ancient","agency","assault","cache","canals","cobblestone","dust2","inferno",
         "italy","militia","mirage","nuke","office","overpass","train","vertigo"]
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DB = os.path.join(SCRIPT_DIR, "map_history.json")
TOPN, COLS = 5, 4

BG, PANEL, PANEL2 = "#160f21", "#221733", "#2b1d40"
ACC, ACC_H = "#9b5cf6", "#7c3aed"
BTN, BTN_H = "#2e2145", "#3a2a58"
GS, GS_H = "#3b82f6", "#2563eb"
BOT, BOT_H = "#f59e0b", "#d97706"
BOTH, BOTH_H = "#22c55e", "#16a34a"
TXT, DIM = "#e9e4f5", "#a999c9"
DNG, DNG_H = "#ef4444", "#dc2626"


class DMP:
    MOMENTUM_BOOST = 5

    def __init__(self, db=DB, md=5):
        self.db, self.hist, self.md = db, [], md
        self.ng = defaultdict(lambda: defaultdict(int))
        self.gc = defaultdict(int)
        self.load(); self.train()

    def load(self):
        if os.path.exists(self.db):
            try:
                with open(self.db, encoding="utf-8") as f: self.hist = json.load(f)
            except (json.JSONDecodeError, OSError): self.hist = []

    def save(self):
        with open(self.db, "w", encoding="utf-8") as f: json.dump(self.hist, f, indent=4)

    def _valid(self):
        """Filters out malformed/corrupted entries so a hand-edited or
        partially-written JSON file can't crash training or prediction."""
        return [e for e in self.hist if isinstance(e, dict) and "bot" in e]

    def train(self):
        self.ng.clear(); self.gc.clear()
        seq = [e["bot"] for e in self._valid()]
        for m in seq: self.gc[m] += 1
        for i in range(len(seq) - 1):
            nxt = seq[i + 1]
            for k in range(1, self.md + 1):
                if i + 1 - k >= 0:
                    ctx = tuple(seq[i + 1 - k : i + 1])
                    self.ng[ctx][nxt] += 1

    def add(self, guess, bot):
        self.hist.append({"guess": guess, "bot": bot})
        self.save(); self.train()

    def undo(self):
        if not self.hist: return None
        r = self.hist.pop(); self.save(); self.train()
        return r

    def _counts(self):
        seq = [e["bot"] for e in self._valid()]
        if not seq: return None, ""
        for k in range(min(len(seq), self.md), 0, -1):
            ctx = tuple(seq[-k:])
            cand = self.ng.get(ctx)
            if cand:
                n = sum(cand.values())
                c_str = " -> ".join(m.capitalize() for m in ctx)
                return cand, f"Context ({k}-round, n={n}): [{c_str}]"
        if self.gc:
            return self.gc, f"Fallback: Global map frequency (n={sum(self.gc.values())})"
        return None, ""

    def predict(self, top_n=TOPN):
        c, msg = self._counts()
        if not c: return [], "Not enough data yet - log a few rounds to see predictions."

        banned = []
        if self.hist and isinstance(self.hist[-1], dict):
            last_guess = self.hist[-1].get("guess")
            banned = last_guess if isinstance(last_guess, list) else [last_guess]
        pool = [m for m in CS_MP if m not in banned]
        if not pool: return [], "No valid prediction available."
        base_raw = {m: c.get(m, 0) + 1 for m in pool}
        seq = [e["bot"] for e in self._valid()]
        momentum_hit = len(seq) >= 2 and seq[-1] == seq[-2] and seq[-1] in base_raw
        if momentum_hit:
            base_raw[seq[-1]] += self.MOMENTUM_BOOST

        tot = sum(base_raw.values())
        if tot <= 0: return [], "No valid prediction available."
        probs = sorted(((m, v / tot * 100) for m, v in base_raw.items()), key=lambda x: -x[1])

        if momentum_hit:
            msg = f"{msg}  [momentum: last 2 rounds matched]"
        if banned:
            excluded = ", ".join(x.capitalize() for x in banned if x)
            msg = f"{msg} | Excluded (last guess): {excluded}"

        return probs[:top_n], msg


class App(ctk.CTk):
    def __init__(self):
        super().__init__()
        ctk.set_appearance_mode("dark"); ctk.set_default_color_theme("dark-blue")
        self.title("DisGO Map Predictor V2"); self.geometry("1150x760"); self.minsize(980, 680)
        self.configure(fg_color=BG)

        self.dmp = DMP()
        self.mode, self.stage = "Single Guess", "guess"
        self.g_sel, self.b_sel = [], None
        self.mbtn, self.prows = {}, []
        self.log_lines = []
        self.log_win = None

        self._build(); self._refresh()

    def _needed(self): return 2 if self.mode == "Double Guess" else 1

    # ---------- build ----------
    def _build(self):
        self.grid_columnconfigure(0, weight=3); self.grid_columnconfigure(1, weight=2)
        self.grid_rowconfigure(1, weight=1)

        hdr = ctk.CTkFrame(self, fg_color=PANEL, corner_radius=0, height=90)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew"); hdr.grid_propagate(False)
        hdr.grid_columnconfigure(0, weight=1)
        ctk.CTkLabel(hdr, text="DisGO Map Predictor", font=ctk.CTkFont(size=26, weight="bold"),
                     text_color=TXT).grid(row=0, column=0, sticky="w", padx=25, pady=(14, 0))
        ctk.CTkLabel(hdr, text="5-depth N-gram map roulette prediction engine", font=ctk.CTkFont(size=13),
                     text_color=DIM).grid(row=1, column=0, sticky="w", padx=27, pady=(0, 14))
        self.round_lbl = ctk.CTkLabel(hdr, text="Rounds Logged: 0", font=ctk.CTkFont(size=16, weight="bold"),
                                      text_color=ACC)
        self.round_lbl.grid(row=0, column=1, rowspan=2, sticky="e", padx=25)

        left = ctk.CTkFrame(self, fg_color=BG); left.grid(row=1, column=0, sticky="nsew", padx=(20, 10), pady=15)
        left.grid_columnconfigure(0, weight=1)

        mf = ctk.CTkFrame(left, fg_color=PANEL, corner_radius=12); mf.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(mf, text="Guess Mode", font=ctk.CTkFont(size=13, weight="bold"),
                     text_color=DIM).pack(side="left", padx=(16, 10), pady=12)
        self.mode_sw = ctk.CTkSegmentedButton(mf, values=["Single Guess", "Double Guess"], command=self._on_mode,
                                               fg_color=BTN, selected_color=ACC, selected_hover_color=ACC_H,
                                               unselected_color=BTN, unselected_hover_color=BTN_H, text_color=TXT)
        self.mode_sw.set("Single Guess"); self.mode_sw.pack(side="left", padx=(0, 16), pady=12)

        self.instr = ctk.CTkLabel(left, text="STEP 1 - Select Your Guess",
                                   font=ctk.CTkFont(size=16, weight="bold"), text_color=ACC)
        self.instr.pack(fill="x", pady=(0, 10))

        gf = ctk.CTkFrame(left, fg_color=PANEL, corner_radius=14); gf.pack(fill="both", expand=True, pady=(0, 12))
        inner = ctk.CTkFrame(gf, fg_color="transparent"); inner.pack(fill="both", expand=True, padx=16, pady=16)

        rows = -(-len(CS_MP) // COLS)  # ceiling division: robust even if CS_MP isn't an exact multiple of COLS
        for c in range(COLS): inner.grid_columnconfigure(c, weight=1)
        for r in range(rows): inner.grid_rowconfigure(r, weight=1)

        for i, m in enumerate(CS_MP):
            r, c = divmod(i, COLS)
            b = ctk.CTkButton(inner, text=m.capitalize(), corner_radius=10, fg_color=BTN, hover_color=BTN_H,
                               text_color=TXT, font=ctk.CTkFont(size=14, weight="bold"), height=58,
                               command=lambda m=m: self._click(m))
            b.grid(row=r, column=c, padx=6, pady=6, sticky="nsew"); self.mbtn[m] = b

        self.summ = ctk.CTkLabel(left, text="Guess: -     Bot Result: -", font=ctk.CTkFont(size=13), text_color=DIM)
        self.summ.pack(fill="x", pady=(0, 10))

        af = ctk.CTkFrame(left, fg_color="transparent"); af.pack(fill="x")
        af.grid_columnconfigure((0, 1, 2), weight=1)
        ctk.CTkButton(af, text="Clear Selection", corner_radius=10, height=44, fg_color=BTN, hover_color=BTN_H,
                      text_color=TXT, font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._clear).grid(row=0, column=0, sticky="ew", padx=(0, 6))
        self.submit_btn = ctk.CTkButton(af, text="Submit / Log Round", corner_radius=10, height=44, fg_color=BOTH,
                                         hover_color=BOTH_H, text_color="#0b1a10",
                                         font=ctk.CTkFont(size=13, weight="bold"), state="disabled",
                                         command=self._submit)
        self.submit_btn.grid(row=0, column=1, sticky="ew", padx=6)
        ctk.CTkButton(af, text="Undo Last Round", corner_radius=10, height=44, fg_color=DNG, hover_color=DNG_H,
                      text_color=TXT, font=ctk.CTkFont(size=13, weight="bold"),
                      command=self._undo).grid(row=0, column=2, sticky="ew", padx=(6, 0))

        right = ctk.CTkFrame(self, fg_color=BG); right.grid(row=1, column=1, sticky="nsew", padx=(10, 20), pady=15)
        right.grid_columnconfigure(0, weight=1)

        pp = ctk.CTkFrame(right, fg_color=PANEL, corner_radius=14); pp.pack(fill="x", pady=(0, 12))
        ctk.CTkLabel(pp, text="Real-Time Predictions", font=ctk.CTkFont(size=17, weight="bold"),
                     text_color=TXT).pack(anchor="w", padx=18, pady=(16, 4))
        ctk.CTkLabel(pp, text="Most likely next map based on the current sequence", font=ctk.CTkFont(size=11),
                     text_color=DIM).pack(anchor="w", padx=18, pady=(0, 12))
        pc = ctk.CTkFrame(pp, fg_color="transparent"); pc.pack(fill="x", padx=18, pady=(0, 6))
        pc.grid_columnconfigure(2, weight=1)
        for i in range(TOPN):
            row = ctk.CTkFrame(pc, fg_color="transparent"); row.grid(row=i, column=0, columnspan=4, sticky="ew", pady=5)
            row.grid_columnconfigure(2, weight=1)
            ctk.CTkLabel(row, text=f"#{i+1}", font=ctk.CTkFont(size=12, weight="bold"), text_color=ACC, width=26,
                         anchor="w").grid(row=0, column=0, sticky="w")
            name = ctk.CTkLabel(row, text="-", font=ctk.CTkFont(size=13, weight="bold"), text_color=TXT, width=90,
                                 anchor="w")
            name.grid(row=0, column=1, sticky="w", padx=(4, 8))
            bar = ctk.CTkProgressBar(row, height=14, corner_radius=6, fg_color=BTN, progress_color=ACC)
            bar.set(0); bar.grid(row=0, column=2, sticky="ew", padx=(0, 8))
            pct = ctk.CTkLabel(row, text="0.0%", font=ctk.CTkFont(size=13, weight="bold"), text_color=DIM, width=55,
                                anchor="e")
            pct.grid(row=0, column=3, sticky="e")
            self.prows.append((name, bar, pct))
        self.pred_status = ctk.CTkLabel(pp, text="", font=ctk.CTkFont(size=12, slant="italic"), text_color=DIM,
                                         wraplength=380, justify="left")
        self.pred_status.pack(anchor="w", padx=18, pady=(4, 16))

        lp = ctk.CTkFrame(right, fg_color=PANEL, corner_radius=14); lp.pack(fill="both", expand=True)
        lh = ctk.CTkFrame(lp, fg_color="transparent"); lh.pack(fill="x", padx=18, pady=(16, 8))
        ctk.CTkLabel(lh, text="Activity Log", font=ctk.CTkFont(size=15, weight="bold"),
                     text_color=TXT).pack(side="left")
        ctk.CTkButton(lh, text="View Full Log", corner_radius=10, height=30, width=120,
                      fg_color=ACC, hover_color=ACC_H, text_color=TXT,
                      font=ctk.CTkFont(size=12, weight="bold"),
                      command=self._open_log_viewer).pack(side="right")
        self.log_box = ctk.CTkTextbox(lp, fg_color=PANEL2, text_color=DIM, corner_radius=10,
                                       font=ctk.CTkFont(size=12), state="disabled",
                                       scrollbar_button_color=ACC, scrollbar_button_hover_color=ACC_H)
        self.log_box.pack(fill="both", expand=True, padx=18, pady=(0, 18))

    # ---------- state ----------
    def _on_mode(self, v):
        self.mode = v; self._clear(); self._log(f"Guess mode switched to: {v}")

    def _click(self, m):
        if self.stage == "guess":
            if m in self.g_sel:
                self.g_sel.remove(m)
            else:
                self.g_sel.append(m)

            if len(self.g_sel) >= self._needed():
                self.stage = "bot"; self.instr.configure(text="STEP 2 - Select What The BOT Rolled")
            else:
                left = self._needed() - len(self.g_sel)
                self.instr.configure(text=f"STEP 1 - Select Guess #{len(self.g_sel)+1} ({left} more needed)")
        else:
            self.b_sel = m; self.instr.configure(text="Ready! Click 'Submit / Log Round' to confirm.")
        self._style(); self._summary(); self._submit_state()

    def _style(self):
        banned = []
        if self.dmp.hist and isinstance(self.dmp.hist[-1], dict):
            last_guess = self.dmp.hist[-1].get("guess")
            banned = last_guess if isinstance(last_guess, list) else [last_guess]
        for m, b in self.mbtn.items():
            if m in banned and self.stage == "guess":
                b.configure(fg_color="#1a1322", hover_color="#1a1322", text_color="#3a2b4a", state="disabled")
                continue
            ig, ib = m in self.g_sel, m == self.b_sel
            if ig and ib: b.configure(fg_color=BOTH, hover_color=BOTH_H, text_color="#0b1a10", state="normal")
            elif ig: b.configure(fg_color=GS, hover_color=GS_H, text_color=TXT, state="normal")
            elif ib: b.configure(fg_color=BOT, hover_color=BOT_H, text_color="#241000", state="normal")
            else: b.configure(fg_color=BTN, hover_color=BTN_H, text_color=TXT, state="normal")

    def _summary(self):
        g = " + ".join(m.capitalize() for m in self.g_sel) if self.g_sel else "-"
        b = self.b_sel.capitalize() if self.b_sel else "-"
        self.summ.configure(text=f"Guess: {g}     Bot Result: {b}")

    def _submit_state(self):
        ok = len(self.g_sel) == self._needed() and self.b_sel is not None
        self.submit_btn.configure(state="normal" if ok else "disabled")

    def _clear(self):
        self.g_sel, self.b_sel, self.stage = [], None, "guess"
        self.instr.configure(text="STEP 1 - Select Your Guess")
        self._style(); self._summary(); self._submit_state()

    # ---------- actions ----------
    def _submit(self):
        gv = list(self.g_sel) if self.mode == "Double Guess" else self.g_sel[0]
        bv = self.b_sel
        self.dmp.add(gv, bv)
        gd = " + ".join(g.capitalize() for g in self.g_sel) if isinstance(gv, list) else gv.capitalize()
        self._log(f"Round #{len(self.dmp.hist)} logged - Guess: {gd}  ->  Bot: {bv.capitalize()}")
        self._clear(); self._preds(); self._rounds()

    def _undo(self):
        if not self.dmp.hist:
            messagebox.showinfo("Nothing to Undo", "There are no logged rounds yet.", parent=self); return
        e = self.dmp.hist[-1]
        g = e.get("guess") if isinstance(e, dict) else None
        g = " + ".join(str(x).capitalize() for x in g) if isinstance(g, list) else str(g).capitalize()
        bo = str(e.get("bot")).capitalize() if isinstance(e, dict) else "Unknown"
        if not messagebox.askyesno("Undo Last Round",
                                    f"Remove the most recent round from {DB}?\n\nGuess: {g}\nBot Result: {bo}\n\n"
                                    "This cannot be undone.", parent=self):
            return
        self.dmp.undo(); self._log(f"Undo - removed last round (Guess: {g}, Bot: {bo})")
        self._clear(); self._preds(); self._rounds()

    # ---------- refresh ----------
    def _refresh(self):
        self._style(); self._summary(); self._submit_state(); self._preds(); self._rounds()
        self._seed_log()
        self._log("Application started. Ready to log rounds.")

    def _seed_log(self):
        for i, e in enumerate(self.dmp.hist, 1):
            if not isinstance(e, dict): continue
            g, b = e.get("guess"), e.get("bot")
            gd = " + ".join(str(x).capitalize() for x in g) if isinstance(g, list) else str(g).capitalize()
            self.log_lines.append(f"Round #{i} logged - Guess: {gd}  ->  Bot: {str(b).capitalize()}")

    def _preds(self):
        preds, msg = self.dmp.predict(TOPN)
        self.pred_status.configure(text=msg)
        for i, (name, bar, pct) in enumerate(self.prows):
            if i < len(preds):
                m, p = preds[i]
                name.configure(text=m.capitalize()); pct.configure(text=f"{p:.1f}%"); bar.set(max(p / 100, 0.01))
            else:
                name.configure(text="-"); pct.configure(text="0.0%"); bar.set(0)

    def _rounds(self):
        self.round_lbl.configure(text=f"Rounds Logged: {len(self.dmp.hist)}")

    def _log(self, msg):
        self.log_lines.append(msg)
        self.log_box.configure(state="normal")
        self.log_box.insert("end", f"- {msg}\n"); self.log_box.see("end")
        self.log_box.configure(state="disabled")
        if self.log_win is not None and self.log_win.winfo_exists():
            self._refresh_log_viewer()

    def _open_log_viewer(self):
        if self.log_win is not None and self.log_win.winfo_exists():
            self.log_win.lift(); self.log_win.focus()
            return

        win = ctk.CTkToplevel(self)
        win.title("Full Activity Log")
        win.geometry("640x600")
        win.minsize(420, 320)
        win.configure(fg_color=BG)
        win.transient(self)
        self.log_win = win

        hdr = ctk.CTkFrame(win, fg_color=PANEL, corner_radius=0, height=64)
        hdr.pack(fill="x"); hdr.pack_propagate(False)
        ctk.CTkLabel(hdr, text="Full Activity Log", font=ctk.CTkFont(size=18, weight="bold"),
                     text_color=TXT).pack(side="left", padx=20)
        ctk.CTkLabel(hdr, text=f"{len(self.log_lines)} entries", font=ctk.CTkFont(size=12),
                     text_color=DIM).pack(side="right", padx=20)

        body = ctk.CTkFrame(win, fg_color=BG); body.pack(fill="both", expand=True, padx=18, pady=16)
        self.log_viewer_box = ctk.CTkTextbox(body, fg_color=PANEL2, text_color=TXT, corner_radius=12,
                                              font=ctk.CTkFont(size=13), state="disabled",
                                              scrollbar_button_color=ACC, scrollbar_button_hover_color=ACC_H)
        self.log_viewer_box.pack(fill="both", expand=True)
        self._refresh_log_viewer()

        ctk.CTkButton(win, text="Close", corner_radius=10, height=40, fg_color=ACC, hover_color=ACC_H,
                      text_color=TXT, font=ctk.CTkFont(size=13, weight="bold"),
                      command=win.destroy).pack(fill="x", padx=18, pady=(0, 18))

    def _refresh_log_viewer(self):
        self.log_viewer_box.configure(state="normal")
        self.log_viewer_box.delete("1.0", "end")
        self.log_viewer_box.insert("end", "\n".join(f"- {m}" for m in self.log_lines))
        self.log_viewer_box.see("end")
        self.log_viewer_box.configure(state="disabled")


if __name__ == "__main__":
    App().mainloop()