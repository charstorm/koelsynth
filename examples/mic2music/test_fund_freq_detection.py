import numpy as np
import time

from fund_freq_detection import get_fund_freq

SAMPLE_RATE = 16000


def gen_tone_complex(freqs, sample_rate):
    """Generate a harmonic tone complex"""

    t = np.arange(0, sample_rate) / sample_rate
    signal = np.zeros(sample_rate)

    for freq in freqs:
        signal += np.sin(2 * np.pi * freq * t)

    return signal


def get_nextpow2(N):
    """
    Find next power of 2
    Taken from https://gist.github.com/lppier/a59adc18bcf32d8545f7
    """
    n = 1
    while n < N:
        n *= 2
    return n


def test_performance():

    N = 10_000

    # simple tone complex
    freqs = 500, 1000, 1500
    signal = gen_tone_complex(freqs, SAMPLE_RATE)

    fft_len = get_nextpow2(len(signal))

    start = time.perf_counter()
    for _ in range(N):
        get_fund_freq(signal, [400, 600], SAMPLE_RATE, fft_len=fft_len)
    stop = time.perf_counter()
    print(f"Time: {stop-start:.4} sec for {N:,} runs.")


def test_correct_result():

    # simple tone complex
    freqs = 500, 1000, 1500, 2000
    signal = gen_tone_complex(freqs, SAMPLE_RATE)

    # additive noise
    np.random.seed(0)
    signal += np.random.randn(len(signal)) * 0.5

    fft_len = get_nextpow2(len(signal))

    f0, fund_ampl = get_fund_freq(signal, [400, 600], SAMPLE_RATE, fft_len=fft_len)

    assert np.isclose(f0, freqs[0])
    #assert np.isclose(fund_ampl, 1.0)

    print(f"F0 = {f0}, ampl = {fund_ampl}")


if __name__ == "__main__":
    test_correct_result()
    test_performance()
