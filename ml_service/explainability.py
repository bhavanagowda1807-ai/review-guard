"""Explainability hooks — text and metadata only (GradCAM removed)."""
import numpy as np
import shap
import lime.lime_text


class SHAPExplainer:
    def __init__(self, predict_fn, background_data: np.ndarray):
        self.predict_fn = predict_fn
        self.explainer = shap.KernelExplainer(self.predict_fn, background_data)

    def explain(self, X: np.ndarray, feature_names=None):
        shap_values = self.explainer.shap_values(X)
        expected_value = self.explainer.expected_value
        if isinstance(shap_values, list):
            shap_values = [sv.tolist() if isinstance(sv, np.ndarray) else sv for sv in shap_values]
        else:
            shap_values = np.array(shap_values).tolist()
        base_value = float(expected_value[0]) if isinstance(expected_value, (list, tuple, np.ndarray)) else float(expected_value)
        return {
            'shap_values': shap_values,
            'base_value': base_value,
            'feature_names': feature_names or [f'feature_{i}' for i in range(X.shape[1])],
        }


class LIMEExplainer:
    def __init__(self, predict_proba_fn):
        self.explainer = lime.lime_text.LimeTextExplainer(class_names=['genuine', 'fake'])
        self.predict_proba_fn = predict_proba_fn

    def explain(self, text: str, num_samples: int = 1000):
        exp = self.explainer.explain_instance(
            text,
            self.predict_proba_fn,
            num_samples=num_samples,
            num_features=10,
        )
        return {'feature_weights': dict(exp.as_list())}
