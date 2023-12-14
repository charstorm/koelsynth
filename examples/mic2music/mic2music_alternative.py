"""
Alternative version of mic2music that attempts to sound more musical by adding background chords and making use of musical scales.
In addition, a new auto-correlation based method for fundamental frequency detection was implemented. 
"""

import itertools
import numpy as np
import pyaudio

import koelsynth
from functools import lru_cache
from fund_freq_detection import get_fund_freq, FreqSmoother

sample_rate = 16000
frame_size = 320 * 2
gain = 0.2
fft_size = 1024


# Subset of notes that will be used for the melody
SCALE = "blues_minor"  # 'chromatic' (all 12) / 'major' / 'pentatonic' / 'blues_major' / 'blues_minor'

# Play some chords in the background to accompany your musical performance
PLAY_BACKGROUND = True

# Only try to detect the input frequency when this input level is exceeded,
# please adjust to your mic sensitivity:
PITCH_DETECT_LVL_THRESHOLD = -25

# If the input freq doesn't change, don't let the sequencer play the same tone over and over again
# Instead, wait a little bit and then play the next tone (waiting time in frames is defined by PAUSE_INTERVAL).
# This avoids machine-gun like note sequences:
PLAY_ON_CHANGE = True
PAUSE_INTERVAL = 4

# -----------------------------------------

# the 'concert pitch' our music is tuned to
BASE_PITCH = 110

# Can make pitch detection more robust but is still experimental
smoother = FreqSmoother(size=3)  # size=1 means no smoothing


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
        decay=1000,
        sustain=sample_rate,
        release=100,
        slevel1=0.7,
        slevel2=0.1,
    )
    # Waveform envelope
    wav_env = koelsynth.AdsrParams(
        attack=100,
        decay=1000,
        sustain=sample_rate,
        release=100,
        slevel1=0.7,
        slevel2=0.1,
    )
    assert wav_env.get_size() == mod_env.get_size()
    return synth_params, mod_env, wav_env


def get_standard_frequencies(scale="chromatic"):
    octaves = 6
    seq = np.arange(12 * octaves)
    freqs = BASE_PITCH * 2 ** (seq / 12)

    # Specify which subset of the 12 tones is used
    subsets = {
        "chromatic": np.arange(0, 12),
        "major": np.array([0, 2, 4, 5, 7, 9, 11]),
        "pentatonic": np.array([0, 2, 4, 7, 9]),
        "blues_major": np.array([0, 2, 3, 4, 7, 9]),
        "blues_minor": np.array([0, 3, 5, 6, 7, 10]),
    }

    oct_offsets = np.arange(0, octaves * 12, 12)
    oct_offsets = np.repeat(oct_offsets, len(subsets[scale]))
    idx = np.tile(subsets[scale], octaves) + oct_offsets

    return freqs[idx]


prev_trigger = 0


class Background:
    """provide some simple background for your melody"""

    def __init__(self) -> None:
        self.call_counter = 0

        # root frequencies of chord sequence
        f = BASE_PITCH * 1
        self.root_freqs = [
            f,
            f * 2 ** (5 / 12),
            f,
            f * 2 ** (7 / 12),
            f * 2 ** (5 / 12),
            f,
        ]

        self.root_freq = self.root_freqs[0]
        self.num_reps = 8

        self.root_freqs = itertools.cycle(self.root_freqs)

    def play_chord(self, sequencer):
        synth_params, mod_env, wav_env = get_synth_params()

        if self.call_counter % self.num_reps == 0:
            self.root_freq = next(self.root_freqs)

        # These correspond to the notes of the chord (major chord)
        freq_factors = [0.5, 1, 2 ** (4 / 12), 2 ** (7 / 12), 2]

        # Every second time, only play the chord's root (and its sub-octave)
        if self.call_counter % 2 == 0:
            freq_factors = freq_factors[:2]

        for freq_factor in freq_factors:
            phase_per_sample = (
                2.0 * np.pi * (self.root_freq * freq_factor / sample_rate)
            )
            sequencer.add_fmsynth(synth_params, mod_env, wav_env, phase_per_sample)

        self.call_counter += 1


background = Background()


def calculate_tone_freq(mic_frame, standard_freqs):
    """Analyse input from mic, detect the fundamental frequency and calculate output freq"""

    search_freq_range = [110, 450]

    peak_freq, peak_val = get_fund_freq(
        mic_frame,
        search_freq_range,
        sample_rate,
        fft_size,
        PITCH_DETECT_LVL_THRESHOLD,
    )

    if peak_val < 0.4:
        return 0

    peak_freq = smoother.append_value(peak_freq).smooth()
    print(f"freq = {peak_freq:.1f}; ampl = {peak_val:.2f}")
    diff = abs(standard_freqs - peak_freq)
    freq = standard_freqs[diff.argmin()]

    return freq


class AudioEventManager:
    def __init__(self):
        self.prev_freq = 0
        self.rep_sequence_len = 0
        self.frame_counter = 0

    def _play_background(self, sequencer):
        if self.frame_counter % 12 == 0:
            background.play_chord(sequencer)

    def _create_output_melody_tone(self, freq, sequencer):
        global prev_trigger

        # Don't play a new tone right away if the input freq didn't change compared to the last frame.
        # Instead, wait for a few frames (defined by rep_sequence_len).
        # This avoids rapid successions of the same note
        if np.isclose(freq, self.prev_freq) and PLAY_ON_CHANGE:
            self.rep_sequence_len += 1
            if self.rep_sequence_len < PAUSE_INTERVAL:
                return
            self.rep_sequence_len = 0

        phase_per_sample = 2.0 * np.pi * (freq / sample_rate)
        prev_trigger = phase_per_sample
        synth_params, mod_env, wav_env = get_synth_params()
        sequencer.add_fmsynth(synth_params, mod_env, wav_env, phase_per_sample)

    def process(
        self, mic_data, standard_freqs, melody_sequencer, background_sequencer=None
    ):
        self.frame_counter += 1

        if background_sequencer is None:
            background_sequencer = melody_sequencer

        mic_frame = np.frombuffer(mic_data, dtype=np.float32)

        if PLAY_BACKGROUND:
            self._play_background(melody_sequencer)

        freq = calculate_tone_freq(mic_frame, standard_freqs)
        if freq == 0:
            print("No fundamental frequency detected")
            return
        freq *= 2

        self._create_output_melody_tone(freq, background_sequencer)

        self.prev_freq = freq


def add_extra_event(sequencer):
    global prev_trigger
    if prev_trigger > 0:
        synth_params, mod_env, wav_env = get_synth_params()
        sequencer.add_fmsynth(synth_params, mod_env, wav_env, prev_trigger * 2)
        prev_trigger = 0


def main():
    audio_event_manager = AudioEventManager()

    standard_freqs = get_standard_frequencies(SCALE)
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
    flag = 0
    while True:
        mic_data = stream.read(frame_size)
        # add_extra_event(sequencer)

        if flag % 6 == 0:
            audio_event_manager.process(mic_data, standard_freqs, sequencer)

        sequencer.next(frame)

        frame *= 0.5
        stream.write(frame.tobytes())

    # TODO: remove the infinite loop above and handle close
    stream.close()


if __name__ == "__main__":
    main()
