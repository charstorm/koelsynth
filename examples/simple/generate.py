#/usr/bin/env python

from collections import deque
import numpy as np

import koelsynth

# Sample rate for the audio
sample_rate = 16000
# Base frequency for all the tones
f0 = 110
# Number of virtual piano keys
num_keys = 32
# Frequencies for each key (equal temperament)
key_frequencies = [f0 * 2 ** (idx/12.0) for idx in range(num_keys)]
# Frame size for processing
frame_size = 160
# Gain to be applied on the signal
gain = 0.2

# FM Modulation parameters
synth_params = koelsynth.FmSynthModParams(
    harmonics=[2, 5, 9],
    amps=[1, 2, 1]
)
# Modulation envelope
mod_env = koelsynth.AdsrParams(
    attack=200,
    decay=200,
    sustain=sample_rate,
    release=100,
    slevel1=0.6,
    slevel2=0.1,
)
# Waveform envelope
wav_env = koelsynth.AdsrParams(
    attack=200,
    decay=200,
    sustain=sample_rate,
    release=100,
    slevel1=0.6,
    slevel2=0.1,
)

# time and keys that need to be played at that time
# time is given in frame count.
events = [
    (0,     [1, 3, 5]),  # 3 keys at once
    (100,   [2]),        # 1 key
    (150,   [3, 8, 14]), # 3 keys
    (200,   [10, 15]),
    (300,   [11, 13]),
    (450,   [3]),
    (600,   [8, 5])
]

# Reverse events (to make it easy to pop from the end)
events = events[::-1]

# Create sequencer
sequencer = koelsynth.Sequencer(frame_size, gain)

# Output file
writer = open("audio.raw", "wb")
frame = np.empty(frame_size, dtype=np.float32)

event = events.pop()
frame_count = 0

# The main processing loop
while events or sequencer.get_generator_count() > 0 or event is not None:
    # Check if we have reached the frame to trigger the event
    if event is not None and event[0] == frame_count:
        # For each key in the event, we add an FmSynth event to the sequencer
        for key_idx in event[1]:
            key_freq = key_frequencies[key_idx]
            phase_per_sample = 2.0 * np.pi * key_freq / sample_rate
            sequencer.add_fmsynth(
                synth_params, mod_env, wav_env, phase_per_sample
            )

        # Prepare the next event
        if events:
            event = events.pop()
        else:
            event = None

    # Get audio from the sequencer
    sequencer.next(frame)
    # Write to the output file
    writer.write(frame.tobytes())
    frame_count += 1
