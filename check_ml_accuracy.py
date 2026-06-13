import sys
sys.path.insert(0, '/app')
import os
import json
import pickle

MODEL_DIR = "/app/saved_models"

print("=" * 80)
print("ML MODELS ACCURACY & PERFORMANCE METRICS")
print("=" * 80)

models = ["text_classifier.card.json", "metadata_classifier.card.json", "fusion_classifier.card.json"]

for card_file in models:
    card_path = os.path.join(MODEL_DIR, card_file)
    model_name = card_file.replace(".card.json", "").replace("_", " ").title()
    
    print(f"\n{model_name}:")
    print("-" * 80)
    
    try:
        with open(card_path, 'r') as f:
            card = json.load(f)
        
        if 'metrics' in card:
            metrics = card['metrics']
            print(f"  Accuracy:    {metrics.get('accuracy', 'N/A')}")
            print(f"  ROC-AUC:     {metrics.get('roc_auc', 'N/A')}")
            
            if 'report' in metrics:
                report = metrics['report']
                if 'weighted avg' in report:
                    print(f"\n  Classification Report:")
                    print(f"    Precision (weighted): {report['weighted avg'].get('precision', 'N/A'):.4f}")
                    print(f"    Recall (weighted):    {report['weighted avg'].get('recall', 'N/A'):.4f}")
                    print(f"    F1-Score (weighted):  {report['weighted avg'].get('f1-score', 'N/A'):.4f}")
            
            print(f"\n  Features: {card.get('feature_names', [])}")
            
    except Exception as e:
        print(f"  Error: {e}")

print("\n" + "=" * 80)
print("CHECKING MODEL FILES...")
print("=" * 80)

pkl_files = [f for f in os.listdir(MODEL_DIR) if f.endswith('.pkl')]
for pkl_file in pkl_files:
    pkl_path = os.path.join(MODEL_DIR, pkl_file)
    size_kb = os.path.getsize(pkl_path) / 1024
    print(f"\n{pkl_file}: {size_kb:.2f} KB")
    
    try:
        with open(pkl_path, 'rb') as f:
            model = pickle.load(f)
        print(f"  Type: {type(model).__name__}")
        if hasattr(model, 'n_features_in_'):
            print(f"  Features: {model.n_features_in_}")
        if hasattr(model, 'classes_'):
            print(f"  Classes: {model.classes_}")
    except Exception as e:
        print(f"  Error loading: {e}")

print("\n" + "=" * 80)
print("OVERALL MODEL QUALITY")
print("=" * 80)
print("\nModels are trained and ready for inference.")
print("Check individual metrics above for accuracy and performance.")
