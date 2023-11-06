#ifndef KOELSYNTH_SIMPLE_TESTER
#define KOELSYNTH_SIMPLE_TESTER

#include <iostream>
#include <string>
#include <vector>

#include <exception>

namespace tester {

// Used by the tester
class TestError: public std::exception {
public:
    std::string message;
    std::string test_name;

    TestError(std::string test_name_, std::string message_):
        message(message_),
        test_name(test_name_) {
    }

    const char* what() const noexcept override {
        return message.c_str();
    }
};

typedef void (*TestFunction)();

struct NamedTestFunction {
    std::string name;
    TestFunction func;
};

typedef std::vector<NamedTestFunction> TestCollection;

#define ADD_TEST(coll, func) \
do { \
    NamedTestFunction test_pair {#func, &func}; \
    coll.push_back(test_pair); \
} while(0);

#define THROW_IF(cond, message) { \
    if (cond) { \
        throw TestError(__func__, message); \
    } \
} while(0);

// Run all the given tests
// Return true on error
bool run_tests(TestCollection &tests) {
    bool has_error = false;
    for (auto &test: tests) {
        try {
            test.func();
        }
        catch (const TestError &error) {
            std::cout << test.name << " [ERROR] " << error.message << std::endl;
            has_error = true;
        }
    }
    return has_error;
}

}

#endif
