#ifndef KOELSYNTH_SIGNAL_GENERATORS_H
#define KOELSYNTH_SIGNAL_GENERATORS_H

#include <cmath>
#include <cassert>
#include <stdexcept>
#include <string>

#include "frame_generator.h"

#ifndef M_PI
    #define M_PI 3.14159265358979323846
#endif

template<typename T>
float cf32(T val) {
    return static_cast<float>(val);
}

namespace signal {

// A class to handle a constant signal
class ConstantGenerator: public FrameGenerator {
    // Value of the constant
    float value = 0;
    // Frame size
    size_t frame_size = DEFAULT_FRAME_SIZE;
    // Size of the stream in samples (not the number of frames)
    size_t size = 0;
    // Remaining number of samples size_t remaining = 0;
    size_t remaining = 0;

    friend class Signal_Tester;

public:
    // value_ : value of the constant
    // size_  : total number of samples
    ConstantGenerator(float value_, size_t size_):
        value(value_),
        size(size_),
        remaining(size_) {
        // nothing to do here
    }

    virtual void set_frame_size(size_t num_samples) {
        frame_size = num_samples;
    }

    virtual bool has_ended() {
        return remaining == 0;
    }

    virtual bool next_frame(std::vector<float> &frame) {
        size_t result_size = frame_size;
        if (remaining < result_size) {
            result_size = remaining;
        }

        frame.resize(result_size);
        for (size_t ii = 0; ii < result_size; ii++) {
            frame[ii] = value;
        }
        remaining -= result_size;

        return remaining == 0;
    }

    virtual size_t get_size() {
        return size;
    }
};


// A class to generate a linear ramp signal
class RampGenerator: public FrameGenerator {
    // starting value of the ramp
    float start = 0;
    // ending value of the ramp
    float end = 0;
    // Number of samples to generate
    size_t size = 0;
    // Number of samples already produced
    size_t progress = 0;
    // Number of samples per frame
    size_t frame_size = DEFAULT_FRAME_SIZE;

    friend class Signal_Tester;

public:
    RampGenerator(float start_, float end_, size_t size_):
        start(start_),
        end(end_),
        size(size_) {
    }

    virtual void set_frame_size(size_t num_samples) {
        frame_size = num_samples;
    }

    virtual bool has_ended() {
        return progress >= size;
    }

    virtual bool next_frame(std::vector<float> &frame) {
        size_t remaining = size - progress;
        size_t result_size = frame_size;
        if (remaining < result_size) {
            result_size = remaining;
        }

        float span = (size - 1);

        frame.resize(result_size);
        for (size_t ii = 0; ii < result_size; ii++) {
            float pos = progress + ii;
            float alpha = (span - pos) / span;
            float beta = pos / span;
            frame[ii] = alpha * start + beta * end;
        }

        progress += frame.size();
        return progress >= size;
    }

    virtual size_t get_size() {
        return size;
    }
};


float halfing_size_to_decay(float halfing_size) {
    return powf(0.5f, 1.0f / halfing_size);
}


// A class to generate an exponentially decaying signal
class ExponentialGenerator: public FrameGenerator {
    // Starting value
    float start = 0;
    // Decay for every step
    float decay = 0;
    // Size of the stream
    size_t size = 0;
    // Current value of the signal
    float current = 0;
    // Number of samples produced so far
    size_t progress = 0;
    // Frame size in samples
    size_t frame_size = DEFAULT_FRAME_SIZE;

    friend class Signal_Tester;

public:

    // start_ : starting value of the signal
    // halfing_size : number of samples to for a decay of 1/2
    ExponentialGenerator(float start_, float halfing_size, size_t size_):
        start(start_),
        size(size_),
        current(start_) {
        decay = halfing_size_to_decay(halfing_size);
    }

    virtual void set_frame_size(size_t num_samples) {
        frame_size = num_samples;
    }

    virtual bool has_ended() {
        return progress >= size;
    }

    virtual size_t get_size() {
        return size;
    }

    virtual bool next_frame(std::vector<float> &frame) {
        size_t remaining = size - progress;
        size_t result_size = frame_size;
        if (remaining < result_size) {
            result_size = remaining;
        }

        frame.resize(result_size);
        for (size_t ii = 0; ii < result_size; ii++) {
            frame[ii] = current;
            current = current * decay;
        }

        progress += frame.size();
        return progress >= size;
    }

};


struct AdsrParams {
    size_t attack = 0;
    size_t decay = 0;
    size_t sustain = 0;
    size_t release = 0;
    // Starting level for sustain
    float slevel1 = 0.5;
    // Ending level for sustain
    float slevel2 = 0.1;

    size_t get_size() {
        return attack + decay + sustain + release;
    }

    std::string to_string() {
        std::string r;
        r += "AdsrParams(attack=";
        r += std::to_string(attack);
        r += ", decay=";
        r += std::to_string(decay);
        r += ", sustain=";
        r += std::to_string(sustain);
        r += ", release=";
        r += std::to_string(release);
        r += ", slevel1=";
        r += std::to_string(slevel1);
        r += ", slevel2=";
        r += std::to_string(slevel2);
        r += ")";
        return r;
    }
};


class AdsrEnvelope: public FrameGenerator {
    // Parameters for ADSR
    AdsrParams params;
    // Progress so far
    size_t progress = 0;
    // Starting point for decay
    size_t decay_start = 0;
    // Starting point for sustain
    size_t sustain_start = 0;
    // Starting for for release
    size_t release_start = 0;
    // Log of sustain_start
    float log_slevel1 = 0.0f;
    // Log of sustain_end
    float log_slevel2 = 0.0f;
    // Size of the frame
    size_t frame_size = DEFAULT_FRAME_SIZE;
    // Total size of the signal
    size_t size = 0;

    friend class Signal_Tester;

public:

    AdsrEnvelope() = default;

    AdsrEnvelope(AdsrParams params_){
        params = params_;

        decay_start = params.attack;
        sustain_start = decay_start + params.decay;
        release_start = sustain_start + params.sustain;

        log_slevel1 = logf(params.slevel1);
        log_slevel2 = logf(params.slevel2);
        size = params.attack + params.decay + params.sustain + params.release;
    }

    virtual void set_frame_size(size_t num_samples) {
        frame_size = num_samples;
    }

    virtual bool has_ended() {
        return progress >= size;
    }

    virtual size_t get_size() {
        return size;
    }

    float get_next_sample() {
        size_t index = progress;

        float result = 0;
        if (index < decay_start) {
            // Attack phase
            result = cf32(index) / cf32(params.attack);
        } else if (index < sustain_start) {
            // Decay phase
            float position = index - decay_start;
            float max_change = 1 - params.slevel1;
            float deviation = position / cf32(params.decay) * max_change;
            result = 1.0f - deviation;
        } else if (index < release_start) {
            // Sustain phase
            // x = position
            float x = index - sustain_start;
            // Last index of sustain
            float M = params.sustain - 1;
            // Compute the value in log (linear)
            float y = (x * log_slevel2 + (M - x) * log_slevel1) / M;
            // convert the value back
            result = expf(y);
        } else {
            // Release phase
            float position = index - release_start;
            float max_change = params.slevel2;
            float deviation = position / cf32(params.release) * max_change;
            result = params.slevel2 - deviation;
        }

        progress++;
        return result;
    }


    virtual bool next_frame(std::vector<float> &frame) {
        size_t remaining = size - progress;
        size_t result_size = frame_size;
        if (remaining < result_size) {
            result_size = remaining;
        }

        frame.resize(result_size);
        for (size_t ii = 0; ii < result_size; ii++) {
            frame[ii] = get_next_sample();
        }
        return progress >= size;
    }
};


// Frequency modulation depends on 3 things.
// 1. A set of harmonics (like multiples of the base frequency) which are used
//    in modulation. Unlike frequency modulation in communications, in music
//    synthesis, the modulation frequencies are higher than the base frequency.
//    Parameters for these are handled by FmSynthModParams below.
// 2. Envelope applied on the modulating signal.
// 3. Envelope applied on the final signal.

// Parameters for the modulation signal
struct FmSynthModParams {
    // Harmonics for frequency modulation.
    // Eg: [2, 7, 11]
    std::vector<float> harmonics;
    // Amplitudes for harmonics.
    // Should be of the same length as harmonics above.
    std::vector<float> amps;

    FmSynthModParams() = default;

    FmSynthModParams(
        std::vector<float> harmonics_, std::vector<float> amps_
    ) {
        if (harmonics_.size() != amps_.size()) {
            throw std::invalid_argument("mismatch in sizes of harmonics and amps");
        }
        harmonics = harmonics_;
        amps = amps_;
    }
};


float compute_phase_per_sample(float f, float fs) {
    return (2 * M_PI) * (f / fs);
}


float key2hz(float key) {
    return 110.0f * powf(2.0f, (key / 12.0f));
}


float key_to_phase_per_sample(float key, float fs) {
    float freq = key2hz(key);
    return compute_phase_per_sample(freq, fs);
}


class FmSynthGenerator: public FrameGenerator {
    // Parameters for modulation signal parameters
    FmSynthModParams mod_params;

    // mod envelope generator
    AdsrEnvelope mod_env_gen;
    // final envelope generator
    AdsrEnvelope env_gen;

    // Size of the generated signal
    size_t size = 0;
    // Progress do far
    size_t progress = 0;
    // Frame size for processing
    size_t frame_size = DEFAULT_FRAME_SIZE;

    // All frequencies below are per sample angle change.

    // Per sample angle change for base signal
    float phase_rate = 0;
    // Per sample angle change for modulation components
    std::vector<float> mod_freq_vec;

    // Current phase value for the base signal
    float base_phase = 0;
    // Phase values for modulation components
    std::vector<float> mod_phase_vec;

    // gain for this event
    float gain = 1.0f;

public:

    // phase_per_sample -> per sample phase change for base frequency.
    //      phase_per_sample = (f / fsamp) * 2pi
    // gain_ -> gain to be applied on the waveform for this event 
    FmSynthGenerator(
        FmSynthModParams mod_params_,
        AdsrParams mod_env_params_,
        AdsrParams env_params_,
        float phase_per_sample,
        float gain_
    ) {
        if (mod_env_params_.get_size() != env_params_.get_size()) {
            throw std::invalid_argument("envelope sizes do not match");
        }

        if (mod_params_.harmonics.size() != mod_params_.amps.size()) {
            throw std::invalid_argument("mismatch in sizes of harmonics and amps");
        }

        mod_params = mod_params_;
        mod_env_gen = AdsrEnvelope(mod_env_params_);
        env_gen = AdsrEnvelope(env_params_);
        phase_rate = phase_per_sample;
        base_phase = 0;
        size = env_params_.get_size();
        gain = gain_;

        // Actual per-sample phase change for every component.
        for (auto mul: mod_params.harmonics) {
            mod_freq_vec.push_back(mul * phase_rate);
        }
        // Phase to be updated after every sample. Starts at 0.
        mod_phase_vec.resize(mod_params.harmonics.size(), 0);
    }

    virtual void set_frame_size(size_t num_samples) {
        frame_size = num_samples;
    }

    virtual bool has_ended() {
        return progress >= size;
    }

    virtual size_t get_size() {
        return size;
    }

    // Compute the next sample using FM synthesis
    float get_next_sample() {
        // Sum of all modulation components
        float comp_sum = 0;
        for (size_t comp = 0; comp < mod_freq_vec.size(); comp++) {
            // Update the phases of modulation signal
            mod_phase_vec[comp] += mod_freq_vec[comp];
            // Modulation component value, with scaling
            float val = sinf(mod_phase_vec[comp]) * mod_params.amps[comp];
            // Update sum of all components
            comp_sum += val;
        }
        // Get modulation signal's envelope
        float mod_env = mod_env_gen.get_next_sample();
        // Find the final modulating signal
        float mod_signal_value = 1 + comp_sum * mod_env;
        // Update final phase for the signal
        base_phase += (phase_rate * mod_signal_value);
        // Envelope for the final signal
        float signal_env = env_gen.get_next_sample();
        // Convert to final signal
        float sig = sinf(base_phase) * signal_env * gain;
        // Update progress
        progress++;
        return sig;
    }

    virtual bool next_frame(std::vector<float> &frame) {
        size_t remaining = size - progress;
        size_t result_size = frame_size;
        if (remaining < result_size) {
            result_size = remaining;
        }

        frame.resize(result_size);
        for (size_t ii = 0; ii < result_size; ii++) {
            frame[ii] = get_next_sample();
        }

        return progress >= size;
    }

};


}

#endif
