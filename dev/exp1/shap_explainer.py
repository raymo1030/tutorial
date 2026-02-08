import numpy as np
import shap
import pricehubble_client as phc

FEATURE_NAMES = ["livingArea", "buildingYear", "numberOfRooms", "numberOfBathrooms"]
FEATURE_LABELS = {
    "livingArea": "面積 (m²)",
    "buildingYear": "築年",
    "numberOfRooms": "部屋数",
    "numberOfBathrooms": "バスルーム数",
}


def _build_background(target_values):
    """Generate background samples around the target property values.

    Creates a small grid varying each feature within realistic ranges
    to keep API call count low (≈15 samples).
    """
    area, year, rooms, baths = target_values

    areas = np.clip([area * 0.7, area * 0.85, area, area * 1.15, area * 1.3], 15, None)
    years = np.clip(
        [year - 20, year - 10, year, year + 10, year + 20], 1800, 2026
    ).astype(int)
    room_opts = np.clip([rooms - 2, rooms - 1, rooms, rooms + 1, rooms + 2], 1, None).astype(int)
    bath_opts = np.clip([baths - 1, baths, baths + 1], 1, None).astype(int)

    # Small diverse sample set to minimize API calls
    rng = np.random.RandomState(42)
    samples = []
    for _ in range(5):
        samples.append([
            rng.choice(areas),
            rng.choice(years),
            rng.choice(room_opts),
            rng.choice(bath_opts),
        ])
    return np.array(samples, dtype=float)


def _make_predict_fn(base_property, country_code, deal_type):
    """Return a function that maps feature arrays → sale prices via PriceHubble."""

    def predict_fn(X):
        properties = []
        for row in X:
            prop = _apply_features(base_property, row)
            properties.append(prop)

        valuations = phc.valuate(properties, country_code=country_code, deal_type=deal_type)
        prices = []
        for v in valuations:
            price = v.get("salePrice") if deal_type == "sale" else v.get("rentGross")
            prices.append(price if price is not None else 0)
        return np.array(prices, dtype=float)

    return predict_fn


def _apply_features(base_property, feature_row):
    """Create a property dict with the given feature values overlaid."""
    import copy

    prop = copy.deepcopy(base_property)
    prop["livingArea"] = float(feature_row[0])
    prop["buildingYear"] = int(feature_row[1])
    prop["numberOfRooms"] = int(feature_row[2])
    prop["numberOfBathrooms"] = int(feature_row[3])
    return prop


def explain(base_property, country_code="CH", deal_type="sale"):
    """Compute SHAP values explaining the valuation of base_property.

    Args:
        base_property: dict with location, livingArea, buildingYear, etc.
        country_code: ISO country code
        deal_type: "sale" or "rent"

    Returns:
        dict with keys:
            shap_values: array of shape (4,) — contribution of each feature
            base_value: float — expected value (background mean prediction)
            feature_names: list of feature label strings
            feature_values: list of input values
            predicted_value: float — model prediction for the target property
    """
    target = np.array([[
        base_property.get("livingArea", 80),
        base_property.get("buildingYear", 2000),
        base_property.get("numberOfRooms", 3),
        base_property.get("numberOfBathrooms", 1),
    ]], dtype=float)

    background = _build_background(target[0])
    predict_fn = _make_predict_fn(base_property, country_code, deal_type)

    explainer = shap.KernelExplainer(predict_fn, background)
    sv = explainer.shap_values(target, nsamples=16)

    shap_vals = sv[0] if sv.ndim > 1 else sv

    predicted = predict_fn(target)[0]

    return {
        "shap_values": shap_vals,
        "base_value": explainer.expected_value,
        "feature_names": [FEATURE_LABELS[f] for f in FEATURE_NAMES],
        "feature_values": target[0].tolist(),
        "predicted_value": predicted,
    }
