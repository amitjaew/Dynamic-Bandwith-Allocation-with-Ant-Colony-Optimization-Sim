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

            
    def round(self):
        for i in range(len(self.time_distribution)):
            print(f'Time Window for ONU: {i}')
            onu = self.onus[i]
            time_window = self.time_distribution[i]
            ends_at: float = self.time + time_window

            def end_flag(evt_time):
                return (
                    evt_time < ends_at or 
                    (ends_at < 0.1 * TIMER_MAX and 0.9 < evt_time)
                )
            event_idx, event_time, event_name = self.get_next_event()
            while end_flag(event_time):
                print(f'Event: {event_name} at ONU {event_idx}')
                event_onu = self.onus[i]
                if (event_idx == i):
                    # Manage event at allowed ONU
                    pass
                else:
                    # Manage event at un-allowed ONU
                    pass
            event_idx, event_time, event_name = self.get_next_event()


    def round_scheduler(self, N):
        for _ in range(N):
            self.round()


    def fitness_function(self):
        val = 0.0
        for onu in self.onus:
            val += onu.WAITED
        return 1 / val


    def optimizer(self):
        fit = self.fitness_function()


    def DBA(self, N, K):
        for _ in range(K):
            # Reset ONU waited
            for onu in self.onus:
                onu.WAITED = 0.0

            self.round_scheduler(N)
            self.optimizer()

