#ifndef KOELSYNTH_SEQUENCER_H
#define KOELSYNTH_SEQUENCER_H

#include <vector>
#include <stdexcept>

#include "frame_generator.h"

void accumulate(
    std::vector<float> &acc,
    std::vector<float> &frame
) {
    if (acc.size() < frame.size()) {
        throw std::invalid_argument("frame size cannot exceed acc size");
    }

    for (size_t idx = 0; idx < frame.size(); idx++) {
        acc[idx] += frame[idx];
    }
}

void scale_vector(std::vector<float> &vec, float scale) {
    for (auto &x: vec) {
        x *= scale;
    }
}

class Sequencer {
    // Sequence of active generators
    std::vector<FrameGenerator*> generators;
    // Frame size of processing
    size_t frame_size = DEFAULT_FRAME_SIZE;
    // Apply gain for every sample
    float gain = 1.0f;

    // Remove all the generators that has ended (also delete them).
    // Update the current generators with active ones.
    void remove_ended() {
        std::vector<FrameGenerator*> result;
        for (auto gen: generators) {
            if (gen->has_ended()) {
                delete gen;
            } else {
                result.push_back(gen);
            }
        }
        generators = result;
    }

public:
    Sequencer(size_t frame_size_ = DEFAULT_FRAME_SIZE,
              float gain_ = 1.0f) {
        frame_size = frame_size_;
        gain = gain_;
    }

    void add(FrameGenerator *gen) {
        gen->set_frame_size(frame_size);
        generators.push_back(gen);
    }

    size_t get_frame_size() {
        return frame_size;
    }

    size_t get_generator_count() {
        return generators.size();
    }

    std::vector<float> next_frame() {
        std::vector<float> output(frame_size, 0);
        std::vector<float> frame;
        bool clean_generators = false;
        for (auto gen: generators) {
            if (gen->has_ended()) {
                clean_generators = true;
                continue;
            }
            gen->next_frame(frame);
            accumulate(output, frame);
        }
        if (clean_generators) {
            remove_ended();
        }
        if (gain != 1.0f) {
            // Apply amplitude adjustment (if needed)
            for (auto &el: output) {
                el *= gain;
            }
        }
        return output;
    }

    ~Sequencer() {
        for (auto gen: generators) {
            delete gen;
        }
    }
};

#endif
