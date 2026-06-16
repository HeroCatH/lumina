import modelview
from modelview.parsers.simple import SimpleModel

model = SimpleModel([
    {"type": "Conv2d", "params": {"in_channels": 3, "out_channels": 64, "kernel_size": 3}},
    {"type": "ReLU", "params": {}},
    {"type": "Flatten", "params": {}},
    {"type": "Linear", "params": {"in_features": 64 * 30 * 30, "out_features": 10}},
])

if __name__ == "__main__":
    modelview.view(model, port=8080)
