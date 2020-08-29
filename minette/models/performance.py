from time import time
from ..serializer import Serializable


class PerformanceInfo(Serializable):
    """
    Performance information of each steps

    Attributes
    ----------
    start_time : float
        Unix epoch seconds at start
    ticks : list
        Seconds since start_time
    milliseconds : int
        Total processing time in milliseconds
    """
    def __init__(self):
        self.start_time = time()
        self.ticks = []
        self.milliseconds = 0

    def append(self, comment):
        """
        Append current performance timestamp

        Parameters
        ----------
        comment : str
            Comment to identify each steps
        """
        self.ticks.append((comment, time() - self.start_time))
        self.milliseconds = int(self.ticks[-1][1] * 1000)
