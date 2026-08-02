"""Exercise the NVIDIA CUDA Driver API and NVML without a CUDA toolkit."""

from __future__ import annotations

import ctypes
import os
import time


def _check(code, operation):
    if code != 0:
        raise RuntimeError(f'{operation} failed with code {code}')


def run():
    cuda = ctypes.CDLL('libcuda.so.1')
    nvml = ctypes.CDLL('libnvidia-ml.so.1')
    _check(cuda.cuInit(0), 'cuInit')
    count = ctypes.c_int()
    _check(cuda.cuDeviceGetCount(ctypes.byref(count)), 'cuDeviceGetCount')
    if count.value < 1:
        raise RuntimeError('CUDA reported no devices')
    device = ctypes.c_int()
    _check(cuda.cuDeviceGet(ctypes.byref(device), 0), 'cuDeviceGet')
    name = ctypes.create_string_buffer(256)
    _check(cuda.cuDeviceGetName(name, len(name), device), 'cuDeviceGetName')

    context = ctypes.c_void_p()
    _check(cuda.cuCtxCreate_v2(ctypes.byref(context), 0, device), 'cuCtxCreate')
    module = ctypes.c_void_p()
    _check(cuda.cuModuleLoad(
        ctypes.byref(module), b'/app/probe_nvidia.fatbin'), 'cuModuleLoad')
    function = ctypes.c_void_p()
    _check(cuda.cuModuleGetFunction(
        ctypes.byref(function), module, b'write_answer'), 'cuModuleGetFunction')
    device_memory = ctypes.c_uint64()
    _check(cuda.cuMemAlloc_v2(
        ctypes.byref(device_memory), ctypes.sizeof(ctypes.c_uint32)),
        'cuMemAlloc')
    argument = ctypes.c_uint64(device_memory.value)
    arguments = (ctypes.c_void_p * 1)(ctypes.cast(
        ctypes.byref(argument), ctypes.c_void_p))
    seconds = float(os.getenv('REEFY_HARDWARE_PROBE_SECONDS', '0.2'))
    if seconds < 0 or seconds > 120:
        raise RuntimeError('duration must be between 0 and 120 seconds')
    started = time.monotonic()
    launches = 0
    while True:
        _check(cuda.cuLaunchKernel(
            function, 1, 1, 1, 1, 1, 1, 0, None, arguments, None),
            'cuLaunchKernel')
        launches += 1
        if launches % 4096 == 0:
            _check(cuda.cuCtxSynchronize(), 'cuCtxSynchronize')
        if time.monotonic() - started >= seconds:
            break
    _check(cuda.cuCtxSynchronize(), 'cuCtxSynchronize')
    answer = ctypes.c_uint32()
    _check(cuda.cuMemcpyDtoH_v2(
        ctypes.byref(answer), device_memory, ctypes.sizeof(answer)),
        'cuMemcpyDtoH')
    if answer.value != 42:
        raise RuntimeError(f'CUDA kernel returned {answer.value}, expected 42')

    _check(nvml.nvmlInit_v2(), 'nvmlInit')
    handle = ctypes.c_void_p()
    _check(nvml.nvmlDeviceGetHandleByIndex_v2(
        0, ctypes.byref(handle)), 'nvmlDeviceGetHandleByIndex')

    class Utilization(ctypes.Structure):
        _fields_ = [('gpu', ctypes.c_uint), ('memory', ctypes.c_uint)]

    utilization = Utilization()
    _check(nvml.nvmlDeviceGetUtilizationRates(
        handle, ctypes.byref(utilization)), 'nvmlDeviceGetUtilizationRates')
    return {
        'backend': 'nvidia',
        'device_count': count.value,
        'device_name': name.value.decode(errors='replace'),
        'cuda_kernel_result': answer.value,
        'kernel_launches': launches,
        'nvml_gpu_utilization_pct': utilization.gpu,
        'nvml_memory_utilization_pct': utilization.memory,
    }
