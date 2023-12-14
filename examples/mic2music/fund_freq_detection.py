"""Fundamental frequency detection"""

from collections import deque
import numpy as np


class FreqSmoother:
    """Rolling median filter
    TODO: still needs some work"""

    def __init__(self, size=5, init_value=None) -> None:
        self.buffer = deque(maxlen=size)

        if init_value is None:
            self.buffer.appendleft(0)

    def append_value(self, val):
        self.buffer.appendleft(val)
        return self

    def smooth(self):
        if len(self.buffer) == 0:
            raise ValueError("Buffer is empty. Please append values.")
        if not any(self.buffer):
            return 0
        return np.median([val for val in self.buffer if val != 0])


def calculate_acf(signal, fft_len):
    """Get the autocorrelation function (acf) from the FFT"""

    N = len(signal)

    # zero-padding
    signal_padded = np.zeros(fft_len)
    signal_padded[: len(signal)] = signal

    ft = np.fft.fft(signal)
    acf = np.fft.ifft(ft * ft.conjugate())
    acf = np.real(acf)
    acf = acf[: len(acf) // 2] / N
    return acf / acf.max()


def get_rms_dB(x):
    """Get root-mean-square value in dB"""
    rms = np.sqrt(np.mean(x**2))
    return 20 * np.log10(rms)


def get_fund_freq(signal, freq_range, sample_rate, fft_len, level_threshold=-20):
    # simple VAD
    if get_rms_dB(signal) < level_threshold:
        fund_freq, fund_ampl = 0, 0
        return fund_freq, fund_ampl

    acf = calculate_acf(signal, fft_len)

    # auto corr func is in the time domain:
    # -> convert freq values in Hz to time values in samples
    low_time_cutoff = int(1 / freq_range[1] * sample_rate)
    high_time_cutoff = int(1 / freq_range[0] * sample_rate)

    max_loc = np.argmax(acf[low_time_cutoff:high_time_cutoff])
    fund_ampl = acf[low_time_cutoff + max_loc]

    fund_freq = 1 / (low_time_cutoff + max_loc) * sample_rate

    # TODO: add parabolic interpolation here ...

    return fund_freq, fund_ampl
