TIMER_MAX = 10_000_000
DISPLAY_UNIT = 'ns'
COMPUTE_UNIT = 'μ'

def scale_time_display(mu_measurement: int | float):
    return 1000 * mu_measurement
