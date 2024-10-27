from .ONU import ONU
from typing import Literal


TIMER_MAX = 1_000_000


class OLT:
    onus: list[ONU]
    time_distribution: list[float]
    time: float


    def __init__(
                self,
                onus: list[ONU],
                time_distribution: list[float]
            ):
        if (len(time_distribution) != len(onus)):
            raise TypeError("Time distribution and ONU's array differ in length")
        self.onus = onus
        self.time_distribution = time_distribution


    def fitness_function(self):
        val = 0.0
        for onu in self.onus:
            val += onu.WAITED
        return 1 / val

    def get_next_event(self):
        next_onu_event_index: int = 0
        next_onu_event_time: float = float('inf')
        min_delta: float = float('inf')
        next_onu_event_type: Literal['IDLE', 'MESSAGE'] = 'IDLE'

        for i in range(len(self.onus)):
            onu = self.onus[i]
            event_type, event_time = onu.get_next_event()
            delta: float
            if (event_time < self.time):
                delta = event_time + (TIMER_MAX - self.time)
            else:
                delta = event_time - self.time

            if (delta < min_delta):
                min_delta = delta
                next_onu_event_time = event_time
                next_onu_event_index = i
                next_onu_event_type = event_type
        return (
            next_onu_event_index,
            next_onu_event_time,
            next_onu_event_type
        )



    def DBA(self):
        pass


    def schedule_messages(self):
        pass


    def update(self):
        pass
