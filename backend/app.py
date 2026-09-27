from flask import Flask, request, jsonify
from flask_cors import CORS
from model.extract_features import extract_features, is_top_domain
import joblib
import numpy as np

# Run from the backend/ directory (the model is loaded by a relative path).

app = Flask(__name__)
CORS(app, resources={r"/*": {"origins": "*"}}, allow_headers=["Content-Type"])

FEATURE_COLUMNS = [
    "url_length",
    "hostname_length",
    "num_dots",
    "num_hyphens",
    "num_digits",
    "num_subdomains",
    "path_depth",
    "path_length",
    "has_suspicious_keywords",
    "has_suspicious_tlds",
    "common_domain",
    "has_ip",
    "has_executable_ext",
    "has_double_extension",
    "has_query"
]

model = joblib.load("model/xgb_model.pkl")

classes = ['benign', 'defacement', 'malware', 'phishing']

@app.route('/check_link', methods=["GET", "POST"])
def check_link():
    if request.method == "GET":
        url = request.args.get("url")
    else:
        data = request.get_json(silent=True)
        url = data.get("url") if data else None

    if not url:
        return jsonify({"error": "Missing 'url'"}), 400

    features = extract_features(url)
    features = np.array([features[col] for col in FEATURE_COLUMNS]).reshape(1, -1)

    prediction = model.predict_proba(features)[0]
    pred_idx = prediction.argmax()
    predicted_class = classes[pred_idx]
    score = prediction[pred_idx]

    return jsonify({
        "class": predicted_class,
        "score": float(score)
    })


@app.route('/predict', methods=["GET", "POST"])
def predict():
    if request.method == "GET":
        url = request.args.get("url")
    else:
        data = request.get_json(silent=True)
        url = data.get("url") if data else None

    if not url:
        return jsonify({"error": "Missing 'url' in request body"}), 400

    # if (is_top_domain(url)):
    #     return jsonify({
    #         "class": "benign",
    #         "score": 1.0
    #     })

    features = extract_features(url)
    features = np.array([features[col] for col in FEATURE_COLUMNS]).reshape(1, -1)

    prediction = model.predict_proba(features)[0]
    pred_idx = prediction.argmax()
    predicted_class = classes[pred_idx]
    score = prediction[pred_idx]

    return jsonify({
        "class": predicted_class,
        "score": float(score),
        "all_scores": {cls: float(prob) for cls, prob in zip(classes, prediction)}
    })



if __name__ == "__main__":
    app.run(host="127.0.0.1", port=5000, debug=True)
