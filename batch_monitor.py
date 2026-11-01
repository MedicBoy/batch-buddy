import os
import threading

from batch_monitor_core import BatchMonitor, MonitorConfig


def main() -> None:
    config = MonitorConfig(
        activitysmith_api_key=os.environ["ACTIVITYSMITH_API_KEY"],
        auth_token=os.environ["INSTACART_AUTH_TOKEN"],
        cookies=os.environ["INSTACART_COOKIES"],
        shopper_id=os.environ.get("INSTACART_SHOPPER_ID", "40757189"),
    )
    stop_event = threading.Event()
    monitor = BatchMonitor(config, on_status=print)
    try:
        monitor.run(stop_event)
    except KeyboardInterrupt:
        stop_event.set()


if __name__ == "__main__":
    main()
