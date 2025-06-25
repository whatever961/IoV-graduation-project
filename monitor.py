import os
import psutil
import time
import csv
from datetime import datetime

class Monitor:
    def __init__(self, interval=5.0, logfile="monitor_log.csv"):
        self.process = psutil.Process(os.getpid())
        self.interval = interval  # seconds between logs
        self.logfile = logfile
        self.start_time = time.time()
        self.end_time = None
        self.log_data = []

    def estimate_mqtt_packet(self, topic, payload):
        header = 2  # MQTT fixed header size (simplified)
        topic_size = len(topic.encode("utf-8")) + 2
        payload_size = len(payload.encode("utf-8"))
        return header + topic_size + payload_size

    def log(self, sim_time, mqtt_sent_now, mqtt_recv_now):
        cpu = self.process.cpu_percent(interval=None)
        entry = {
            "real_time": datetime.now().strftime("%Y-%m-%d, %H:%M:%S"),
            "sim_time": sim_time,
            "cpu": round(cpu, 2),
            "mqtt_sent": mqtt_sent_now,
            "mqtt_recv": mqtt_recv_now,
        }
        self.log_data.append(entry)

    def save(self):
        if not self.log_data:
            return

        with open(self.logfile, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=self.log_data[0].keys())
            writer.writeheader()
            writer.writerows(self.log_data)
        print(f"[Monitor] Log saved to {self.logfile}")
        print("end_time - start_time = " + (self.end_time - self.start_time))
