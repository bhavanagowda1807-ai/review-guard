"""Explainability wrapper functions for text + metadata models (image removed)."""
import numpy as np
from explainability import SHAPExplainer


def explain_text_with_lime(text: str, text_model):
    """Generate LIME explanation for text predictions."""
    def predict_fn(texts):
        scores = np.array([text_model.predict(t)['score'] for t in texts], dtype=np.float32)
        return np.vstack([1.0 - scores, scores]).T

    try:
        from explainability import LIMEExplainer
        explainer = LIMEExplainer(predict_fn)
        exp = explainer.explain(text)
        return {'lime': exp}
    except Exception as e:
        return {'lime': {'error': str(e)}}


def explain_metadata_with_shap(features_dict: dict, metadata_model):
    """Generate SHAP explanation for metadata predictions."""
    try:
        feature_values = np.array([[
            features_dict.get('account_age', 0),
            features_dict.get('reviews_per_day', 0),
            features_dict.get('verified_purchase_ratio', 0),
            features_dict.get('rating_deviation', 0),
            features_dict.get('burstiness', 0),
            features_dict.get('helpfulness_ratio', 0),
        ]], dtype=np.float32)

        def predict_fn(X):
            scores = []
            for row in X:
                entry = {
                    'account_age': float(row[0]),
                    'reviews_per_day': float(row[1]),
                    'verified_purchase_ratio': float(row[2]),
                    'rating_deviation': float(row[3]),
                    'burstiness': float(row[4]),
                    'helpfulness_ratio': float(row[5]),
                }
                scores.append(metadata_model.predict(entry)['score'])
            scores = np.array(scores, dtype=np.float32)
            return np.vstack([1.0 - scores, scores]).T

        background_data = np.random.uniform(0, 1, (100, 6)).astype(np.float32)
        explainer = SHAPExplainer(predict_fn, background_data)
        shap_out = explainer.explain(feature_values, feature_names=[
            'account_age', 'reviews_per_day', 'verified_purchase_ratio',
            'rating_deviation', 'burstiness', 'helpfulness_ratio',
        ])
        return {'shap': shap_out}
    except Exception as e:
        return {'shap': {'error': str(e)}}


def explain_fusion_attention(attention: dict):
    """Generate attention weight visualization for text+metadata fusion."""
    return {
        'attention': attention,
        'interpretation': {
            'text': f"Text modality contributes {attention.get('text', 0)*100:.1f}%",
            'meta': f"Metadata modality contributes {attention.get('meta', 0)*100:.1f}%",
        },
    }
