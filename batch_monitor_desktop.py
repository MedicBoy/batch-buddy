from __future__ import annotations

import json
import os
import queue
import sys
import threading
import tkinter as tk
from datetime import datetime
from pathlib import Path
from tkinter import messagebox, ttk

from batch_history import BatchHistory
from batch_monitor_core import BatchMonitor, BatchResult, MonitorConfig


CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "BatchBuddy" / "monitor.json"
HISTORY_PATH = Path(os.environ.get("APPDATA", Path.home())) / "BatchBuddy" / "history.sqlite3"


def _icon_path() -> Path:
    bundle_root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    bundled = bundle_root / "assets" / "batchbuddy.ico"
    if bundled.exists():
        return bundled
    return Path(__file__).resolve().parent / "assets" / "batchbuddy.ico"


class BatchBuddyMonitorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Batch Buddy Monitor")
        self.geometry("860x1040")
        self.minsize(700, 820)
        self.configure(bg="#07131d")
        icon = _icon_path()
        if icon.exists():
            self.iconbitmap(default=str(icon))
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._stop_event: threading.Event | None = None
        self._thread: threading.Thread | None = None
        self._selected_signature: str | None = None
        self._pulse_phase = 0
        self._pulse_running = True
        self._history = BatchHistory(HISTORY_PATH)
        self._vars = {name: tk.StringVar() for name in ("activitysmith", "auth", "cookies", "shopper")}
        self._apns_vars = {name: tk.StringVar() for name in ("push_token", "team_id", "key_id", "private_key_path")}
        self._build_ui()
        self._load_config()
        self.after(250, self._drain_events)
        self.protocol("WM_DELETE_WINDOW", self._close)

    def _build_ui(self) -> None:
        style = ttk.Style(self)
        style.theme_use("clam")
        palette = {"bg": "#071018", "panel": "#0d1b26", "panel2": "#102431", "text": "#e8f4f5", "muted": "#829aa5", "cyan": "#63e6ff", "green": "#44dfaa", "amber": "#ffc266", "line": "#203844"}
        style.configure("TFrame", background=palette["bg"])
        style.configure("TLabel", background=palette["bg"], foreground=palette["text"], font=("Segoe UI", 10))
        style.configure("Muted.TLabel", background=palette["bg"], foreground=palette["muted"], font=("Segoe UI", 9))
        style.configure("Card.TLabelframe", background=palette["panel"], foreground=palette["cyan"], bordercolor=palette["line"], relief="flat")
        style.configure("Card.TLabelframe.Label", background=palette["panel"], foreground=palette["cyan"], font=("Segoe UI", 9, "bold"))
        style.configure("Card.TLabel", background=palette["panel"], foreground=palette["text"], font=("Segoe UI", 10))
        style.configure("CardMuted.TLabel", background=palette["panel"], foreground=palette["muted"], font=("Segoe UI", 9))
        style.configure("Header.TLabel", background=palette["bg"], foreground=palette["text"], font=("Segoe UI", 16, "bold"))
        style.configure("Section.TLabel", background=palette["bg"], foreground=palette["muted"], font=("Segoe UI", 8, "bold"))
        style.configure("Accent.TButton", padding=(14, 8), foreground="#041017", background=palette["cyan"], font=("Segoe UI", 9, "bold"))
        style.map("Accent.TButton", background=[("active", "#a4f3ff")])
        style.configure("Stop.TButton", padding=(12, 8), foreground=palette["text"], background=palette["panel2"])
        style.configure("TButton", padding=(10, 7), foreground=palette["text"], background=palette["panel2"])
        style.configure("Treeview", background=palette["panel"], fieldbackground=palette["panel"], foreground=palette["text"], bordercolor=palette["line"], rowheight=30, font=("Segoe UI", 9))
        style.configure("Treeview.Heading", background=palette["panel2"], foreground=palette["muted"], relief="flat", font=("Segoe UI", 8, "bold"))
        style.map("Treeview", background=[("selected", "#17465a")], foreground=[("selected", palette["text"])])

        shell = ttk.Frame(self)
        shell.pack(fill="both", expand=True)
        self._dashboard_canvas = tk.Canvas(shell, background=palette["bg"], highlightthickness=0, borderwidth=0)
        scrollbar = ttk.Scrollbar(shell, orient="vertical", command=self._dashboard_canvas.yview)
        self._dashboard_canvas.configure(yscrollcommand=scrollbar.set)
        self._dashboard_canvas.pack(side="left", fill="both", expand=True)
        scrollbar.pack(side="right", fill="y")
        root = ttk.Frame(self._dashboard_canvas, padding=(28, 22, 28, 28))
        window = self._dashboard_canvas.create_window((0, 0), window=root, anchor="nw")
        root.bind("<Configure>", lambda _event: self._dashboard_canvas.configure(scrollregion=self._dashboard_canvas.bbox("all")))
        self._dashboard_canvas.bind("<Configure>", lambda event: self._dashboard_canvas.itemconfigure(window, width=event.width))
        self._dashboard_canvas.bind_all("<MouseWheel>", lambda event: self._dashboard_canvas.yview_scroll(-max(1, abs(event.delta) // 120), "units"))

        header = ttk.Frame(root)
        header.pack(fill="x")
        brand = ttk.Frame(header)
        brand.pack(side="left")
        ttk.Label(brand, text="⚡", foreground=palette["cyan"], font=("Segoe UI Symbol", 20, "bold")).pack(side="left", padx=(0, 8))
        ttk.Label(brand, text="BATCH BUDDY", style="Header.TLabel").pack(side="left")
        ttk.Label(brand, text="  /  RADAR", style="Muted.TLabel").pack(side="left", pady=(5, 0))
        actions = ttk.Frame(header)
        actions.pack(side="right")
        self._pulse_label = ttk.Label(actions, text="●  OFFLINE", style="Muted.TLabel")
        self._pulse_label.pack(side="left", padx=(0, 12))
        self.start_button = ttk.Button(actions, text="Start monitor", command=self._start, style="Accent.TButton")
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(actions, text="Stop", command=self._stop, state="disabled", style="Stop.TButton")
        self.stop_button.pack(side="left", padx=(8, 0))
        self.status = tk.StringVar(value="Ready. Enter credentials, then start the monitor.")
        ttk.Label(root, textvariable=self.status, style="Muted.TLabel").pack(anchor="w", pady=(5, 20))

        ttk.Label(root, text="LIVE OVERVIEW", style="Section.TLabel").pack(anchor="w")
        stats = ttk.Frame(root)
        stats.pack(fill="x", pady=(8, 14))
        self.stats = tk.StringVar()
        self._stat_cards = []
        for title in ("Offers today", "Completed", "Net estimate", "Average rate"):
            card = tk.Frame(stats, bg=palette["panel"], highlightbackground=palette["line"], highlightthickness=1)
            card.pack(side="left", fill="x", expand=True, padx=(0, 10))
            tk.Label(card, text=title.upper(), bg=palette["panel"], fg=palette["muted"], font=("Segoe UI", 8, "bold")).pack(anchor="w", padx=14, pady=(12, 1))
            value = tk.Label(card, text="—", bg=palette["panel"], fg=palette["text"], font=("Segoe UI", 19, "bold"))
            value.pack(anchor="w", padx=14, pady=(0, 12))
            self._stat_cards.append(value)

        main_grid = ttk.Frame(root)
        main_grid.pack(fill="x")
        live = ttk.LabelFrame(main_grid, text="  TOP SIGNAL  ", padding=18, style="Card.TLabelframe")
        live.pack(side="left", fill="both", expand=True, padx=(0, 10))
        live_head = ttk.Frame(live)
        live_head.pack(fill="x")
        ttk.Label(live_head, text="No active batch", style="Card.TLabel", font=("Segoe UI", 13, "bold")).pack(side="left")
        self._recommendation_badge = ttk.Label(live_head, text="WAITING", style="CardMuted.TLabel")
        self._recommendation_badge.pack(side="right")
        self.latest = tk.StringVar(value="Waiting for a new offer from the live feed.")
        self.latest_label = ttk.Label(live, textvariable=self.latest, justify="left", style="CardMuted.TLabel", wraplength=620)
        self.latest_label.pack(anchor="w", pady=(13, 18))
        self._signal_meter = tk.Canvas(live, height=8, background=palette["panel"], highlightthickness=0)
        self._signal_meter.pack(fill="x", pady=(0, 16))
        self._signal_meter.create_rectangle(0, 1, 360, 7, fill=palette["line"], outline="")
        self._signal_meter.create_rectangle(0, 1, 0, 7, fill=palette["green"], outline="", tags="meter")
        decision_buttons = ttk.Frame(live)
        decision_buttons.pack(fill="x")
        ttk.Button(decision_buttons, text="Mark completed", command=lambda: self._mark_latest("completed"), style="Accent.TButton").pack(side="left")
        ttk.Button(decision_buttons, text="Mark skipped", command=lambda: self._mark_latest("skipped")).pack(side="left", padx=8)

        inspector = ttk.LabelFrame(main_grid, text="  SIGNAL INSPECTOR  ", padding=18, style="Card.TLabelframe")
        inspector.pack(side="right", fill="both", expand=False)
        self._inspector = tk.StringVar(value="Live Activity\nStand by for the next offer.\n\nActivitySmith\nNot connected")
        ttk.Label(inspector, textvariable=self._inspector, justify="left", style="Card.TLabel", wraplength=220).pack(anchor="w")
        ttk.Label(inspector, text="Accept only opens Shopper. No batch is accepted automatically.", style="CardMuted.TLabel", wraplength=220).pack(anchor="w", pady=(20, 0))

        history = ttk.LabelFrame(root, text="  BATCH HISTORY  ", padding=14, style="Card.TLabelframe")
        history.pack(fill="x", pady=(16, 0))
        columns = ("status", "time", "recommendation", "pay", "net", "rate", "distance")
        self.history_table = ttk.Treeview(history, columns=columns, show="headings", height=7)
        headings = {"status": "Status", "time": "Observed", "recommendation": "Decision", "pay": "Pay", "net": "Net", "rate": "$/hr", "distance": "Distance"}
        widths = {"status": 105, "time": 145, "recommendation": 120, "pay": 75, "net": 75, "rate": 75, "distance": 90}
        for column in columns:
            self.history_table.heading(column, text=headings[column])
            self.history_table.column(column, width=widths[column], anchor="w")
        self.history_table.pack(fill="x", expand=True)
        self.history_table.bind("<<TreeviewSelect>>", self._select_history_row)
        self.details = tk.StringVar(value="Select a batch row to inspect its recorded details.")
        ttk.Label(root, textvariable=self.details, style="Muted.TLabel", justify="left", wraplength=900).pack(anchor="w", pady=(9, 0))

        form = ttk.LabelFrame(root, text="  CONNECTION SETTINGS  ", padding=14, style="Card.TLabelframe")
        form.pack(fill="x", pady=(20, 0))
        self._field(form, 0, "ActivitySmith API key", "activitysmith", True)
        self._field(form, 1, "Instacart auth token", "auth", True)
        self._field(form, 2, "Instacart cookies", "cookies", True)
        self._field(form, 3, "Shopper ID", "shopper", False)

        apns = ttk.LabelFrame(root, text="  NATIVE LIVE ACTIVITY / CARPLAY (OPTIONAL)  ", padding=14, style="Card.TLabelframe")
        apns.pack(fill="x", pady=(12, 0))
        self._field(apns, 0, "ActivityKit push token", "push_token", True, self._apns_vars)
        self._field(apns, 1, "Apple Team ID", "team_id", False, self._apns_vars)
        self._field(apns, 2, "Apple Key ID", "key_id", False, self._apns_vars)
        self._field(apns, 3, "Private .p8 key path", "private_key_path", False, self._apns_vars)
        ttk.Label(apns, text="The Apple key stays local. Native updates are optional; ActivitySmith notifications work without APNs setup.", style="CardMuted.TLabel", wraplength=820).grid(row=4, column=0, columnspan=2, sticky="w", pady=(7, 0))
        ttk.Label(root, text="Batch Buddy keeps monitoring while this window is minimized. Leave the computer online for live offer detection.", style="Muted.TLabel", wraplength=820).pack(anchor="w", pady=(18, 0))
        self._refresh_stats()
        self._refresh_history()
        self._animate_pulse()

    def _field(self, parent: ttk.LabelFrame, row: int, label: str, name: str, secret: bool, variables: dict[str, tk.StringVar] | None = None) -> None:
        variables = variables or self._vars
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=variables[name], show="•" if secret else "")
        entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=5)
        parent.columnconfigure(1, weight=1)

    def _load_config(self) -> None:
        try:
            values = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for name, value in values.items():
                if name in self._vars:
                    self._vars[name].set(value)
                if name in self._apns_vars:
                    self._apns_vars[name].set(value)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._vars["shopper"].set("40757189")

    def _save_config(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        values = {name: var.get() for name, var in self._vars.items()}
        values.update({name: var.get() for name, var in self._apns_vars.items()})
        CONFIG_PATH.write_text(json.dumps(values), encoding="utf-8")

    def _start(self) -> None:
        values = {name: var.get().strip() for name, var in self._vars.items()}
        if not all(values.values()):
            messagebox.showerror("Missing connection details", "Enter the ActivitySmith key, Instacart token, cookies, and Shopper ID.")
            return
        self._save_config()
        apns_values = {name: var.get().strip() for name, var in self._apns_vars.items()}
        config = MonitorConfig(
            activitysmith_api_key=values["activitysmith"],
            auth_token=values["auth"],
            cookies=values["cookies"],
            shopper_id=values["shopper"],
            live_activity_push_token=apns_values["push_token"],
            apple_team_id=apns_values["team_id"],
            apple_key_id=apns_values["key_id"],
            apple_private_key_path=apns_values["private_key_path"],
        )
        self._stop_event = threading.Event()
        monitor = BatchMonitor(config, on_batch=lambda result: self._events.put(("batch", result)), on_status=lambda message: self._events.put(("status", message)))
        self._thread = threading.Thread(target=monitor.run, args=(self._stop_event,), daemon=True)
        self._thread.start()
        self.start_button.configure(state="disabled")
        self.stop_button.configure(state="normal")

    def _stop(self) -> None:
        if self._stop_event:
            self._stop_event.set()
        self.start_button.configure(state="normal")
        self.stop_button.configure(state="disabled")

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "status":
                    self.status.set(str(payload))
                else:
                    result = payload
                    if isinstance(result, BatchResult):
                        self._history.record(result)
                        self.latest.set(f"{result.recommendation}\nPay ${result.pay:.2f}  •  {result.distance:.1f} km  •  {result.items} items\nNet ${result.net_estimate:.2f}  •  ${result.hourly_estimate:.2f}/hr")
                        self.latest_label.configure(foreground="#5de3ff" if result.recommendation == "✅ ACCEPT" else "#ffb454")
                        self._recommendation_badge.configure(text="ACCEPT" if result.recommendation == "✅ ACCEPT" else "CONSIDER")
                        self._inspector.set(f"Live Activity\n{result.recommendation}\n\nPay\n${result.pay:.2f}\n\nNet estimate\n${result.net_estimate:.2f}\n\nHourly estimate\n${result.hourly_estimate:.2f}\n\nActivitySmith\nUpdated")
                        self._signal_meter.coords("meter", 0, 1, max(4, min(360, result.hourly_estimate / 40 * 360)), 7)
                        self._refresh_stats()
                        self._refresh_history()
        except queue.Empty:
            pass
        self.after(250, self._drain_events)

    def _mark_latest(self, status: str) -> None:
        if self._selected_signature:
            self._history.mark(self._selected_signature, status)
        else:
            self._history.mark_latest(status)
        self._refresh_stats()
        self._refresh_history()
        self.status.set(f"Latest batch marked {status}.")

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_table"):
            return
        for item in self.history_table.get_children():
            self.history_table.delete(item)
        for batch in self._history.recent():
            status_icon = {"completed": "✅ Completed", "skipped": "⏭ Skipped"}.get(str(batch["status"]), "• Offered")
            observed = datetime.fromtimestamp(float(batch["observed_at"])).strftime("%b %d %H:%M:%S")
            self.history_table.insert(
                "", "end", iid=str(batch["signature"]),
                values=(status_icon, observed, batch["recommendation"], f"${float(batch['pay']):.2f}",
                        f"${float(batch['net_estimate']):.2f}", f"${float(batch['hourly_estimate']):.2f}",
                        f"{float(batch['distance']):.1f} km"),
            )

    def _select_history_row(self, _event: object) -> None:
        selection = self.history_table.selection()
        if not selection:
            return
        signature = selection[0]
        self._selected_signature = signature
        batch = next((row for row in self._history.recent() if row["signature"] == signature), None)
        if batch:
            observed = datetime.fromtimestamp(float(batch["observed_at"])).strftime("%Y-%m-%d %H:%M:%S")
            self.details.set(
                f"{batch['status'].upper()}  •  {observed}\n"
                f"Pay ${float(batch['pay']):.2f}  •  {float(batch['distance']):.1f} km  •  {int(batch['items'])} items\n"
                f"Net ${float(batch['net_estimate']):.2f}  •  ${float(batch['hourly_estimate']):.2f}/hr\n"
                f"Signature: {signature}"
            )

    def _refresh_stats(self) -> None:
        summary = self._history.summary()
        values = (str(int(summary["offers"])), str(int(summary["completed"])), f"${summary['net']:.2f}", f"${summary['average_hourly']:.2f}")
        if hasattr(self, "_stat_cards"):
            for card, value in zip(self._stat_cards, values):
                card.configure(text=value)

    def _animate_pulse(self) -> None:
        if not self._pulse_running:
            return
        if self._stop_event and not self._stop_event.is_set():
            self._pulse_phase = (self._pulse_phase + 1) % 3
            self._pulse_label.configure(text=("●  MONITORING" if self._pulse_phase else "◉  MONITORING"), foreground="#44dfaa")
        else:
            self._pulse_label.configure(text="●  OFFLINE", foreground="#829aa5")
        self.after(700, self._animate_pulse)

    def _close(self) -> None:
        self._pulse_running = False
        self._stop()
        self.destroy()


if __name__ == "__main__":
    BatchBuddyMonitorApp().mainloop()
