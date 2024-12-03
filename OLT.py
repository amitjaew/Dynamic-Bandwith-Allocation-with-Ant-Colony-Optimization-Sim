from ONU import ONU
from constants import TIMER_MAX
from typing import Literal, Any, List
from time import sleep, time
import numpy as np


# GPON upstream = 1.25 [Gbps]
# => 1 bit cada 0.8 [ns] = 0.8e-3 [microsegundos]

class OptimizerACO:
    def __init__(
                self,
                time_paths,
                n_onus: int,
                forget_factor: float = 0.7,
                update_factor: float = 0.3
            ):
        self.time_paths = np.array(time_paths, dtype='float64')
        self.forget_factor = forget_factor
        self.update_factor = update_factor
        self.n_onus = n_onus
        self.pheromones = np.ones((
            n_onus,
            len(time_paths)
        )) / len(time_paths)

    def update(self, demmand):
        self.pheromones *= self.forget_factor
        for i in range(self.n_onus):
            delta = np.abs(self.time_paths - demmand[i]) + 0.01
            # print(f'ONU {i} deltas:')
            # print(delta)
            self.pheromones[i] += 1/delta * self.update_factor
        # print(f'demmand: {demmand}')
        # print(f'update: \n{self.time_paths}\n{self.pheromones}')
        #sleep(1)

        # for i in range(len(self.time_paths)):
        #     delta = np.abs(demmand - self.time_paths) + 0.1
        #     self.pheromones[i] += 1/delta * self.update_factor

    def get_time_distribution(self):
        valid_indexes = [i for i in range(len(self.time_paths))]
        results = np.zeros(self.n_onus)

        for i in range(self.n_onus):
            ph = self.pheromones[i]
            ph = ph[valid_indexes]
            probs = ph / ph.sum()
            selected_index = np.random.choice(valid_indexes, p=probs)
            valid_indexes.remove(selected_index)
            results[i] = self.time_paths[selected_index]

        #print(f'resuls: {results}')
        #sleep(1)

        return results


class OLT:
    onus: list[ONU]
    time: float
    optimizer: OptimizerACO
    mode: Literal['OPTIMIZED', 'FIXED_DISTRIBUTION']
    verbose: bool = False
    debug: bool = False


    def __init__(
                self,
                onus: list[ONU],
                time_distribution: list[float],
                optimizer: OptimizerACO,
                mode: Literal['OPTIMIZED', 'FIXED_DISTRIBUTION'] = 'OPTIMIZED',
                verbose: bool = False,
                debug: bool = False
            ):
        if (len(time_distribution) != len(onus)):
            raise TypeError("Time distribution and ONU's array differ in length")
        self.onus = onus
        self.mode = mode
        self.verbose = verbose
        self.debug = debug
        self.time_distribution = np.array(time_distribution, dtype='float64')
        self.optimizer = optimizer


    def get_next_message_event(self):
        next_onu_event_index: int = 0
        next_onu_event_time: float = float('inf')
        min_delta: float = float('inf')

        for i in range(len(self.onus)):
            onu = self.onus[i]
            mssg_event_time = onu.get_next_message_event()
            delta: float
            if (mssg_event_time < self.time):
                delta = mssg_event_time + (TIMER_MAX - self.time)
            else:
                delta = mssg_event_time - self.time

            if (delta < min_delta):
                min_delta = delta
                next_onu_event_time = mssg_event_time
                next_onu_event_index = i
        return (
            next_onu_event_index,
            next_onu_event_time
        )

            
    def run_window(self):
        for allowed_onu_idx in range(len(self.time_distribution)):
            if (self.verbose):
                print("-" * 32)
                print(f'Time Window for ONU: {allowed_onu_idx}')
                print("-" * 32)

            allowed_onu = self.onus[allowed_onu_idx]
            time_window = self.time_distribution[allowed_onu_idx]
            window_ends_at: float = self.time + time_window

            if (not allowed_onu.current_message):
                allowed_onu.dequeue_message()
            
            current_message_ends_at = None
            if (allowed_onu.current_message and allowed_onu.current_message_progress != None):
                current_message_ends_at = (
                    self.time +
                    allowed_onu.current_message -
                    allowed_onu.current_message_progress
                ) % TIMER_MAX
                if (self.verbose):
                    print(f'\ttime: {self.time})')
                    print(f'Resuming message from onu {allowed_onu_idx}')
                    print(f'new message ends at {current_message_ends_at}')

            def continue_flag(evt_time):
                return (
                    evt_time < window_ends_at or
                    (window_ends_at < 0.2 * TIMER_MAX and 0.8 * TIMER_MAX < evt_time)
                )

            event_onu_idx, event_time = self.get_next_message_event()
            while continue_flag(event_time):
                while (current_message_ends_at != None and
                        ( current_message_ends_at < event_time or
                          (event_time < 0.2 * TIMER_MAX and 0.8 * TIMER_MAX < current_message_ends_at)
                       )):
                    self.time = current_message_ends_at
                    allowed_onu.dequeue_message()
                    
                    current_message_ends_at = None
                    if (allowed_onu.current_message and allowed_onu.current_message_progress != None):
                        current_message_ends_at = (
                            self.time +
                            allowed_onu.current_message -
                            allowed_onu.current_message_progress
                        ) % TIMER_MAX
                        if (self.verbose):
                            print(f'\ttime: {event_time})')
                            print(f'Message intent from ONU: {event_onu_idx}')
                            print(f'new message ends at {current_message_ends_at}')


                if (self.verbose):
                    print(f'\ttime: {event_time})')
                    print(f'Message intent from ONU: {event_onu_idx}')
                self.time = event_time
                self.onus[event_onu_idx].enqueue_message()

                # Manage message event at allowed ONU if no message sending (=> no messages enqueued)
                if (event_onu_idx == allowed_onu_idx and current_message_ends_at == None):
                    allowed_onu.dequeue_message()
                    if (allowed_onu.current_message and allowed_onu.current_message_progress != None):
                        current_message_ends_at = (
                            self.time +
                            allowed_onu.current_message -
                            allowed_onu.current_message_progress
                        ) % TIMER_MAX
                        if (self.verbose):
                            print(current_message_ends_at)


                event_onu_idx, event_time = self.get_next_message_event()

            self.time = window_ends_at


    def round(self, N):
        for _ in range(N):
            if (self.debug):
                sleep(1)
            self.run_window()

        if (self.verbose):
            for i in range(len(self.onus)):
                print(f'onu {i} queue: {len(self.onus[i].message_queue)}')
        
        if (self.mode == 'OPTIMIZED'):
            demmand = np.zeros(len(self.onus))
            for i in range(len(self.onus)):
                demmand[i] = self.onus[i].demmand
                self.onus[i].flush_demmand()
            demmand /= N
            self.optimizer.update(demmand=demmand)
            self.time_distribution = self.optimizer.get_time_distribution()
            # print('-' * 32)
            # print(f'DEMMAND: {demmand}')
            # print(f'UPDATE TIME DIST: {self.time_distribution}')
            # print('-' * 32)



    def simulate(self, n_rounds=100_000, round_size=10):
        self.time = 0.0
        for _ in range(n_rounds):
            self.round(N=round_size)


if __name__ == '__main__':
    onus = [
        ONU(),
        ONU()
    ]
    base_time_dist = [
        120e-3,
        120e-3
    ]
    time_paths = np.arange(10e-3, 420e-3, 10e-3)
    optimizer = OptimizerACO(
        time_paths=time_paths,
        n_onus=len(onus)
    )
    olt = OLT(
        onus=onus,
        time_distribution=[0.5, 0.5],
        optimizer=optimizer,
        mode='OPTIMIZED',
        verbose=False,
        debug=False
    )
    t_start = time()
    olt.simulate(
        n_rounds=10_000,
        round_size=10
    )
    for onu in olt.onus:
        print(f'queue len: {len(onu.message_queue)}')
        p_blocked = onu.BLOCKED_MESSAGES / (onu.SENT_MESSAGES + onu.BLOCKED_MESSAGES)
        print(f'blocked probs: {p_blocked}')
    t_end = time()

    print(f'elapsed {t_end - t_start} seconds')
