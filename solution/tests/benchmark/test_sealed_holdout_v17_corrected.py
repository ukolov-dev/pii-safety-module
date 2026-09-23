from app.detection.detector_v3_28 import detect
from benchmark import evaluate_quality as quality
from benchmark.evaluate_sealed_v17_corrected import (
    CORRECTED_SHA256,
    build_corrected_dataset,
)


def test_v17_corrected_derivative_is_frozen_and_meets_candidate_gate() -> None:
    assert CORRECTED_SHA256 == "d8c840f66ad73047c3a57b0e5f2b1768ebaa79ee99e8f1361176a16c373f5fa8"
    quality.detect = detect
    report = quality.evaluate_dataset(build_corrected_dataset())

    assert report["overall"]["precision"] >= 0.95
    assert report["overall"]["recall"] >= 0.95
    assert report["overall"]["f1"] >= 0.95
    assert report["round_trip_exact"]["rate"] == 1.0
