"""
This is a simple keyboard based synthesizer. It uses the getch library to get
the keypresses, koelsynth to generate the audio, and pyaudio to play the
generated audio.
"""

import sys
import threading
import time
import tty
import termios

import numpy as np
import pyaudio

import koelsynth

# Configuration related to audio
sample_rate = 16000
frame_size = 160
gain = 0.2  # volume gain

# Mapping for keys (see build_key_str_map)
key_str_to_int: dict[str, int] = {}

# Mapping of keyboard keys to piano keys
key_remap: dict[str, str] = {}


def getch():
    """
    Hacky black magic implementation of getch.
    Caution!! Ctrl+c or Ctrl+z wont work!!
    """
    fd = sys.stdin.fileno()
    old_settings = termios.tcgetattr(fd)
    try:
        tty.setraw(sys.stdin.fileno())
        ch = sys.stdin.read(1)
    finally:
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
    return ch


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
    kb_keys = "q w e r t y u i o p".split()
    # pentatonic scale (b and f are omitted)
    piano_keys = "1c 1d 1e 1g 1a 2c 2d 2e 2g 2a".split()
    for kb_key, piano_key in zip(kb_keys, piano_keys):
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


def handle_key_press(
    sequencer: koelsynth.Sequencer,
    lock: threading.Lock,
) -> None:
    # FM Modulation parameters
    synth_params = koelsynth.FmSynthModParams([2, 4, 8], [1, 1, 1])
    # Modulation envelope
    mod_env = koelsynth.AdsrParams(
        attack=200,
        decay=200,
        sustain=sample_rate,
        release=100,
        slevel1=0.7,
        slevel2=0.1,
    )
    # Waveform envelope
    wav_env = koelsynth.AdsrParams(
        attack=200,
        decay=200,
        sustain=sample_rate,
        release=100,
        slevel1=0.5,
        slevel2=0.1,
    )
    assert wav_env.get_size() == mod_env.get_size()
    # Setup curses interface (blank)
    time.sleep(2)
    print("\n" + "--" * 40)
    print("Once started, use ` or ? to quit. Ctrl+C wont work!!")
    input("Press enter to start:")
    print(flush=True)
    while True:
        ch = getch()
        if ch == "`" or ch == "?":
            break
        if ch not in key_remap:
            print(f"\nKey {ch} not recognized! Use ` or ? to exit.")
            continue
        piano_key = key_remap[ch.lower()]
        phase_per_sample = get_phase_per_sample(piano_key)
        with lock:
            sequencer.add_fmsynth(synth_params, mod_env, wav_env, phase_per_sample)


def main():
    build_key_str_map()
    build_key_remap()
    print(key_str_to_int)
    print(key_remap)
    lock = threading.Lock()
    sequencer = koelsynth.Sequencer(frame_size, gain)
    # Start the audio handling thread
    thread = threading.Thread(target=handle_sequencer_audio, args=(sequencer, lock))
    thread.daemon = True
    thread.start()
    # Manage keypress
    handle_key_press(sequencer, lock)


if __name__ == "__main__":
    main()
