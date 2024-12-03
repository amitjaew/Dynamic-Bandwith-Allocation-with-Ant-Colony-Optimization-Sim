from ONU import ONU
from constants import TIMER_MAX
from typing import Literal
from time import sleep, time
import numpy as np
import random


# GPON upstream = 1.25 [Gbps]
# => 1 bit cada 0.8 [ns] = 0.8e-3 [microsegundos]

class OptimizerACO:
    def __init__(
                self,
                time_paths,
                n_onus: int,
                learning_rate: float = 0.2,
            ):
        self.time_paths = np.array(time_paths, dtype='float64')
        self.learning_rate = learning_rate
        self.n_onus = n_onus
        self.pheromones = np.ones((
            n_onus,
            len(time_paths)
        )) / len(time_paths)

    def update(self, demmand):
        self.pheromones *= (1 - self.learning_rate)
        for i in range(self.n_onus):
            delta = np.abs(self.time_paths - demmand[i]) + 0.0001
            self.pheromones[i] += 1/delta * self.learning_rate
    
    def get_time_distribution(self):
        valid_indexes = [i for i in range(len(self.time_paths))]
        results_indexes = np.ndarray(self.n_onus, dtype='int')
        results = np.zeros(self.n_onus)
        
        indexes = [i for i in range(self.n_onus)]
        random.shuffle(indexes)

        #for i in range(self.n_onus):
        for i in indexes:
            ph = self.pheromones[i]
            ph = ph[valid_indexes]
            probs = ph / ph.sum()
            selected_index = np.random.choice(valid_indexes, p=probs)
            valid_indexes.remove(selected_index)

            results_indexes[i] = selected_index
            results[i] = self.time_paths[selected_index]

        return results, results_indexes


class OLT:
    onus: list[ONU]
    time: float
    optimizer: OptimizerACO
    mode: Literal['OPTIMIZED', 'FIXED_DISTRIBUTION']
    verbose: bool = False
    debug: bool = False

    # ------ Metrics --------
    # time_path_freq: Frequency for each time path at a particular oONU
    # mean_pheromones: Mean pheromones for each ONU / timepath
    # mean_demmand: Mean demmand for each ONU
    # blocking_rate: Ponderated blocking rate for each ONU
    # -----------------------

    def init_metrics(self):
        self.time_path_frequency = np.zeros((len(self.onus), len(self.optimizer.time_paths)))
        self.mean_pheromones = np.zeros(self.optimizer.pheromones.shape)
        self.mean_demmand = np.zeros(len(self.onus))

    def update_metrics(self, time_path_indexes, N=100_000):
        #print(time_path_indexes)
        if (self.mode == 'OPTIMIZED'):
            self.mean_pheromones += self.optimizer.pheromones/N

        for i in range(len(self.onus)):
            if (self.mode == 'OPTIMIZED'):
                self.time_path_frequency[i][time_path_indexes[i]] += 1
            self.mean_demmand[i] += self.onus[i].demmand/N

    def get_metrics_names(self):
        return (
            'time_path_freq: Frequency for each time path at a particular ONU',
            'mean_pheromones: Mean pheromones for each ONU / timepath',
            'mean_demmand: Mean demmand for each ONU',
            'blocking_rate: Ponderated blocking rate for each ONU'
        )

    def get_metrics(self):
        blocking_rate = np.zeros(len(self.onus))

        for i in range(len(self.onus)):
            B_rate = self.onus[i].BLOCKED_MESSAGES
            S_rate = self.onus[i].SENT_MESSAGES

            blocking_rate[i] = B_rate / (B_rate + S_rate)

        if (self.mode == 'OPTIMIZED'):
            return (
                self.time_path_frequency,
                self.mean_pheromones,
                self.mean_demmand,
                blocking_rate
            )
        return (
            None,
            None,
            self.mean_demmand,
            blocking_rate
        )
        

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
        self.init_metrics()


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

            if (allowed_onu.current_message == None):
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
                    (window_ends_at < 0.1 * TIMER_MAX and 0.9 * TIMER_MAX < evt_time)
                )

            event_onu_idx, event_time = self.get_next_message_event()
            while continue_flag(event_time):
                while (current_message_ends_at != None and
                        ( current_message_ends_at < event_time or
                          (event_time < 0.1 * TIMER_MAX and 0.9 * TIMER_MAX < current_message_ends_at)
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


    def round(self, round_size, N):
        for _ in range(round_size):
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
            demmand /= N
            self.optimizer.update(demmand=demmand)
            time_dist, time_dist_indexes = self.optimizer.get_time_distribution()
            self.time_distribution = time_dist

            self.update_metrics(
                time_path_indexes=time_dist_indexes,
                N=N//round_size
            )
        else:
            self.update_metrics(
                time_path_indexes=None,
                N=N//round_size
            )



        for onu in self.onus:
            onu.flush_demmand()
            # print('-' * 32)
            # print(f'DEMMAND: {demmand}')
            # print(f'UPDATE TIME DIST: {self.time_distribution}')
            # print('-' * 32)


    def simulate(self, n_iter=1_000_000, round_size=10):
        n_rounds = n_iter // round_size

        self.time = 0.0
        for _ in range(n_rounds):
            self.round(round_size=round_size, N=n_iter)
