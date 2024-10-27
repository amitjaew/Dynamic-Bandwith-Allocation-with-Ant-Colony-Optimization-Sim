from numpy import random
from typing import Literal


TIMER_MAX = 1_000_000


class Message:
    amount: float = 0.0
    progress: float = 0.0

    def __init__(self, amount):
        self.amount = amount


class ONU:
    state: Literal['IDLE', 'WAITING', 'SENDING']
    mean_mssg_time: float
    mean_idle_time: float
    message_queue: list[float]
    next_event: Literal['MESSAGE', 'IDLE'] = 'MESSAGE'
    next_event_mssg: float
    next_event_idle: float
    next_message_length: float

    waiting_since: float = 0.0
    WAITED: float = 0.0

    MESSAGE_QUEUE_LENGTH: int = 10
    BLOCKED_MESSAGES: int = 0
    SENT_MESSAGES: int = 0
    current_message: Message | None = None

    def __init__(
                self,
                mean_mssg_time,
                mean_idle_time,
                MESSAGE_QUEUE_LENGTH
            ):
        self.mean_mssg_time = mean_mssg_time
        self.mean_idle_time = mean_idle_time
        self.MESSAGE_QUEUE_LENGTH = MESSAGE_QUEUE_LENGTH
        self.next_event_idle = 0.0
        self.next_event_mssg = 0.0
        self.state = 'IDLE'


    def schedule_events(self):
        event_mssg_gen = random.exponential(
            scale=self.mean_idle_time
        )
        self.next_message_length = random.exponential(
            scale=self.mean_mssg_time
        )
        self.next_event_mssg = self.next_event_idle + event_mssg_gen % TIMER_MAX
        self.next_event_idle = self.next_event_mssg + self.next_message_length % TIMER_MAX


    def queue_message(self):
        if (len(self.message_queue) >= self.MESSAGE_QUEUE_LENGTH):
            self.BLOCKED_MESSAGES += 1
        else:
            self.message_queue.append(self.next_message_length)


    def get_next_event(self):
        time: float
        if (self.next_event == 'IDLE'):
            time = self.next_event_idle
        else:
            time = self.next_event_mssg
        return (
            self.next_event,
            time
        )


    def start_message_intent(self, time=0.0):
        self.current_message = Message(self.next_message_length)
        self.state = 'WAITING'
        self.waiting_since = time


    def start_message_send(self, time=0.0):
        self.state = 'SENDING'

        if (time < self.waiting_since):
            self.WAITED += time + (TIMER_MAX - self.waiting_since)
        else:
            self.WAITED += time - self.waiting_since


    def pause_message_send(self, time=0.0, progress=0.0):
        if (not self.current_message):
            return

        self.state = 'WAITING'
        self.current_message.progress += progress
        self.waiting_since = time


    def end_message_send(self):
        self.SENT_MESSAGES += 1
        self.current_message = None
        self.state = 'IDLE'
