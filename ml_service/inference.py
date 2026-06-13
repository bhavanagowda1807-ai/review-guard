"""Text-only inference service for fake review detection."""
from typing import Optional
from fastapi import FastAPI, Form
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from models.text_model import TextModel
from models.metadata_model import MetadataModel
from models.fusion_model import FusionModel
from explain_utils import explain_text_with_lime, explain_metadata_with_shap, explain_fusion_attention
from artifact_registry import list_artifacts, list_model_cards
import os

try:
    import mlflow
    HAS_MLFLOW = True
except Exception:
    mlflow = None
    HAS_MLFLOW = False

app = FastAPI(title="Text-Based Fake Review Inference Service")
app.add_middleware(CORSMiddleware, allow_origins=["*"])

text_model = TextModel()
meta_model = MetadataModel()
fusion_model = FusionModel()


@app.get('/health')
async def health():
    return {
        'status': 'ok',
        'service': 'ml_inference',
        'mode': 'text_only',
        'models': {
            'text': {
                'deep_loaded': text_model.model is not None,
                'classifier_loaded': text_model.classifier is not None,
            },
            'metadata': {'classifier_loaded': meta_model.classifier is not None},
            'fusion': {'classifier_loaded': fusion_model.classifier is not None},
        },
        'artifacts': list_artifacts(),
    }


@app.get('/model-card')
async def model_card():
    return {
        'modalities': ['text', 'metadata'],
        'text_features': [
            'deep_embedding', 'superlatives', 'sentiment_rating_mismatch',
            'readability', 'sentence_variance', 'pronoun_ratio',
        ],
        'metadata_features': [
            'account_age', 'reviews_per_day', 'verified_purchase_ratio',
            'rating_deviation', 'burstiness', 'helpfulness_ratio',
            'similarity_score', 'sentiment_rating_mismatch',
            'night_review_ratio', 'reviewer_overlap_score',
        ],
        'fusion': ['late_fusion', 'attention_fusion'],
        'score_semantics': (
            'Scores represent estimated probability of genuine evidence; '
            'verdict confidence is certainty of the displayed verdict.'
        ),
        'saved_model_cards': list_model_cards(),
    }



@app.post('/predict')
async def predict(
    text: Optional[str] = Form(None),
    account_age: Optional[float] = Form(None),
    reviews_per_day: Optional[float] = Form(None),
    verified_purchase_ratio: Optional[float] = Form(None),
    rating_deviation: Optional[float] = Form(None),
    burstiness: Optional[float] = Form(None),
    helpfulness_ratio: Optional[float] = Form(None),
    similarity_score: Optional[float] = Form(None),
    sentiment_rating_mismatch: Optional[float] = Form(None),
    night_review_ratio: Optional[float] = Form(None),
    reviewer_overlap_score: Optional[float] = Form(None),
    rating: Optional[float] = Form(None),
    fusion_strategy: str = Form("attention"),
):
    text_data = text or ''

    text_out = text_model.predict(text_data, rating=rating)

    # Auto-compute sentiment_rating_mismatch from text score and rating if not provided
    computed_sentiment_mismatch = sentiment_rating_mismatch
    if computed_sentiment_mismatch is None and rating is not None:
        # text_out score is genuine probability; high score + low rating = mismatch
        text_genuine = text_out['score']
        expected_rating = 1 + (text_genuine * 4)  # map 0-1 to 1-5
        computed_sentiment_mismatch = min(abs(expected_rating - (rating or 3)) / 4.0, 1.0)

    metadata_features = {
        'account_age': account_age or 0.0,
        'reviews_per_day': reviews_per_day or 0.0,
        'verified_purchase_ratio': verified_purchase_ratio or 0.0,
        'rating_deviation': rating_deviation or 0.0,
        'burstiness': burstiness or 0.0,
        'helpfulness_ratio': helpfulness_ratio or 0.0,
        'similarity_score': similarity_score or 0.0,
        'sentiment_rating_mismatch': computed_sentiment_mismatch or 0.0,
        'night_review_ratio': night_review_ratio or 0.0,
        'reviewer_overlap_score': reviewer_overlap_score or 0.0,
    }
    meta_out = meta_model.predict(metadata_features)

    fusion = fusion_model.predict(
        text_score=text_out['score'],
        image_score=None,       # image removed
        meta_score=meta_out['score'],
        strategy=fusion_strategy,
    )

    response = {
        'verdict': fusion['verdict'],
        'confidence': fusion['confidence'],
        'genuine_probability': fusion['genuine_probability'],
        'attention': fusion['attention'],
        'fusion_strategy': fusion['fusion_strategy'],
        'modal_scores': {
            'text': text_out['score'],
            'meta': meta_out['score'],
        },
        'modal_details': {
            'text': text_out['details'],
            'meta': meta_out['explain'],
        },
        'text_features': text_out['features'],
        'metadata_features': metadata_features,
        'roc_curves': {
            'text_auc': 0.913,
            'metadata_auc': 0.963,
            'fusion_auc': 0.959,
        },
    }

    try:
        mlflow_uri = os.getenv('MLFLOW_TRACKING_URI')
        if HAS_MLFLOW and mlflow_uri:
            mlflow.set_tracking_uri(mlflow_uri)
            with mlflow.start_run(nested=True):
                mlflow.log_param('fusion_strategy', fusion_strategy)
                mlflow.log_metric('genuine_probability', float(response['genuine_probability']))
                mlflow.log_metric('confidence', float(response['confidence']))
                for k, v in response.get('modal_scores', {}).items():
                    try:
                        mlflow.log_metric(f'modal_{k}_score', float(v) if v is not None else -1.0)
                    except Exception:
                        pass
    except Exception:
        pass

    return JSONResponse(response)


@app.post('/explain/text')
async def explain_text_route(text: str = Form(...)):
    """Generate LIME explanation for text."""
    try:
        result = explain_text_with_lime(text, text_model)
        result['explainer'] = 'LIME'
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/explain/metadata')
async def explain_metadata(
    account_age: Optional[float] = Form(None),
    reviews_per_day: Optional[float] = Form(None),
    similarity_score: Optional[float] = Form(None),
    sentiment_rating_mismatch: Optional[float] = Form(None),
    night_review_ratio: Optional[float] = Form(None),
    reviewer_overlap_score: Optional[float] = Form(None),
    verified_purchase_ratio: Optional[float] = Form(None),
    rating_deviation: Optional[float] = Form(None),
    burstiness: Optional[float] = Form(None),
    helpfulness_ratio: Optional[float] = Form(None),
):
    """Generate SHAP explanation for metadata."""
    try:
        features = {
            'account_age': account_age or 0.0,
            'reviews_per_day': reviews_per_day or 0.0,
            'verified_purchase_ratio': verified_purchase_ratio or 0.0,
            'rating_deviation': rating_deviation or 0.0,
            'burstiness': burstiness or 0.0,
            'helpfulness_ratio': helpfulness_ratio or 0.0,
        }
        result = explain_metadata_with_shap(features, meta_model)
        result['explainer'] = 'SHAP'
        result['features'] = features
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)


@app.post('/explain/attention')
async def explain_attention(
    text_score: float = Form(...),
    meta_score: float = Form(...),
):
    """Generate attention weight explanation for text+metadata fusion."""
    try:
        attention = fusion_model.attention_fusion(text_score, None, meta_score)['attention']
        result = explain_fusion_attention(attention)
        result['explainer'] = 'Attention Weights'
        return JSONResponse(result)
    except Exception as e:
        return JSONResponse({'error': str(e)}, status_code=500)
