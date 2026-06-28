#!/usr/bin/env python3
"""Produce a subject/background matte using U2Net (the model rembg uses),
without the rembg package. Outputs a grayscale PNG: white = subject.

Usage: subject_mask.py INPUT_IMAGE OUTPUT_MASK_PNG
"""
import sys, os
import numpy as np
from PIL import Image
import onnxruntime as ort

HERE = os.path.dirname(os.path.abspath(__file__))
MODEL = os.path.join(HERE, "models", "u2net.onnx")
MEAN = (0.485, 0.456, 0.406)
STD = (0.229, 0.224, 0.225)
SIZE = (320, 320)


def main(inp, outp):
    img = Image.open(inp).convert("RGB")
    w0, h0 = img.size

    im = img.resize(SIZE, Image.LANCZOS)
    a = np.array(im).astype(np.float64)
    a = a / np.max(a)
    t = np.zeros((SIZE[1], SIZE[0], 3))
    for c in range(3):
        t[:, :, c] = (a[:, :, c] - MEAN[c]) / STD[c]
    t = t.transpose((2, 0, 1))[None, ...].astype(np.float32)

    sess = ort.InferenceSession(MODEL, providers=["CPUExecutionProvider"])
    pred = sess.run(None, {sess.get_inputs()[0].name: t})[0][:, 0, :, :]
    pred = (pred - pred.min()) / (pred.max() - pred.min() + 1e-8)
    mask = Image.fromarray((pred.squeeze() * 255).astype(np.uint8), mode="L")
    mask = mask.resize((w0, h0), Image.LANCZOS)
    mask.save(outp)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
