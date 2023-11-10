
#include <pybind11/pybind11.h>
#include <pybind11/stl.h>
#include <pybind11/numpy.h>

#include "signal_generators.h"
#include "sequencer.h"

namespace py = pybind11;
using namespace pybind11::literals;
using namespace signal;

// ssize_t is note defined for msvc ...
#if defined(_MSC_VER)
#include <BaseTsd.h>
typedef SSIZE_T ssize_t;
#endif

void add_fmsynth(
    Sequencer &seq,
    FmSynthModParams &mod_params,
    AdsrParams mod_env_params,
    AdsrParams env_params,
    float base_freq
) {
    auto gen = new FmSynthGenerator(
        mod_params, mod_env_params, env_params, base_freq
    );
    seq.add(gen);
}

void get_next_frame(Sequencer &seq, py::array_t<float> &output) {
    if (output.ndim() != 1) {
        throw std::invalid_argument("need a single dimensional array");
    }

    if (output.shape(0) != (ssize_t) seq.get_frame_size()) {
        throw std::invalid_argument("input must be of frame size");
    }

    std::vector<float> frame = seq.next_frame();
    for (size_t ii = 0; ii < frame.size(); ii++) {
        output.mutable_at(ii) = frame[ii];
    }
}

PYBIND11_MODULE(koelsynth, m) {
    m.doc() = "A simple, synchronous music synthesis library";

    m.def("key_to_phase_per_sample", &key_to_phase_per_sample,
          "key"_a, "sample_rate"_a);

    // AdsrParams - Envelope parameters
    py::class_<AdsrParams>(m, "AdsrParams")
        .def(py::init<size_t, size_t, size_t, size_t, float, float>(),
             "Configuration parameter for ADSR envelope",
             "attack"_a = 100, "decay"_a = 100, "sustain"_a = 16000,
             "release"_a = 100, "slevel1"_a = 0.5, "slevel2"_a = 0.1)
        .def_readwrite("attack", &AdsrParams::attack,
                "attack duration in samples")
        .def_readwrite("decay", &AdsrParams::decay,
                "decay duration in samples")
        .def_readwrite("sustain", &AdsrParams::sustain,
                "sustain duration in samples")
        .def_readwrite("release", &AdsrParams::release,
                "release duration in samples")
        .def_readwrite("slevel1", &AdsrParams::slevel1,
                "starting level for sustain")
        .def_readwrite("slevel2", &AdsrParams::slevel2,
                "ending level for sustain")
        .def("get_size", &AdsrParams::get_size,
                "Return the total size in samples")
        .def("__repr__", &AdsrParams::to_string,
                "Return the string representation of this data")
        .def("copy", [](const AdsrParams &params) {
                AdsrParams result = params;
                return result;
            }, "Create a copy");

    py::class_<FmSynthModParams>(m, "FmSynthModParams")
        .def(py::init<std::vector<float>, std::vector<float>>(),
             "FM synthesis modulation parameters",
             "harmonics"_a = std::vector<float> {2.0f},
             "amps"_a = std::vector<float> {1.0f})
        .def_readwrite("harmonics", &FmSynthModParams::harmonics)
        .def_readwrite("amps", &FmSynthModParams::amps)
        .def("copy", [](const FmSynthModParams &params) {
                FmSynthModParams result = params;
                return result;
            });

    py::class_<Sequencer>(m, "Sequencer")
        .def(py::init<size_t, float>(), "Create a Sequencer",
             "frame_size"_a = DEFAULT_FRAME_SIZE,
             "gain"_a = 1.0f)
        .def("add_fmsynth", &add_fmsynth, "Add FM synth event",
            "mod_params"_a, "mod_env_params"_a,
            "env_params"_a, "phase_per_sample"_a)
        .def("get_frame_size", &Sequencer::get_frame_size,
             "Return the frame size expected by the sequencer")
        .def("get_generator_count", &Sequencer::get_generator_count,
             "Return the current number of generators")
        .def("next", &get_next_frame, "Fill the next frame of samples",
             "array"_a);

}

// Following is used by cppimport
#if 0
<%
cfg['compiler_args'] = ['-std=c++17', '-Wall', '-Wextra']
cfg['dependencies'] = """
frame_generator.h
signal_generators.h
sequencer.h
""".split()
cfg['sources'] = []
setup_pybind11(cfg)
%>
#endif
