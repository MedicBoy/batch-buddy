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
        style.configure("TFrame", background="#07131d")
        style.configure("TLabel", background="#07131d", foreground="#e6f4f7")
        style.configure("Muted.TLabel", background="#07131d", foreground="#91a6ad")
        style.configure("Header.TLabel", background="#07131d", foreground="#5de3ff", font=("Segoe UI", 18, "bold"))
        style.configure("Card.TLabelframe", background="#10212d", foreground="#5de3ff", bordercolor="#244454", relief="groove")
        style.configure("Card.TLabelframe.Label", background="#10212d", foreground="#8cecff", font=("Segoe UI", 10, "bold"))
        style.configure("Card.TLabel", background="#10212d", foreground="#e6f4f7")
        style.configure("CardMuted.TLabel", background="#10212d", foreground="#91a6ad")
        style.configure("Accent.TButton", padding=9, foreground="#07131d", background="#5de3ff", font=("Segoe UI", 10, "bold"))
        style.configure("Stop.TButton", padding=9)
        style.configure("TButton", padding=8)

        root = ttk.Frame(self, padding=20)
        root.pack(fill="both", expand=True)
        header = ttk.Frame(root)
        header.pack(fill="x")
        ttk.Label(header, text="BATCH BUDDY", style="Header.TLabel").pack(side="left")
        ttk.Label(header, text="LIVE MONITOR", style="Muted.TLabel").pack(side="right", pady=(7, 0))
        ttk.Label(root, text="A focused desktop companion for real-time Shopper offers", style="Muted.TLabel").pack(anchor="w", pady=(2, 18))

        form = ttk.LabelFrame(root, text="Connection settings", padding=14, style="Card.TLabelframe")
        form.pack(fill="x")
        self._field(form, 0, "ActivitySmith API key", "activitysmith", True)
        self._field(form, 1, "Instacart auth token", "auth", True)
        self._field(form, 2, "Instacart cookies", "cookies", True)
        self._field(form, 3, "Shopper ID", "shopper", False)

        apns = ttk.LabelFrame(root, text="Native Batch Buddy Live Activity / CarPlay (optional)", padding=14, style="Card.TLabelframe")
        apns.pack(fill="x", pady=(14, 0))
        self._field(apns, 0, "ActivityKit push token", "push_token", True, self._apns_vars)
        self._field(apns, 1, "Apple Team ID", "team_id", False, self._apns_vars)
        self._field(apns, 2, "Apple Key ID", "key_id", False, self._apns_vars)
        self._field(apns, 3, "Private .p8 key path", "private_key_path", False, self._apns_vars)
        ttk.Label(apns, text="Copy the token from Batch Buddy after preparing the Live Activity. The .p8 key stays on this computer.", style="CardMuted.TLabel", wraplength=620).grid(row=4, column=0, columnspan=2, sticky="w", pady=(8, 0))

        buttons = ttk.Frame(root)
        buttons.pack(fill="x", pady=14)
        self.start_button = ttk.Button(buttons, text="Start live monitor", command=self._start, style="Accent.TButton")
        self.start_button.pack(side="left")
        self.stop_button = ttk.Button(buttons, text="Stop", command=self._stop, state="disabled", style="Stop.TButton")
        self.stop_button.pack(side="left", padx=8)
        self.status = tk.StringVar(value="Ready. Enter credentials, then start the monitor.")
        ttk.Label(root, textvariable=self.status, style="Muted.TLabel", wraplength=500).pack(anchor="w")

        card = ttk.LabelFrame(root, text="Latest real batch", padding=18, style="Card.TLabelframe")
        card.pack(fill="x", pady=(18, 0))
        self.latest = tk.StringVar(value="No batch received yet.")
        self.latest_label = ttk.Label(card, textvariable=self.latest, font=("Segoe UI", 15, "bold"), justify="left", style="Card.TLabel")
        self.latest_label.pack(anchor="w")
        decision_buttons = ttk.Frame(card)
        decision_buttons.pack(fill="x", pady=(14, 0))
        ttk.Button(decision_buttons, text="Mark completed", command=lambda: self._mark_latest("completed"), style="Accent.TButton").pack(side="left")
        ttk.Button(decision_buttons, text="Mark skipped", command=lambda: self._mark_latest("skipped")).pack(side="left", padx=8)

        stats = ttk.LabelFrame(root, text="Session statistics", padding=14, style="Card.TLabelframe")
        stats.pack(fill="x", pady=(14, 0))
        self.stats = tk.StringVar()
        ttk.Label(stats, textvariable=self.stats, style="Card.TLabel", font=("Segoe UI", 11), justify="left").pack(anchor="w")
        self._refresh_stats()

        history = ttk.LabelFrame(root, text="Batch history", padding=14, style="Card.TLabelframe")
        history.pack(fill="both", expand=True, pady=(14, 0))
        columns = ("status", "time", "recommendation", "pay", "net", "rate", "distance")
        self.history_table = ttk.Treeview(history, columns=columns, show="headings", height=9)
        headings = {
            "status": "Status", "time": "Observed", "recommendation": "Decision",
            "pay": "Pay", "net": "Net", "rate": "$/hr", "distance": "Distance",
        }
        widths = {"status": 100, "time": 145, "recommendation": 120, "pay": 75, "net": 75, "rate": 75, "distance": 90}
        for column in columns:
            self.history_table.heading(column, text=headings[column])
            self.history_table.column(column, width=widths[column], anchor="w")
        self.history_table.pack(fill="both", expand=True, side="left")
        scrollbar = ttk.Scrollbar(history, orient="vertical", command=self.history_table.yview)
        scrollbar.pack(fill="y", side="right")
        self.history_table.configure(yscrollcommand=scrollbar.set)
        self.history_table.bind("<<TreeviewSelect>>", self._select_history_row)
        self.details = tk.StringVar(value="Select a batch to see its full recorded details.")
        ttk.Label(root, textvariable=self.details, style="Muted.TLabel", justify="left", wraplength=760).pack(anchor="w", pady=(10, 0))
        self._refresh_history()

        ttk.Label(root, text="Accept only opens Shopper. Reject performs no Shopper action. The monitor must stay running and online to discover new batches.", style="Muted.TLabel", wraplength=500).pack(anchor="w", pady=(18, 0))

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
        self.stats.set(
            f"Offers seen: {int(summary['offers'])}    Completed: {int(summary['completed'])}\n"
            f"Gross: ${summary['gross']:.2f}    Net estimate: ${summary['net']:.2f}\n"
            f"Distance: {summary['distance']:.1f} km    Avg completed rate: ${summary['average_hourly']:.2f}/hr"
        )

    def _close(self) -> None:
        self._stop()
        self.destroy()


if __name__ == "__main__":
    BatchBuddyMonitorApp().mainloop()
