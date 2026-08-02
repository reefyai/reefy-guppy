"""Compile and infer one OpenVINO graph explicitly on Intel GPU and NPU."""

from __future__ import annotations

import numpy as np
import openvino as ov


def run():
    core = ov.Core()
    available = list(core.available_devices)
    required = ('GPU', 'NPU')
    missing = [device for device in required
               if not any(value == device or value.startswith(device + '.')
                          for value in available)]
    if missing:
        raise RuntimeError(
            f'OpenVINO missing explicit devices {missing}; available={available}')

    parameter = ov.opset13.parameter([1, 4], ov.Type.f32, name='input')
    result = ov.opset13.relu(parameter)
    model = ov.Model([result], [parameter], 'reefy-hardware-probe')
    sample = np.array([[-2.0, -1.0, 3.0, 4.0]], dtype=np.float32)
    expected = np.array([[0.0, 0.0, 3.0, 4.0]], dtype=np.float32)
    outcomes = {}
    for device in required:
        compiled = core.compile_model(model, device)
        output = compiled([sample])[0]
        if not np.allclose(output, expected):
            raise RuntimeError(f'{device} inference returned {output.tolist()}')
        outcomes[device.lower()] = output.tolist()
    return {
        'backend': 'intel',
        'available_devices': available,
        'compiled_devices': list(required),
        'results': outcomes,
        'used_auto_or_cpu': False,
    }
