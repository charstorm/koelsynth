"""
CAUTION: UNDER CONSTRUCTION!

This script reads audio from mic, estimates the peak feaquency and plays
synth sounds with matching frequency.
"""

import threading
import numpy as np
import pyaudio

import koelsynth
from functools import lru_cache

sample_rate = 16000
frame_size = 320 * 2
gain = 0.2
fft_size = 1024

@lru_cache()
def get_synth_params():
    """
    Return FM synthesis parameters.

    This is the function to play around with the sound texture.
    """
    # FM Modulation parameters
    synth_params = koelsynth.FmSynthModParams(
        harmonics=[2, 4, 7],
        amps=[3, 1, 1],
    )
    # Modulation envelope
    mod_env = koelsynth.AdsrParams(
        attack=100,
        decay=200,
        sustain=sample_rate,
        release=100,
        slevel1=0.7,
        slevel2=0.1,
    )
    # Waveform envelope
    wav_env = koelsynth.AdsrParams(
        attack=100,
        decay=200,
        sustain=sample_rate,
        release=100,
        slevel1=0.5,
        slevel2=0.1,
    )
    assert wav_env.get_size() == mod_env.get_size()
    return synth_params, mod_env, wav_env


def get_standard_frequencies():
    octaves = 6
    seq = np.arange(12 * octaves)
    freqs = 110 * 2 ** (seq / 12)
    return freqs


def get_spectrum_peak(frame):
    frame_fft = np.fft.rfft(frame, fft_size)
    spectrum = np.abs(frame_fft)
    min_idx = int(110 / sample_rate * fft_size)
    max_idx = int(4000 / sample_rate * fft_size)
    spectrum[:min_idx] = 0
    spectrum[max_idx:] = 0
    peak_loc = spectrum.argmax()
    peak_freq = peak_loc / fft_size * sample_rate
    return peak_freq, spectrum[peak_loc]


prev_trigger = 0


def process_audio_add_event(mic_data, standard_freqs, sequencer):
    global prev_trigger
    mic_frame = np.frombuffer(mic_data, dtype=np.float32)
    peak_freq, peak_val = get_spectrum_peak(mic_frame)
    if peak_freq < 110:
        return
    if peak_val < 2:
        return
    diff = abs(standard_freqs - peak_freq)
    freq = standard_freqs[diff.argmin()]
    freq /= 4
    phase_per_sample = 2.0 * np.pi * (freq / sample_rate)
    prev_trigger = phase_per_sample
    synth_params, mod_env, wav_env = get_synth_params()
    sequencer.add_fmsynth(synth_params, mod_env, wav_env, phase_per_sample)


def add_extra_event(sequencer):
    global prev_trigger
    if prev_trigger > 0:
        synth_params, mod_env, wav_env = get_synth_params()
        sequencer.add_fmsynth(synth_params, mod_env, wav_env, prev_trigger*2)
        prev_trigger = 0


def main():
    standard_freqs = get_standard_frequencies()
    sequencer = koelsynth.Sequencer(frame_size, gain)
    frame = np.zeros(frame_size, dtype=np.float32)
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=sample_rate,
        output=True,
        input=True,
        frames_per_buffer=frame_size,
    )

    print("processing ...")
    while True:
        mic_data = stream.read(frame_size)
        if np.random.randint(0, 2) == 0:
            add_extra_event(sequencer)
        if np.random.randint(0, 2) == 0:
            process_audio_add_event(mic_data, standard_freqs, sequencer)
        sequencer.next(frame)
        stream.write(frame.tobytes())

    # TODO: remove the infinite loop above and handle close
    stream.close()


if __name__ == "__main__":
    main()
