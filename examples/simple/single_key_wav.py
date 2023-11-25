"""
Script to dump the audio for a set of frequencies to their own wav files.

You can use ffmpeg to convert audio from wav to a target format.
See convert_audio.sh for more details.
"""

import wave
import numpy as np

import koelsynth

# Global configuration
sample_rate = 48000
frame_size = 480

# FM Modulation parameters.
# This is the most important parameter to adjust
synth_params = koelsynth.FmSynthModParams(harmonics=[2, 5, 9], amps=[1, 2, 1])

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

# Total size of both envelopes have to match.
assert wav_env.get_size() == mod_env.get_size()

# s16 max limit
s16_max_limit = 2**15 - 1

# Sequencer handles generation of audio
sequencer = koelsynth.Sequencer(frame_size, gain=0.2)


def convert_f32_to_s16(arr_f32: np.ndarray) -> np.ndarray:
    """
    Convert f32 array of audio samples to s16.

    Koelsynth generates audio in f32. We want to write that in s16.
    """
    return (arr_f32 * s16_max_limit).astype(np.int16)


def generate_key_wav(freq: float, output_file: str, gain: float = 0.2) -> None:
    """
    Generates a key sound of the given `freq` and writes audio to
    `output_file` in wave format.
    """
    phase_per_sample = 2.0 * np.pi * freq / sample_rate
    sequencer.add_fmsynth(synth_params, mod_env, wav_env, phase_per_sample, gain)

    frame_f32 = np.empty(frame_size, dtype=np.float32)

    # Open the wav file
    wf = wave.open(output_file, "w")
    wf.setnchannels(1)
    wf.setsampwidth(2)
    wf.setframerate(sample_rate)

    while sequencer.get_generator_count() > 0:
        # Get audio from sequencer
        sequencer.next(frame_f32)
        # Convert to s16
        frame_s16 = convert_f32_to_s16(frame_f32)
        # Write to audio file
        wf.writeframes(frame_s16.tobytes())

    wf.close()
    print(f"{output_file} is written")


def main():
    f0 = 440
    gain = 1.0
    num_keys = 12
    for idx in range(num_keys):
        # Equal temperament
        freq = f0 * 2 ** (idx / 12)
        audio_file = f"audio_{freq:.2f}hz.wav"
        generate_key_wav(freq, audio_file, gain)


if __name__ == "__main__":
    main()
