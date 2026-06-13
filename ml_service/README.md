# ML Service Model Artifacts

The `ml_service` container loads pretrained classifier artifacts from the mounted `saved_models` directory.

## Expected artifact files

Place the following files under `ml_service/saved_models`:

- `text_classifier.pkl`
- `image_classifier.pkl`
- `metadata_classifier.pkl`
- `fusion_classifier.pkl`

## Container mount

In `docker-compose.yml`, the `ml_inference` service mounts the local directory:

```yaml
volumes:
  - ./ml_service/saved_models:/app/saved_models:rw
```

This makes any trained `.pkl` artifacts available inside the container at `/app/saved_models`.

## Training artifacts

Use the training scripts to generate the files:

```bash
cd ml_service
python train/train.py --module text
python train/train.py --module image
python train/train.py --module metadata
python train/train.py --module fusion
```

To log metrics and model artifacts to MLflow, add `--mlflow --mlflow-uri http://localhost:5000` when running training.

If models are not present, the inference code will still run using heuristic fallbacks, but saved artifacts improve prediction consistency and enable classifier-based scoring.
