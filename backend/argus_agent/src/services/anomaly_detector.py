"""Multi-signal anomaly detection for urban heat grid readings."""

from statistics import mean, pstdev

from argus_agent.src.constants import (
    ANOMALY_SIGNAL_WEIGHTS,
    SEVERITY_THRESHOLDS,
    WHO_BAND_SCORE,
    WHO_HEAT_BANDS,
)
from argus_agent.src.enums import Severity


def who_heat_band(temp_f: float) -> str:
    for lo, hi, band in WHO_HEAT_BANDS:
        if lo <= temp_f < hi:
            return band
    return "EXTREME"


def classify_severity(score: float) -> Severity:
    for threshold, severity in SEVERITY_THRESHOLDS:
        if score >= threshold:
            return Severity(severity)
    return Severity.INFO


class AnomalyDetector:
    """Scores each grid cell against its neighbors and a historical baseline."""

    def score_cell(
        self,
        temperature_f: float,
        neighbor_avg_f: float,
        baseline_mean_f: float,
        baseline_std_f: float,
        temperature_1h_ago_f: float,
    ) -> dict:
        band = who_heat_band(temperature_f)
        who_score = WHO_BAND_SCORE[band]

        z_score = (temperature_f - baseline_mean_f) / baseline_std_f if baseline_std_f else 0.0
        z_score_score = min(100.0, max(0.0, abs(z_score) * 25))

        rate = temperature_f - temperature_1h_ago_f
        rate_score = min(100.0, max(0.0, rate * 10))

        spatial_diff = temperature_f - neighbor_avg_f
        spatial_score = min(100.0, max(0.0, spatial_diff * 8))

        composite = (
            who_score * ANOMALY_SIGNAL_WEIGHTS["who_band"]
            + z_score_score * ANOMALY_SIGNAL_WEIGHTS["z_score"]
            + rate_score * ANOMALY_SIGNAL_WEIGHTS["rate_of_change"]
            + spatial_score * ANOMALY_SIGNAL_WEIGHTS["spatial_anomaly"]
        )

        return {
            "composite_score": round(composite, 1),
            "severity": classify_severity(composite),
            "signals": {
                "who_band": band,
                "z_score": round(z_score, 2),
                "rate_of_change_f_per_hr": round(rate, 1),
                "spatial_anomaly_f": round(spatial_diff, 1),
            },
        }

    @staticmethod
    def baseline_from_grid(temperatures_f: list[float]) -> tuple[float, float]:
        if len(temperatures_f) < 2:
            return (temperatures_f[0] if temperatures_f else 0.0, 1.0)
        return mean(temperatures_f), max(pstdev(temperatures_f), 0.5)


anomaly_detector = AnomalyDetector()
