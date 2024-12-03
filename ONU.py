from numpy import random
from typing import Literal
from collections import deque
from constants import TIMER_MAX


class ONU:
    mean_arrival_period: float
    mean_message_length: float

    mean_mssg_time: float
    mean_idle_time: float

    next_message_event = 0.0
    next_message_length: float

    message_queue: deque[float] = deque([])
    waiting_since: float = 0.0
    WAITED: float = 0.0

    MESSAGE_QUEUE_LENGTH: int = 10
    BLOCKED_MESSAGES: int = 0
    BLOCKED_MESSAGES_BY_ROUND: int = 0
    SENT_MESSAGES: int = 0
    SENT_MESSAGES_BY_ROUND: int = 0
    current_message: float | None = None
    current_message_progress: float | None = None

    demmand = 0.0

    def __init__(
                self,
                mean_arrival_period: float = 200e-3, # 120 ns o 0.12 [microsegundos]
                mean_message_length: float = 40e-3, # ~ 200 bits a 0.8 bits por ns [en microsegundos]
                MESSAGE_QUEUE_LENGTH:int = 2048  # Limite estandar para router Cisco
            ):
        self.mean_arrival_period = mean_arrival_period
        self.mean_message_length = mean_message_length
        self.MESSAGE_QUEUE_LENGTH = MESSAGE_QUEUE_LENGTH
        self.next_message_event = 0.0
        self.schedule_events()


    def schedule_events(self):
        self.next_message_length = random.exponential(
            scale=self.mean_message_length
        )
        self.next_message_event = (
            self.next_message_event + 
            random.exponential(scale=self.mean_arrival_period)
        ) % TIMER_MAX


    def enqueue_message(self):
        self.demmand += self.next_message_length
        if (len(self.message_queue) >= self.MESSAGE_QUEUE_LENGTH):
            self.BLOCKED_MESSAGES_BY_ROUND += 1
            self.BLOCKED_MESSAGES += 1
            # print('! ******* BLOCKED ******* !')
        else:
            self.message_queue.append(self.next_message_length)
        
        self.schedule_events()


    def dequeue_message(self):
        if (len(self.message_queue) == 0):
            return None
        self.SENT_MESSAGES += 1
        self.SENT_MESSAGES_BY_ROUND += 1
        self.current_message = self.message_queue.popleft()
        self.current_message_progress = 0.0
        return self.current_message

    
    def get_next_message_event(self):
        return self.next_message_event


    def flush_demmand(self):
        self.demmand = 0.0
        self.BLOCKED_MESSAGES_BY_ROUND = 0
        self.SENT_MESSAGES_BY_ROUND = 0
