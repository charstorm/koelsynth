"""
A simple keyboard based piano app.

It works as follows:
    1. Use getch provided by py-getch library to get keyboard input
    2. Use koelsynth to produce FM synth audio
    3. Use pyaudio to play the produced audio

The keyboard input is handled in the main thread. Audio processing is handled
in a separate thread.

Note: PyAudio may print some logs during the startup. This can be ignored.

See get_synth_params() to adjust the audio.
"""

import threading
import time

import numpy as np
import pyaudio
from getch import getch

import koelsynth

# Configuration related to audio
sample_rate = 16000
frame_size = 160
gain = 0.2  # volume gain

# Mapping for keys (see build_key_str_map)
key_str_to_int: dict[str, int] = {}

# Mapping of keyboard keys to piano keys
key_remap: dict[str, str] = {}

# Supported keys (from your keyboard)
input_keys = "q w e r t y u i o p"
# Mapped piano keys for the above chars
piano_keys = "1c 1d 1e 1g 1a 2c 2d 2e 2g 2a"


def build_key_str_map() -> None:
    """
    Mapping keys to index for 1 octave
    """
    keys = "c c# d d# e f f# g g# a a# b".split()
    for idx, key in enumerate(keys):
        key_str_to_int[key] = idx
    assert len(key_str_to_int) == 12


def build_key_remap() -> None:
    """
    Mapping keyboard keys to piano keys
    """
    source_keys = input_keys.split()
    target_keys = piano_keys.split()
    assert len(source_keys) == len(target_keys)
    for kb_key, piano_key in zip(source_keys, target_keys):
        key_remap[kb_key] = piano_key


def parse_key(key: str) -> int:
    """
    Parse a key of the form 2c# to it's index in a keyboard
    """
    octave = int(key[0])
    key = key[1:]
    return 12 * octave + key_str_to_int[key]


def get_phase_per_sample(key: str) -> float:
    """
    Converts a key of the form 2c# to its frequency and then phase per sample.

    Koelsynth does not use frequencies directly. Instead, it uses phase per
    sample for generating sound. The calculation needed is provided
    here.
    """
    key_index = parse_key(key)
    # 12 key equal temperament scale
    key_hz = 110 * 2 ** (key_index / 12.0)
    # phase/sample = 2pi * f/fs
    phase_per_sample = 2.0 * np.pi * (key_hz / sample_rate)
    return phase_per_sample


def handle_sequencer_audio(
    sequencer: koelsynth.Sequencer,
    lock: threading.Lock,
) -> None:
    """
    Manage audio stream coming from sequencer.
    """
    frame = np.zeros(frame_size, dtype=np.float32)
    pa = pyaudio.PyAudio()
    stream = pa.open(
        format=pyaudio.paFloat32,
        channels=1,
        rate=sample_rate,
        output=True,
        frames_per_buffer=frame_size,
    )

    while True:
        with lock:
            sequencer.next(frame)
        stream.write(frame.tobytes())

    # TODO: remove the infinite loop above and handle close
    stream.close()


def get_synth_params() -> (
    tuple[koelsynth.FmSynthModParams, koelsynth.AdsrParams, koelsynth.AdsrParams]
):
    """
    Return FM synthesis parameters.

    This is the function to play around with the sound texture.
    """
    # FM Modulation parameters
    synth_params = koelsynth.FmSynthModParams([2, 5, 9, 13], [1, 2, 1, 1])
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
    assert wav_env.get_size() == mod_env.get_size()
    return synth_params, mod_env, wav_env


def handle_key_press(
    sequencer: koelsynth.Sequencer,
    lock: threading.Lock,
) -> None:
    """
    Setup synthesis parameters and handle key-press.
    """
    synth_params, mod_env, wav_env = get_synth_params()
    # Wait for pyaudio prints. This is a dirty way to manage this.
    # TODO: move to better synchronization!
    time.sleep(3)
    print("\n" + "--" * 40)
    print("Once started, use ` or ? to quit. Ctrl+C may not work!!")
    print("Supported input keys:", input_keys)
    input("Press enter to start:")
    print(flush=True)
    while True:
        # Get input from keyboard
        ch_in = getch()
        ch = ""
        if isinstance(ch_in, bytes):
            # In windows, it returns bytes (not string)
            ch = ch_in.decode()
        else:
            ch = ch_in
        # Ctrl+C does not seem to work. We need a way to quit nicely.
        if ch == "`" or ch == "?":
            break
        if ch not in key_remap:
            print(f"\nKey {ch} not recognized! Use ` or ? to exit.")
            continue
        # Remap input key to corresponding piano key
        piano_key = key_remap[ch.lower()]
        # This handles the frequency of the tone that will be played
        phase_per_sample = get_phase_per_sample(piano_key)
        with lock:
            # Add a new FM synth event
            sequencer.add_fmsynth(synth_params, mod_env, wav_env, phase_per_sample)


def start_audio_processing_thread(
    sequencer: koelsynth.Sequencer, lock: threading.Lock
) -> None:
    """
    Setup the thread to handle sequencer processing and audio output
    """
    thread = threading.Thread(target=handle_sequencer_audio, args=(sequencer, lock))
    thread.daemon = True
    thread.start()


def main():
    """
    The main function of this script.
    """
    build_key_str_map()
    build_key_remap()
    lock = threading.Lock()
    sequencer = koelsynth.Sequencer(frame_size, gain)
    start_audio_processing_thread(sequencer, lock)
    handle_key_press(sequencer, lock)


if __name__ == "__main__":
    main()
