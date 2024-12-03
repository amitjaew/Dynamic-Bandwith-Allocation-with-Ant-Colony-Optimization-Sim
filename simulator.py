import pickle
import os
from time import time
import numpy as np

from ONU import ONU
from OLT import OLT, OptimizerACO

import pickle
import os

def save_results(data, directory):
    """
    Save numerized results to a sequentially numbered pickle file.

    :param data: The data to save (e.g., a list, dictionary, etc.).
    :param directory: The directory to save the pickle files.
    """

    if not os.path.exists(directory):
        os.makedirs(directory)
    
    existing_files = [f for f in os.listdir(directory) if f.endswith('.pkl')]
    existing_numbers = [
        int(f.split('.')[0]) for f in existing_files if f.split('.')[0].isdigit()
    ]
    next_number = max(existing_numbers, default=0) + 1
    
    file_name = f"{next_number:02d}.pkl"
    file_path = os.path.join(directory, file_name)
    
    try:
        with open(file_path, 'wb') as file:
            pickle.dump(data, file)
        print(f"Data successfully saved to {file_path}.")
    except Exception as e:
        print(f"An error occurred while saving to {file_path}: {e}")


if __name__ == '__main__':
    onus = [
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=120e-3, # ~ 600 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=120e-3, # ~ 600 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=120e-3, # ~ 600 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=120e-3, # ~ 600 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=40e-3, # ~ 200 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=40e-3, # ~ 200 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=40e-3, # ~ 200 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
        ONU(
            mean_arrival_period=30, #  every 30 microseconds
            mean_message_length=40e-3, # ~ 200 bits at 0.8 bits per ns
            MESSAGE_QUEUE_LENGTH=512  # Standard queue for Cisco Router
        ),
    ]
    time_paths = np.arange(1e-3, 2_000e-3, 200e-3)
    base_time_dist = [ time_paths[i] for i in range(len(onus)) ]
    optimizer = OptimizerACO(
        time_paths=time_paths,
        n_onus=len(onus)
    )
    olt = OLT(
        onus=onus,
        time_distribution=base_time_dist,
        optimizer=optimizer,
        mode='OPTIMIZED',
        verbose=False,
        debug=False
    )
    t_start = time()
    olt.simulate(
        n_iter=100_000,
        round_size=10
    )
    for onu in olt.onus:
        print(f'queue len: {len(onu.message_queue)}')
        p_blocked = onu.BLOCKED_MESSAGES / (onu.SENT_MESSAGES + onu.BLOCKED_MESSAGES)
        print(f'blocked probs: {p_blocked}')
    t_end = time()

    print(f'elapsed {t_end - t_start} seconds')

    print('METRICS')
    metrics_names = olt.get_metrics_names()
    metrics = olt.get_metrics()

    for i in range(len(metrics)):
        print(metrics_names[i])
        print(metrics[i])

    save_results(metrics, './results')
