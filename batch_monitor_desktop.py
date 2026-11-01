from __future__ import annotations

import json
import os
import queue
import threading
import tkinter as tk
from pathlib import Path
from tkinter import messagebox, ttk

from batch_monitor_core import BatchMonitor, BatchResult, MonitorConfig


CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "BatchBuddy" / "monitor.json"


class BatchBuddyMonitorApp(tk.Tk):
    def __init__(self) -> None:
        super().__init__()
        self.title("Batch Buddy Monitor")
        self.geometry("620x700")
        self.minsize(540, 620)
        self.configure(bg="#07131d")
        self._events: queue.Queue[tuple[str, object]] = queue.Queue()
        self._stop_event: threading.Event | None = None
        self._thread: threading.Thread | None = None
        self._vars = {name: tk.StringVar() for name in ("activitysmith", "auth", "cookies", "shopper")}
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

        ttk.Label(root, text="Accept only opens Shopper. Reject performs no Shopper action. The monitor must stay running and online to discover new batches.", style="Muted.TLabel", wraplength=500).pack(anchor="w", pady=(18, 0))

    def _field(self, parent: ttk.LabelFrame, row: int, label: str, name: str, secret: bool) -> None:
        ttk.Label(parent, text=label, style="Card.TLabel").grid(row=row, column=0, sticky="w", pady=5)
        entry = ttk.Entry(parent, textvariable=self._vars[name], show="•" if secret else "")
        entry.grid(row=row, column=1, sticky="ew", padx=(12, 0), pady=5)
        parent.columnconfigure(1, weight=1)

    def _load_config(self) -> None:
        try:
            values = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for name, value in values.items():
                if name in self._vars:
                    self._vars[name].set(value)
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self._vars["shopper"].set("40757189")

    def _save_config(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        CONFIG_PATH.write_text(json.dumps({name: var.get() for name, var in self._vars.items()}), encoding="utf-8")

    def _start(self) -> None:
        values = {name: var.get().strip() for name, var in self._vars.items()}
        if not all(values.values()):
            messagebox.showerror("Missing connection details", "Enter the ActivitySmith key, Instacart token, cookies, and Shopper ID.")
            return
        self._save_config()
        config = MonitorConfig(values["activitysmith"], values["auth"], values["cookies"], values["shopper"])
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
                        self.latest.set(f"{result.recommendation}\nPay ${result.pay:.2f}  •  {result.distance:.1f} km\nNet ${result.net_estimate:.2f}  •  ${result.hourly_estimate:.2f}/hr")
                        self.latest_label.configure(foreground="#5de3ff" if result.recommendation == "✅ ACCEPT" else "#ffb454")
        except queue.Empty:
            pass
        self.after(250, self._drain_events)

    def _close(self) -> None:
        self._stop()
        self.destroy()


if __name__ == "__main__":
    BatchBuddyMonitorApp().mainloop()
