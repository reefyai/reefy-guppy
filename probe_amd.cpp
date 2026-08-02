#include <hip/hip_runtime.h>

#include <chrono>
#include <cstdlib>
#include <iostream>
#include <stdexcept>
#include <string>
#include <vector>

namespace {

void check(hipError_t result, const char* operation) {
    if (result != hipSuccess) {
        throw std::runtime_error(
            std::string(operation) + " failed: " + hipGetErrorString(result));
    }
}

__global__ void add_one(const int* input, int* output, int count) {
    int index = blockIdx.x * blockDim.x + threadIdx.x;
    if (index < count) {
        output[index] = input[index] + 1;
    }
}

std::string json_escape(const char* value) {
    std::string result;
    for (const char* cursor = value; *cursor; ++cursor) {
        if (*cursor == '\\' || *cursor == '"') {
            result.push_back('\\');
        }
        result.push_back(*cursor);
    }
    return result;
}

}  // namespace

int main(int argc, char** argv) {
    try {
        double seconds = argc > 1 ? std::stod(argv[1]) : 0.2;
        if (seconds < 0.0 || seconds > 120.0) {
            throw std::runtime_error("duration must be between 0 and 120 seconds");
        }

        int device_count = 0;
        check(hipGetDeviceCount(&device_count), "hipGetDeviceCount");
        if (device_count < 1) {
            throw std::runtime_error("HIP reported no devices");
        }
        check(hipSetDevice(0), "hipSetDevice");
        hipDeviceProp_t properties{};
        check(hipGetDeviceProperties(&properties, 0), "hipGetDeviceProperties");

        constexpr int count = 1 << 20;
        constexpr size_t bytes = count * sizeof(int);
        std::vector<int> input(count, 41);
        std::vector<int> output(count, 0);
        int* device_input = nullptr;
        int* device_output = nullptr;
        check(hipMalloc(&device_input, bytes), "hipMalloc(input)");
        check(hipMalloc(&device_output, bytes), "hipMalloc(output)");
        check(hipMemcpy(
            device_input, input.data(), bytes, hipMemcpyHostToDevice),
            "hipMemcpy(input)");

        const auto started = std::chrono::steady_clock::now();
        unsigned long long launches = 0;
        do {
            hipLaunchKernelGGL(
                add_one, dim3((count + 255) / 256), dim3(256), 0, 0,
                device_input, device_output, count);
            check(hipGetLastError(), "add_one launch");
            ++launches;
            if ((launches % 128) == 0) {
                check(hipDeviceSynchronize(), "hipDeviceSynchronize");
            }
        } while (std::chrono::duration<double>(
                     std::chrono::steady_clock::now() - started).count()
                 < seconds);
        check(hipDeviceSynchronize(), "hipDeviceSynchronize");
        check(hipMemcpy(
            output.data(), device_output, bytes, hipMemcpyDeviceToHost),
            "hipMemcpy(output)");
        check(hipFree(device_output), "hipFree(output)");
        check(hipFree(device_input), "hipFree(input)");

        for (int value : output) {
            if (value != 42) {
                throw std::runtime_error("HIP kernel returned an invalid result");
            }
        }
        std::cout << "{\"backend\":\"amd\",\"device_count\":"
                  << device_count << ",\"device_name\":\""
                  << json_escape(properties.name) << "\",\"gcn_arch\":\""
                  << json_escape(properties.gcnArchName)
                  << "\",\"hip_kernel_result\":42,\"kernel_launches\":"
                  << launches << "}" << std::endl;
        return 0;
    } catch (const std::exception& error) {
        std::cerr << error.what() << std::endl;
        return 1;
    }
}
