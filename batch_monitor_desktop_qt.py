from __future__ import annotations

import json
import os
import queue
import sys
import threading
import webbrowser
from datetime import datetime
from pathlib import Path

from PySide6.QtCore import QPointF, QRectF, Qt, QTimer, Signal
from PySide6.QtGui import QColor, QFont, QIcon, QPainter, QPen, QRadialGradient
from PySide6.QtWidgets import (
    QApplication,
    QFileDialog,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMainWindow,
    QMessageBox,
    QProgressBar,
    QPushButton,
    QScrollArea,
    QSizePolicy,
    QSpacerItem,
    QTableWidget,
    QTableWidgetItem,
    QTabWidget,
    QVBoxLayout,
    QWidget,
)

from activitysmith import ActivitySmith
from batch_history import BatchHistory
from batch_monitor_core import BatchMonitor, BatchResult, MonitorConfig


CONFIG_PATH = Path(os.environ.get("APPDATA", Path.home())) / "BatchBuddy" / "monitor.json"
HISTORY_PATH = Path(os.environ.get("APPDATA", Path.home())) / "BatchBuddy" / "history.sqlite3"
BG = "#071017"
SURFACE = "#0d1b25"
SURFACE_2 = "#112734"
BORDER = "#1d3b49"
TEXT = "#edf7f8"
MUTED = "#8ca6af"
CYAN = "#63e6ff"
GREEN = "#43dfaa"
AMBER = "#ffc266"
RED = "#ff7180"


def asset_path(name: str) -> Path:
    root = Path(getattr(sys, "_MEIPASS", Path(__file__).resolve().parent))
    return root / "assets" / name


class RadarWidget(QWidget):
    def __init__(self, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.phase = 0
        self.signal = 0.0
        self.active = False
        self.setMinimumHeight(210)
        self.setSizePolicy(QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Fixed)
        self.timer = QTimer(self)
        self.timer.timeout.connect(self._tick)
        self.timer.start(45)

    def set_signal(self, value: float, active: bool = True) -> None:
        self.signal = max(0.0, min(1.0, value))
        self.active = active
        self.update()

    def _tick(self) -> None:
        self.phase = (self.phase + 2) % 360
        self.update()

    def paintEvent(self, _event: object) -> None:
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.fillRect(self.rect(), QColor(SURFACE))
        center = QPointF(self.width() / 2, self.height() / 2)
        radius = min(self.width(), self.height()) * 0.38
        painter.setPen(QPen(QColor(BORDER), 1))
        for multiplier in (1.0, 0.72, 0.45):
            painter.drawEllipse(center, radius * multiplier, radius * multiplier)
        painter.drawLine(center.x() - radius, center.y(), center.x() + radius, center.y())
        painter.drawLine(center.x(), center.y() - radius, center.x(), center.y() + radius)
        painter.setPen(QPen(QColor("#214556"), 1, Qt.PenStyle.DotLine))
        painter.drawEllipse(center, radius * 0.2, radius * 0.2)
        if self.active:
            sweep = QRadialGradient(center, radius)
            sweep.setColorAt(0, QColor(99, 230, 255, 28))
            sweep.setColorAt(0.7, QColor(99, 230, 255, 7))
            sweep.setColorAt(1, QColor(99, 230, 255, 0))
            painter.setBrush(sweep)
            painter.setPen(Qt.PenStyle.NoPen)
            painter.drawEllipse(center, radius, radius)
            painter.setPen(QPen(QColor(CYAN), 2))
            painter.drawArc(QRectF(center.x() - radius, center.y() - radius, radius * 2, radius * 2), self.phase * 16, 42 * 16)
            dot_angle = (self.phase - 32) * 3.14159 / 180
            dot = QPointF(center.x() + radius * self.signal * 0.72 * __import__("math").cos(dot_angle), center.y() + radius * self.signal * 0.72 * __import__("math").sin(dot_angle))
            painter.setBrush(QColor(GREEN))
            painter.setPen(QPen(QColor("#b9ffe7"), 2))
            painter.drawEllipse(dot, 6, 6)
        painter.setPen(QColor(TEXT))
        painter.setFont(QFont("Segoe UI", 9, QFont.Weight.DemiBold))
        painter.drawText(QRectF(center.x() - 48, center.y() - 9, 96, 20), Qt.AlignmentFlag.AlignCenter, "LIVE" if self.active else "STANDBY")
        painter.setPen(QColor(MUTED))
        painter.setFont(QFont("Segoe UI", 8))
        painter.drawText(QRectF(12, 12, 110, 18), "OFFER RADAR")


class MetricCard(QFrame):
    def __init__(self, title: str, accent: str = CYAN, parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("metricCard")
        layout = QVBoxLayout(self)
        layout.setContentsMargins(15, 12, 15, 12)
        layout.setSpacing(3)
        self.title = QLabel(title.upper())
        self.title.setObjectName("metricTitle")
        self.value = QLabel("—")
        self.value.setObjectName("metricValue")
        self.value.setStyleSheet(f"color: {accent};")
        layout.addWidget(self.title)
        layout.addWidget(self.value)


class BatchBuddyWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Batch Buddy Radar")
        self.resize(1160, 820)
        self.setMinimumSize(920, 650)
        icon = asset_path("batchbuddy.ico")
        if icon.exists():
            self.setWindowIcon(QIcon(str(icon)))
        self.events: queue.Queue[tuple[str, object]] = queue.Queue()
        self.stop_event: threading.Event | None = None
        self.monitor_thread: threading.Thread | None = None
        self.history = BatchHistory(HISTORY_PATH)
        self.vars = {name: QLineEdit() for name in ("activitysmith", "auth", "cookies", "shopper")}
        self.apns_vars = {name: QLineEdit() for name in ("push_token", "team_id", "key_id", "private_key_path")}
        self.selected_signature: str | None = None
        self._build_ui()
        self._load_config()
        self._refresh_stats()
        self._refresh_history()
        self.event_timer = QTimer(self)
        self.event_timer.timeout.connect(self._drain_events)
        self.event_timer.start(200)
        self.pulse_timer = QTimer(self)
        self.pulse_timer.timeout.connect(self._animate_status)
        self.pulse_timer.start(700)

    def _build_ui(self) -> None:
        self.setStyleSheet(f"""
            QMainWindow, QWidget {{ background:{BG}; color:{TEXT}; font-family:'Segoe UI'; font-size:10pt; }}
            QScrollArea {{ border:0; background:{BG}; }}
            QTabWidget::pane {{ border:1px solid {BORDER}; border-radius:10px; background:{BG}; top:-1px; }}
            QTabBar::tab {{ background:{SURFACE}; color:{MUTED}; border:1px solid {BORDER}; padding:10px 20px; margin-right:4px; border-top-left-radius:8px; border-top-right-radius:8px; }}
            QTabBar::tab:selected {{ background:{SURFACE_2}; color:{CYAN}; border-bottom-color:{SURFACE_2}; }}
            QTabBar::tab:hover {{ color:{TEXT}; }}
            QFrame#surface, QFrame#metricCard {{ background:{SURFACE}; border:1px solid {BORDER}; border-radius:12px; }}
            QFrame#signalCard {{ background:qlineargradient(x1:0,y1:0,x2:1,y2:1, stop:0 #0f2936, stop:1 {SURFACE}); border:1px solid #2c7386; border-radius:14px; }}
            QLabel#brand {{ color:{TEXT}; font-size:21pt; font-weight:700; letter-spacing:1px; }}
            QLabel#eyebrow, QLabel#metricTitle, QLabel#panelTitle {{ color:{MUTED}; font-size:8pt; font-weight:700; letter-spacing:1px; }}
            QLabel#metricValue {{ color:{TEXT}; font-size:20pt; font-weight:700; }}
            QLabel#heroPay {{ color:{TEXT}; font-size:34pt; font-weight:700; }}
            QLabel#muted {{ color:{MUTED}; }}
            QLabel#status {{ color:{MUTED}; padding:5px 9px; border:1px solid {BORDER}; border-radius:9px; }}
            QPushButton {{ background:{SURFACE_2}; color:{TEXT}; border:1px solid {BORDER}; border-radius:8px; padding:8px 13px; font-weight:600; }}
            QPushButton:hover {{ background:#183b4b; border-color:#367487; }}
            QPushButton:pressed {{ background:#0b1a22; }}
            QPushButton#primary {{ background:{CYAN}; color:#041017; border:0; }}
            QPushButton#primary:hover {{ background:#a5f3ff; }}
            QPushButton#danger {{ color:{RED}; }}
            QLineEdit {{ background:#08151e; color:{TEXT}; border:1px solid {BORDER}; border-radius:7px; padding:9px 10px; selection-background-color:#225b70; }}
            QLineEdit:focus {{ border:1px solid {CYAN}; }}
            QProgressBar {{ background:#07131b; border:0; border-radius:4px; height:7px; text-visible:false; }}
            QProgressBar::chunk {{ background:{GREEN}; border-radius:4px; }}
            QTableWidget {{ background:{SURFACE}; color:{TEXT}; border:1px solid {BORDER}; border-radius:8px; gridline-color:#183440; alternate-background-color:#0f222d; selection-background-color:#1a5365; }}
            QHeaderView::section {{ background:{SURFACE_2}; color:{MUTED}; border:0; padding:8px; font-size:8pt; font-weight:700; }}
            QScrollBar:vertical {{ background:{BG}; width:11px; margin:3px; }}
            QScrollBar::handle:vertical {{ background:#244857; border-radius:5px; min-height:35px; }}
            QScrollBar::handle:vertical:hover {{ background:#397184; }}
        """)
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        content = QWidget()
        root = QVBoxLayout(content)
        root.setContentsMargins(18, 16, 18, 18)
        scroll.setWidget(content)
        self.setCentralWidget(scroll)
        tabs = QTabWidget()
        tabs.setDocumentMode(True)
        root.addWidget(tabs)
        radar_page = QWidget()
        page = QVBoxLayout(radar_page)
        page.setContentsMargins(10, 12, 10, 18)
        page.setSpacing(16)
        settings_page = QWidget()
        settings_layout = QVBoxLayout(settings_page)
        settings_layout.setContentsMargins(22, 22, 22, 22)
        settings_layout.setSpacing(14)
        tabs.addTab(radar_page, "Radar")

        top = QHBoxLayout()
        logo = QLabel("⚡")
        logo.setStyleSheet(f"color:{CYAN}; font-size:26pt; font-weight:700;")
        top.addWidget(logo)
        brand = QLabel("BATCH BUDDY")
        brand.setObjectName("brand")
        top.addWidget(brand)
        radar = QLabel("  /  RADAR")
        radar.setObjectName("muted")
        radar.setStyleSheet(f"color:{CYAN}; font-weight:600;")
        top.addWidget(radar)
        top.addItem(QSpacerItem(20, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.status_badge = QLabel("●  OFFLINE")
        self.status_badge.setObjectName("status")
        top.addWidget(self.status_badge)
        self.start_button = QPushButton("Start monitor")
        self.start_button.setObjectName("primary")
        self.start_button.clicked.connect(self._start)
        top.addWidget(self.start_button)
        self.stop_button = QPushButton("Stop")
        self.stop_button.setObjectName("danger")
        self.stop_button.setEnabled(False)
        self.stop_button.clicked.connect(self._stop)
        top.addWidget(self.stop_button)
        page.addLayout(top)
        self.status_line = QLabel("Ready. Enter credentials, then start the monitor.")
        self.status_line.setObjectName("muted")
        page.addWidget(self.status_line)

        eyebrow = QLabel("LIVE OVERVIEW")
        eyebrow.setObjectName("eyebrow")
        page.addWidget(eyebrow)
        metrics = QHBoxLayout()
        metrics.setSpacing(10)
        self.metric_cards = [MetricCard("Offers today"), MetricCard("Completed", GREEN), MetricCard("Net estimate", CYAN), MetricCard("Average rate", AMBER)]
        for card in self.metric_cards:
            metrics.addWidget(card)
        page.addLayout(metrics)

        main_row = QHBoxLayout()
        main_row.setSpacing(14)
        signal = QFrame()
        signal.setObjectName("signalCard")
        signal_layout = QVBoxLayout(signal)
        signal_layout.setContentsMargins(17, 15, 17, 17)
        signal_layout.setSpacing(10)
        signal_head = QHBoxLayout()
        label = QLabel("TOP SIGNAL")
        label.setObjectName("panelTitle")
        signal_head.addWidget(label)
        signal_head.addItem(QSpacerItem(10, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        self.recommendation = QLabel("WAITING")
        self.recommendation.setStyleSheet(f"color:{MUTED}; font-weight:700;")
        signal_head.addWidget(self.recommendation)
        signal_layout.addLayout(signal_head)
        signal_content = QHBoxLayout()
        self.radar_widget = RadarWidget()
        signal_content.addWidget(self.radar_widget, 4)
        offer = QVBoxLayout()
        self.latest_title = QLabel("No active batch")
        self.latest_title.setStyleSheet(f"font-size:15pt; font-weight:700; color:{TEXT};")
        offer.addWidget(self.latest_title)
        self.latest_detail = QLabel("Waiting for a new offer from the live feed.")
        self.latest_detail.setObjectName("muted")
        self.latest_detail.setWordWrap(True)
        offer.addWidget(self.latest_detail)
        self.live_pay = QLabel("—")
        self.live_pay.setObjectName("heroPay")
        offer.addWidget(self.live_pay)
        self.live_summary = QLabel("No current signal")
        self.live_summary.setObjectName("muted")
        self.live_summary.setWordWrap(True)
        offer.addWidget(self.live_summary)
        self.signal_bar = QProgressBar()
        self.signal_bar.setRange(0, 100)
        self.signal_bar.setValue(0)
        offer.addWidget(self.signal_bar)
        offer.addStretch(1)
        buttons = QHBoxLayout()
        completed = QPushButton("Mark completed")
        completed.setObjectName("primary")
        completed.clicked.connect(lambda: self._mark_latest("completed"))
        skipped = QPushButton("Mark skipped")
        skipped.clicked.connect(lambda: self._mark_latest("skipped"))
        buttons.addWidget(completed)
        buttons.addWidget(skipped)
        offer.addLayout(buttons)
        signal_content.addLayout(offer, 5)
        signal_layout.addLayout(signal_content)
        main_row.addWidget(signal, 7)

        inspector = QFrame()
        inspector.setObjectName("surface")
        inspector.setMinimumWidth(238)
        inspector_layout = QVBoxLayout(inspector)
        inspector_layout.setContentsMargins(17, 15, 17, 17)
        title = QLabel("SIGNAL INSPECTOR")
        title.setObjectName("panelTitle")
        inspector_layout.addWidget(title)
        self.inspector = QLabel("Live Activity\nStand by for the next offer.\n\nActivitySmith\nWaiting for monitor start")
        self.inspector.setWordWrap(True)
        self.inspector.setStyleSheet(f"font-size:10pt; color:{TEXT}; line-height:1.5;")
        inspector_layout.addWidget(self.inspector)
        inspector_layout.addStretch(1)
        note = QLabel("Accept only opens Shopper. No batch is accepted automatically.")
        note.setObjectName("muted")
        note.setWordWrap(True)
        inspector_layout.addWidget(note)
        main_row.addWidget(inspector, 3)
        page.addLayout(main_row)

        history_panel = QFrame()
        history_panel.setObjectName("surface")
        history_layout = QVBoxLayout(history_panel)
        history_layout.setContentsMargins(15, 13, 15, 13)
        history_head = QHBoxLayout()
        history_title = QLabel("BATCH HISTORY")
        history_title.setObjectName("panelTitle")
        history_head.addWidget(history_title)
        history_head.addItem(QSpacerItem(10, 1, QSizePolicy.Policy.Expanding, QSizePolicy.Policy.Minimum))
        newest = QLabel("Newest first")
        newest.setObjectName("muted")
        history_head.addWidget(newest)
        history_layout.addLayout(history_head)
        self.history_table = QTableWidget(0, 7)
        self.history_table.setHorizontalHeaderLabels(["Status", "Observed", "Decision", "Pay", "Net", "$/hr", "Distance"])
        self.history_table.setMinimumHeight(180)
        self.history_table.setMaximumHeight(250)
        self.history_table.setAlternatingRowColors(True)
        self.history_table.setSelectionBehavior(QTableWidget.SelectionBehavior.SelectRows)
        self.history_table.setEditTriggers(QTableWidget.EditTrigger.NoEditTriggers)
        self.history_table.verticalHeader().setVisible(False)
        self.history_table.horizontalHeader().setStretchLastSection(True)
        self.history_table.itemSelectionChanged.connect(self._select_history_row)
        history_layout.addWidget(self.history_table)
        self.details = QLabel("Select a batch row to inspect its recorded details.")
        self.details.setObjectName("muted")
        self.details.setWordWrap(True)
        history_layout.addWidget(self.details)
        page.addWidget(history_panel)

        settings_layout.addWidget(self._settings_card("CONNECTION SETTINGS", [("ActivitySmith API key", "activitysmith", True), ("Instacart auth token", "auth", True), ("Instacart cookies", "cookies", True), ("Shopper ID", "shopper", False)]))
        native = self._settings_card("NATIVE LIVE ACTIVITY / CARPLAY (OPTIONAL)", [("ActivityKit push token", "push_token", True), ("Apple Team ID", "team_id", False), ("Apple Key ID", "key_id", False), ("Private .p8 key path", "private_key_path", False)], apns=True)
        settings_layout.addWidget(native)
        settings_actions = QHBoxLayout()
        self.save_button = QPushButton("Save settings")
        self.save_button.setObjectName("primary")
        self.save_button.clicked.connect(self._save_config_ui)
        settings_actions.addWidget(self.save_button)
        self.save_status = QLabel("Credentials are stored locally on this computer.")
        self.save_status.setObjectName("muted")
        settings_actions.addWidget(self.save_status)
        settings_actions.addStretch(1)
        settings_layout.addLayout(settings_actions)
        footer = QLabel("Batch Buddy keeps monitoring while minimized. Leave the computer online for live offer detection.")
        footer.setObjectName("muted")
        settings_layout.addWidget(footer)
        settings_layout.addStretch(1)
        tabs.addTab(settings_page, "Settings")

        smith_page = QWidget()
        smith_layout = QVBoxLayout(smith_page)
        smith_layout.setContentsMargins(22, 22, 22, 22)
        smith_layout.setSpacing(14)
        smith_title = QLabel("ACTIVITYSMITH CONTROL ROOM")
        smith_title.setObjectName("eyebrow")
        smith_layout.addWidget(smith_title)
        smith_intro = QLabel("ActivitySmith is the live delivery layer for Batch Buddy notifications, Live Activities, and metric widgets.")
        smith_intro.setObjectName("muted")
        smith_intro.setWordWrap(True)
        smith_layout.addWidget(smith_intro)
        smith_actions = QHBoxLayout()
        self.test_smith_button = QPushButton("Send test notification")
        self.test_smith_button.setObjectName("primary")
        self.test_smith_button.clicked.connect(self._test_activitysmith)
        smith_actions.addWidget(self.test_smith_button)
        self.smith_test_status = QLabel("Not tested yet")
        self.smith_test_status.setObjectName("muted")
        smith_actions.addWidget(self.smith_test_status)
        smith_actions.addStretch(1)
        smith_layout.addLayout(smith_actions)
        smith_live_grid = QGridLayout()
        smith_live_grid.setSpacing(12)
        self.smith_connection_panel, self.smith_connection_value, self.smith_connection_detail = self._smith_status_panel("Connection", "Not tested", "Use the test button to verify the API key.")
        self.smith_delivery_panel, self.smith_delivery_value, self.smith_delivery_detail = self._smith_status_panel("Last delivery", "No delivery yet", "Waiting for a valid batch.")
        self.smith_activity_panel, self.smith_activity_value, self.smith_activity_detail = self._smith_status_panel("Live Activity", "Standby", "No current native activity update.")
        self.smith_metrics_panel, self.smith_metrics_value, self.smith_metrics_detail = self._smith_status_panel("Metric widgets", "—", "Latest pay · net · hourly")
        smith_live_grid.addWidget(self.smith_connection_panel, 0, 0)
        smith_live_grid.addWidget(self.smith_delivery_panel, 0, 1)
        smith_live_grid.addWidget(self.smith_activity_panel, 1, 0)
        smith_live_grid.addWidget(self.smith_metrics_panel, 1, 1)
        smith_layout.addLayout(smith_live_grid)
        self.smith_log = QLabel("Delivery log\nNo ActivitySmith events recorded in this session.")
        self.smith_log.setObjectName("muted")
        self.smith_log.setWordWrap(True)
        smith_layout.addWidget(self.smith_log)
        open_smith = QPushButton("Open ActivitySmith")
        open_smith.clicked.connect(lambda: webbrowser.open("https://activitysmith.com/app"))
        smith_layout.addWidget(open_smith, alignment=Qt.AlignmentFlag.AlignLeft)
        smith_grid = QGridLayout()
        smith_grid.setSpacing(12)
        for index, (title, detail) in enumerate((("Push notifications", "Immediate offer alerts with Accept and Reject actions."), ("Live Activity", "Persistent current-batch state on your iPhone."), ("Metric widgets", "Latest pay, net estimate, and hourly estimate."), ("Tags + metadata", "Searchable batch context in ActivitySmith history."))):
            panel = QFrame()
            panel.setObjectName("surface")
            panel_layout = QVBoxLayout(panel)
            panel_layout.setContentsMargins(16, 16, 16, 16)
            panel_title = QLabel(title)
            panel_title.setStyleSheet(f"color:{CYAN}; font-size:11pt; font-weight:700;")
            panel_layout.addWidget(panel_title)
            panel_detail = QLabel(detail)
            panel_detail.setObjectName("muted")
            panel_detail.setWordWrap(True)
            panel_layout.addWidget(panel_detail)
            smith_grid.addWidget(panel, index // 2, index % 2)
        smith_layout.addLayout(smith_grid)
        smith_layout.addStretch(1)
        tabs.insertTab(1, smith_page, "ActivitySmith")

    def _smith_status_panel(self, title: str, value: str, detail: str) -> tuple[QFrame, QLabel, QLabel]:
        panel = QFrame()
        panel.setObjectName("surface")
        layout = QVBoxLayout(panel)
        layout.setContentsMargins(15, 13, 15, 13)
        heading = QLabel(title.upper())
        heading.setObjectName("panelTitle")
        value_label = QLabel(value)
        value_label.setStyleSheet(f"color:{CYAN}; font-size:14pt; font-weight:700;")
        detail_label = QLabel(detail)
        detail_label.setObjectName("muted")
        detail_label.setWordWrap(True)
        layout.addWidget(heading)
        layout.addWidget(value_label)
        layout.addWidget(detail_label)
        return panel, value_label, detail_label

    def _settings_card(self, title: str, fields: list[tuple[str, str, bool]], apns: bool = False) -> QFrame:
        card = QFrame()
        card.setObjectName("surface")
        layout = QGridLayout(card)
        layout.setContentsMargins(15, 13, 15, 13)
        layout.setHorizontalSpacing(14)
        layout.setVerticalSpacing(8)
        heading = QLabel(title)
        heading.setObjectName("panelTitle")
        layout.addWidget(heading, 0, 0, 1, 3)
        for row, (label, name, secret) in enumerate(fields, start=1):
            caption = QLabel(label)
            caption.setObjectName("muted")
            entry = self.apns_vars[name] if apns else self.vars[name]
            entry.setEchoMode(QLineEdit.EchoMode.Password if secret else QLineEdit.EchoMode.Normal)
            layout.addWidget(caption, row, 0)
            layout.addWidget(entry, row, 1)
            if name == "private_key_path":
                browse = QPushButton("Browse")
                browse.clicked.connect(lambda _checked=False, field=entry: self._browse_key(field))
                layout.addWidget(browse, row, 2)
            else:
                layout.addWidget(QWidget(), row, 2)
        if apns:
            note = QLabel("The Apple key stays local. ActivitySmith notifications work without APNs setup.")
            note.setObjectName("muted")
            note.setWordWrap(True)
            layout.addWidget(note, len(fields) + 1, 0, 1, 3)
        layout.setColumnStretch(1, 1)
        return card

    def _browse_key(self, field: QLineEdit) -> None:
        path, _ = QFileDialog.getOpenFileName(self, "Select Apple private key", "", "Apple key (*.p8);;All files (*.*)")
        if path:
            field.setText(path)

    def _load_config(self) -> None:
        try:
            values = json.loads(CONFIG_PATH.read_text(encoding="utf-8"))
            for name, value in values.items():
                if name in self.vars:
                    self.vars[name].setText(str(value))
                if name in self.apns_vars:
                    self.apns_vars[name].setText(str(value))
        except (FileNotFoundError, json.JSONDecodeError, OSError):
            self.vars["shopper"].setText("40757189")

    def _save_config(self) -> None:
        CONFIG_PATH.parent.mkdir(parents=True, exist_ok=True)
        values = {name: field.text() for name, field in self.vars.items()}
        values.update({name: field.text() for name, field in self.apns_vars.items()})
        CONFIG_PATH.write_text(json.dumps(values), encoding="utf-8")

    def _save_config_ui(self) -> None:
        self._save_config()
        self.save_status.setText("Saved locally. These values will be restored next time Batch Buddy opens.")

    def _test_activitysmith(self) -> None:
        api_key = self.vars["activitysmith"].text().strip()
        if not api_key:
            self.smith_test_status.setText("Enter an ActivitySmith API key in Settings first.")
            return
        self.test_smith_button.setEnabled(False)
        self.smith_test_status.setText("Sending test…")
        try:
            smith = ActivitySmith(api_key=api_key)
            smith.notifications.send(title="Batch Buddy connected", message="ActivitySmith is connected and ready for live batch alerts.", tags=["batch-buddy", "connection-test"])
            self.smith_test_status.setText("Test sent successfully. Check your iPhone.")
            self.smith_connection_value.setText("CONNECTED")
            self.smith_connection_detail.setText("API key accepted by ActivitySmith.")
            self.smith_delivery_value.setText("TEST SENT")
            self.smith_delivery_detail.setText("Check the paired ActivitySmith iPhone.")
            self.smith_log.setText("Delivery log\n✓ Test notification sent successfully.")
            self.inspector.setText("Live Activity\nStand by for the next offer.\n\nActivitySmith\nConnected · test sent")
        except Exception as error:
            self.smith_test_status.setText(f"Test failed: {error}")
            self.inspector.setText("Live Activity\nStand by for the next offer.\n\nActivitySmith\nConnection test failed")
        finally:
            self.test_smith_button.setEnabled(True)

    def _start(self) -> None:
        values = {name: field.text().strip() for name, field in self.vars.items()}
        if not all(values.values()):
            QMessageBox.warning(self, "Missing connection details", "Enter the ActivitySmith key, Instacart token, cookies, and Shopper ID.")
            return
        self._save_config()
        apns = {name: field.text().strip() for name, field in self.apns_vars.items()}
        config = MonitorConfig(activitysmith_api_key=values["activitysmith"], auth_token=values["auth"], cookies=values["cookies"], shopper_id=values["shopper"], live_activity_push_token=apns["push_token"], apple_team_id=apns["team_id"], apple_key_id=apns["key_id"], apple_private_key_path=apns["private_key_path"])
        self.stop_event = threading.Event()
        monitor = BatchMonitor(config, on_batch=lambda result: self.events.put(("batch", result)), on_status=lambda message: self.events.put(("status", message)))
        self.monitor_thread = threading.Thread(target=monitor.run, args=(self.stop_event,), daemon=True)
        self.monitor_thread.start()
        self.start_button.setEnabled(False)
        self.stop_button.setEnabled(True)
        self.radar_widget.set_signal(0.35, True)
        self.inspector.setText("Live Activity\nWaiting for the next valid offer.\n\nActivitySmith\nConfigured · monitor running")
        self.smith_connection_value.setText("MONITORING")
        self.smith_connection_detail.setText("Credentials loaded; waiting for a valid offer.")
        self.smith_delivery_value.setText("WAITING")
        self.smith_delivery_detail.setText("No valid batch has been delivered yet.")
        self.smith_activity_value.setText("STANDBY")
        self.smith_activity_detail.setText("Will update when a valid batch is parsed.")

    def _stop(self) -> None:
        if self.stop_event:
            self.stop_event.set()
        self.start_button.setEnabled(True)
        self.stop_button.setEnabled(False)
        self.radar_widget.set_signal(0.0, False)

    def _drain_events(self) -> None:
        try:
            while True:
                kind, payload = self.events.get_nowait()
                if kind == "status":
                    self.status_line.setText(str(payload))
                    if "ActivitySmith" in str(payload) and ("sent" in str(payload) or "updated" in str(payload)):
                        self.inspector.setText("Live Activity\nCurrent offer channel ready.\n\nActivitySmith\nConnected · live update sent")
                        self.smith_delivery_value.setText("DELIVERED")
                        self.smith_delivery_detail.setText(str(payload))
                        self.smith_log.setText(f"Delivery log\n✓ {payload}")
                elif isinstance(payload, BatchResult):
                    result = payload
                    self.history.record(result)
                    self.latest_title.setText(f"${result.pay:.2f} batch")
                    self.latest_detail.setText(f"{result.distance:.1f} km  ·  {result.items} items  ·  observed {datetime.fromtimestamp(result.observed_at).strftime('%H:%M:%S')}")
                    self.live_pay.setText(f"${result.pay:.2f}")
                    self.live_summary.setText(f"Net estimate ${result.net_estimate:.2f}  ·  ${result.hourly_estimate:.2f}/hr  ·  ${result.pay_per_km:.2f}/km")
                    self.recommendation.setText(result.recommendation)
                    self.recommendation.setStyleSheet(f"color:{GREEN if result.recommendation == '✅ ACCEPT' else AMBER}; font-weight:700;")
                    signal = min(1.0, max(0.0, result.hourly_estimate / 40))
                    self.signal_bar.setValue(int(signal * 100))
                    self.radar_widget.set_signal(signal, True)
                    self.inspector.setText(f"Live Activity\n{result.recommendation}\n\nPay\n${result.pay:.2f}\n\nNet estimate\n${result.net_estimate:.2f}\n\nHourly estimate\n${result.hourly_estimate:.2f}\n\nActivitySmith\nUpdated")
                    self.smith_activity_value.setText("UPDATED")
                    self.smith_activity_detail.setText("Current batch Live Activity state sent.")
                    self.smith_metrics_value.setText(f"${result.pay:.2f}  ·  ${result.net_estimate:.2f}  ·  ${result.hourly_estimate:.2f}/hr")
                    self.smith_metrics_detail.setText("Pay · net estimate · hourly estimate")
                    self._refresh_stats()
                    self._refresh_history()
        except queue.Empty:
            pass

    def _refresh_stats(self) -> None:
        summary = self.history.summary()
        values = (str(int(summary["offers"])), str(int(summary["completed"])), f"${summary['net']:.2f}", f"${summary['average_hourly']:.2f}")
        if hasattr(self, "metric_cards"):
            for card, value in zip(self.metric_cards, values):
                card.value.setText(value)

    def _refresh_history(self) -> None:
        if not hasattr(self, "history_table"):
            return
        rows = self.history.recent()
        self.history_table.setRowCount(len(rows))
        for row_index, batch in enumerate(rows):
            status = {"completed": "✓ Completed", "skipped": "↗ Skipped"}.get(str(batch["status"]), "• Offered")
            observed = datetime.fromtimestamp(float(batch["observed_at"])).strftime("%b %d  %H:%M:%S")
            values = (status, observed, str(batch["recommendation"]), f"${float(batch['pay']):.2f}", f"${float(batch['net_estimate']):.2f}", f"${float(batch['hourly_estimate']):.2f}", f"{float(batch['distance']):.1f} km")
            for column, value in enumerate(values):
                self.history_table.setItem(row_index, column, QTableWidgetItem(value))
            self.history_table.item(row_index, 0).setData(Qt.ItemDataRole.UserRole, str(batch["signature"]))
        self.history_table.resizeColumnsToContents()

    def _select_history_row(self) -> None:
        selected = self.history_table.selectedItems()
        if not selected:
            return
        row = selected[0].row()
        signature = self.history_table.item(row, 0).data(Qt.ItemDataRole.UserRole)
        self.selected_signature = signature
        batch = next((item for item in self.history.recent() if item["signature"] == signature), None)
        if batch:
            observed = datetime.fromtimestamp(float(batch["observed_at"])).strftime("%Y-%m-%d %H:%M:%S")
            self.details.setText(f"{str(batch['status']).upper()}  ·  {observed}  ·  ${float(batch['pay']):.2f} pay  ·  {float(batch['distance']):.1f} km  ·  {int(batch['items'])} items  ·  ${float(batch['net_estimate']):.2f} net  ·  ${float(batch['hourly_estimate']):.2f}/hr  ·  signature {signature}")

    def _mark_latest(self, status: str) -> None:
        if self.selected_signature:
            self.history.mark(self.selected_signature, status)
        else:
            self.history.mark_latest(status)
        self._refresh_stats()
        self._refresh_history()
        self.status_line.setText(f"Batch marked {status}.")

    def _animate_status(self) -> None:
        running = self.stop_event is not None and not self.stop_event.is_set()
        if running:
            self.status_badge.setText("◉  MONITORING")
            self.status_badge.setStyleSheet(f"color:{GREEN}; border:1px solid #256b5b; padding:5px 9px; border-radius:9px;")
        else:
            self.status_badge.setText("●  OFFLINE")
            self.status_badge.setStyleSheet(f"color:{MUTED}; border:1px solid {BORDER}; padding:5px 9px; border-radius:9px;")

    def closeEvent(self, event: object) -> None:
        self._stop()
        event.accept()


def main() -> None:
    app = QApplication(sys.argv)
    app.setApplicationName("Batch Buddy Radar")
    app.setWindowIcon(QIcon(str(asset_path("batchbuddy.ico"))))
    window = BatchBuddyWindow()
    window.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
