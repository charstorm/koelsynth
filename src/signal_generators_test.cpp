
#include <fstream>
#include <cmath>

#include "simple_tester.h"
#include "signal_generators.h"

namespace signal {

using tester::TestError;

std::vector<float> collect_frames(FrameGenerator *gen) {
    bool ended = false;
    std::vector<float> output;
    std::vector<float> frame;
    output.reserve(gen->get_size());
    while (!ended) {
        ended = gen->next_frame(frame);
        for (float x: frame) {
            output.push_back(x);
        }
    }
    return output;
}


class Signal_Tester {
public:
    static void test_ConstantGenerator() {
        float val = 11;
        size_t size = 99;
        size_t frame_size = 17;
        ConstantGenerator gen(val, size);
        gen.set_frame_size(frame_size);

        size_t total_output_size = 0;
        std::vector<float> frame;
        for (size_t ii = 0; ii < 10; ii++) {
            bool ended = gen.next_frame(frame);
            total_output_size += frame.size();
            THROW_IF(frame.size() > frame_size, "Mismatch in frame size");
            if (total_output_size == size) {
                THROW_IF(!ended, "Expects the stream to end when size match");
            }
            THROW_IF(gen.remaining + total_output_size != size,
                    "Sizes are not adding up");
            for (auto x:  frame) {
                THROW_IF(x != val, "Value mismatch");
            }
        }
        THROW_IF(total_output_size != size, "Mismatch in total_output_size");
        THROW_IF(gen.remaining != 0, "Remaining must be 0 at the end");
    }

    static void test_RampGenerator() {
        float lower = 0.477f;
        float upper = 15.22f;
        size_t size = 1333;
        size_t frame_size = 127;
        size_t num_frames = size / frame_size;
        float eps = 2e-6f;
        float delta = (upper - lower) / (size - 1);

        RampGenerator gen(lower, upper, size);
        gen.set_frame_size(frame_size);

        std::vector<float> samples;
        samples.reserve(size);
        std::vector<float> frame;
        for (size_t ii = 0; ii < num_frames + 10; ii++) {
            gen.next_frame(frame);
            for (float x: frame) {
                samples.push_back(x);
            }
        }
        THROW_IF(samples.size() != size, "Total samples size mismatch");
        float first = samples[0];
        float last = samples[samples.size()-1];
        THROW_IF(std::abs(first-lower) > eps,
            "first value is not close enough");
        THROW_IF(std::abs(last-upper) > eps,
            "last value is not close enough");
        THROW_IF(!gen.has_ended(),
            "generator has not ended");
        for (size_t ii = 0; ii < samples.size() - 1; ii++) {
            float diff = samples[ii+1] - samples[ii];
            THROW_IF(std::abs(diff-delta) > eps,
                "difference between samples do not match");
        }
    }

    static void test_ExponentialGenerator() {
        size_t halfing_size = 16;
        size_t size = 128;
        size_t frame_size = 32;
        float start = 128.0f;

        ExponentialGenerator gen(start, halfing_size, size);
        gen.set_frame_size(frame_size);
        THROW_IF(std::abs(gen.decay - 0.95760) > 0.0001,
                "Decay calculation is wrong");
        std::vector<float> output =
            collect_frames(static_cast<FrameGenerator*>(&gen));
        THROW_IF(output.size() != size, "Size mismatch");
        THROW_IF(!gen.has_ended(), "Generated has not ended!");
        float expected = start;
        for (size_t idx = 0; idx < size; idx += halfing_size) {
            float absdiff = std::abs(output[idx] - expected);
            THROW_IF(std::abs(output[idx] - expected) > 0.00001,
                "Calculated exponential deviates too much " +
                std::to_string(absdiff));
            expected /= 2.0f;
        }
    }

    static void test_AdsrEnvelope() {
        size_t frame_size = 200;
        AdsrParams params = {
            .attack = 200,
            .decay = 100,
            .sustain = 2000,
            .release = 300,
            .slevel1 = 0.7,
        };

        size_t size_total = 200 + 100 + 2000 + 300;

        AdsrEnvelope envelope(params);
        envelope.set_frame_size(frame_size);
        std::vector<float> samples = collect_frames(&envelope);
        THROW_IF(samples.size() != size_total,
                 "Total size mismatch");
        float max_abs_diff = 0;
        for (size_t ii = 0; ii < samples.size() - 1; ii++) {
            float diff = samples[ii+1] - samples[ii];
            float abs_diff = fabs(diff);
            if (abs_diff > max_abs_diff) {
                max_abs_diff = abs_diff;
            }
            float sign = 1.0f;
            if (ii >= params.attack) {
                sign = -1.0f;
            }
            float eps = 1e-8f;
            THROW_IF(diff * sign < -eps,
                "Sign mismatch for difference ");
        }
        THROW_IF(max_abs_diff > 0.01,
                "Maximum sample difference beyond threshold");
    }

    static void test_FmSynthGenerator() {
        size_t frame_size = 160;
        AdsrParams env_params = {
            .attack = 800,
            .decay = 800,
            .sustain = 16000,
            .release = 800,
            .slevel1 = 0.5,
            .slevel2 = 0.05,
        };

        FmSynthModParams mod_params = {
            .harmonics = {2, 6, 11},
            .amps = {1, 1, 1}
        };

        FmSynthGenerator fmsynth(
            mod_params, env_params, env_params,
            compute_phase_per_sample(440.0f, 16000.0f)
        );
        fmsynth.set_frame_size(frame_size);

        std::vector<float> samples = collect_frames(&fmsynth);
        THROW_IF(samples.size() != env_params.get_size(),
                "Total size mismatch");
        // TODO: add more tests!
    }

};

}

void test_all() {
    using namespace signal;
    using namespace tester;

    TestCollection tests;
    ADD_TEST(tests, Signal_Tester::test_ConstantGenerator);
    ADD_TEST(tests, Signal_Tester::test_RampGenerator);
    ADD_TEST(tests, Signal_Tester::test_ExponentialGenerator);
    ADD_TEST(tests, Signal_Tester::test_AdsrEnvelope);
    ADD_TEST(tests, Signal_Tester::test_FmSynthGenerator);
    run_tests(tests);
}

int main() {
    test_all();
    return 0;
}
