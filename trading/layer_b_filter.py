import json
import math
import numpy as np
import os

MODEL_PATH = "/home/noogh/projects/noogh_unified_system/src/data/layer_b_model.json"

# Load once at startup
with open(MODEL_PATH, "r") as f:
    MODEL = json.load(f)

def statistical_alpha_filter(setup: dict) -> tuple[bool, float, str]:
    mean = np.array(MODEL["scaler_mean"])
    scale = np.array(MODEL["scaler_scale"])
    coef = np.array(MODEL["coef"])
    intercept = MODEL["intercept"]
    threshold = MODEL["threshold"]

    # Build feature vector in same order
    x = np.array([
        setup.get("atr", 0.0),
        setup.get("volume", 0.0),
        setup.get("taker_buy_ratio", 0.5),
        setup.get("rsi", 50.0),
        1.0 if setup.get("signal") == "LONG" else 0.0
    ])

    # Standardize
    z = (x - mean) / scale

    # Logit
    logit = intercept + np.dot(coef, z)

    prob = 1.0 / (1.0 + math.exp(-logit))

    if prob >= threshold:
        return True, prob, f"Statistical Alpha Confirmed ({prob:.2f})"

    return False, prob, f"Rejected ({prob:.2f})"
