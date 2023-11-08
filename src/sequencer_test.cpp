
#include <iostream>
#include <fstream>
#include <cstdlib>

#include "sequencer.h"
#include "signal_generators.h"

const float fs = 16000.0f;

using namespace signal;

AdsrParams env_params_base = {
    .attack = 800,
    .decay = 400,
    .sustain = 16000,
    .release = 1600
};

FmSynthModParams mod_params_base {
    .harmonics = {2, 6, 12},
    .amps = {1, 3, 1}
};

void add_event(Sequencer &seq, size_t frame_size, float key) {
    float key_hz = key2hz(key);
    float base_freq = compute_phase_per_sample(key_hz, fs);
    int duration = 1 + rand() % 4;
    AdsrParams env_params = env_params_base;
    env_params.sustain *= duration;
    env_params.slevel2 = 0.05;

    auto gen = new FmSynthGenerator(
        mod_params_base, env_params, env_params, base_freq
    );
    gen->set_frame_size(frame_size);
    seq.add(gen);
}

void generate_tones() {
    std::ofstream output("audio.raw", std::ios::binary);
    Sequencer seq;
    size_t frame_count = 10000;
    size_t frame_size = 256;
    seq.set_frame_size(frame_size);

    for (size_t ii = 0; ii < frame_count; ii++) {
        if (rand() % 101 == 1) {
            float key = 12 + rand() % 12;
            add_event(seq, frame_size, key);
        }
        
        if (rand() % 81 == 1) {
            float key = 24 + rand() % 12;
            add_event(seq, frame_size, key);
        }
        
        if (rand() % 61 == 1) {
            float key = 36 + rand() % 12;
            add_event(seq, frame_size, key);
        }

        std::vector frame = seq.next_frame();
        scale_vector(frame, 0.2f);
        output.write((char*) frame.data(), 4 * frame.size());
    }
}

int main() {
    srand(time(nullptr));
    generate_tones();
    return 0;
}

