from minette.serializer import JsonSerializable
from time import time


class PerformanceInfo(JsonSerializable):
    def __init__(self):
        self.start_time = time()
        self.ticks = []

    def append(self, comment):
        self.ticks.append((comment, time() - self.start_time))
