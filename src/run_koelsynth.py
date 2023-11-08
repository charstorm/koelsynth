import numpy as np
import cppimport
from matplotlib import pyplot as plt

# cppimport will build the code and return a module
koelsynth = cppimport.imp("koelsynth")

params1 = koelsynth.AdsrParams()
params2 = params1.copy()
params2.slevel1 = 0.7
params2.sustain = 40000
print(params1)
print(params2)

synth_params = koelsynth.FmSynthModParams([2, 4, 8], [1, 1, 1])
print(synth_params.harmonics)
print(synth_params.amps)

base_freq = 440.0
samp_rate = 16000.0
ks_base_freq = 2.0 * np.pi * base_freq / samp_rate;

seq = koelsynth.Sequencer()
frame_size = seq.get_frame_size()
buf = np.zeros(frame_size, dtype=np.float32)
seq.add_fmsynth(synth_params, params1, params1, ks_base_freq)
frames = []
while seq.get_generator_count() > 0:
    seq.next(buf)
    frames.append(buf.copy())

combined = np.hstack(frames)
plt.plot(combined)
plt.show()
