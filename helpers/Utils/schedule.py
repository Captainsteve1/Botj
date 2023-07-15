import logging
import time
from datetime import datetime


class schedule:
    def __init__(self, Time: str):
        self.logger = logging.getLogger(__name__)
        self.Time = Time
        
    def time_checker(self):
        try:
            self.timestamp_converter(self.Time)
        except ValueError as e:
            self.logger.info("Error: {}".format(e))
            return False

        if self.timestamp_converter(self.Time) <= self.timestamp_now():
            self.logger.info("Time is in the past, unless you have a time machine!.")
            return False

        return True

    def sleep(self, t: int):
        time.sleep(t)

    def time_corretion(self, time_str: str):
        time_str = time_str[: time_str.index(".")] if "." in time_str else time_str
        return time_str

    def timestamp_now(self):
        return int(datetime.timestamp(datetime.now()))

    def time_now(self):
        return self.time_corretion(str(datetime.now()))

    def timestamp_converter(self, sf: str):
        return int(datetime.strptime(sf, "%Y-%m-%d %H:%M:%S").timestamp())

    def time_converter(self, ts: int):
        return datetime.utcfromtimestamp(ts).strftime("%Y-%m-%d %H:%M:%S")

    def eta(self):
        return self.time_corretion(str(datetime.strptime(self.Time, "%Y-%m-%d %H:%M:%S") - datetime.now()))

    def countdown(self):
        if not self.time_checker():
            return

        while self.timestamp_now() < self.timestamp_converter(self.Time):
            print("Current Time: {} - Start at: {} - eta: {}".format(self.time_now(), self.Time, self.eta()), flush=True, end="\r")
            self.sleep(1)

        print()

        return
