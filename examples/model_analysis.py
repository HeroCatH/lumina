import lumina
from lumina.parsers.simple import SimpleModel

model = SimpleModel([
    {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3, "padding": 1}},
    {"type": "ReLU", "params": {}},
    {"type": "Flatten", "params": {}},
    {"type": "Linear", "params": {"in_features": 64 * 32 * 32, "out_features": 10}},
])

stats = lumina.analyze(model, input_shape=[1, 3, 32, 32])
print("Params:", stats["params"]["total_params"])
print("FLOPs:", stats["flops"]["total_flops"])
print("Memory (MB):", stats["memory"]["param_megabytes"])
print("Output shape:", stats["shapes"]["output_shape"])
