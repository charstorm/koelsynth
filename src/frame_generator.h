#ifndef KOELSYNTH_FRAME_GENERATOR_H
#define KOELSYNTH_FRAME_GENERATOR_H

#include <vector>

#define DEFAULT_FRAME_SIZE (128)

// A top level parent class to handle the behavior of a frame generator object.
// A frame is a vector of samples.
class FrameGenerator {
public:
    // Sets the frame size for processing (should be same for all modules)
    virtual void set_frame_size(size_t num_samples) = 0;
    // Returns whether the generator has ended
    virtual bool has_ended() = 0;
    // Fill the next frame to the given vector.
    // Returns whether the stream has ended.
    virtual bool next_frame(std::vector<float> &frame) = 0;
    // Total number of samples that will be generated
    virtual size_t get_size() = 0;
    // Destructor
    virtual ~FrameGenerator() {}
};

// Assumptions on generators
// 1. A generator must return either 0 of frame_size number of samples
//    for every call to next_frame (except possibly for the final frame)

#endif
