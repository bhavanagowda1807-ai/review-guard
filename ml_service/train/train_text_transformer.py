"""Fine-tune DistilBERT/RoBERTa-style text classifiers for fake-review detection.

Expected CSV columns are normalized by train.data.load_text_dataset:
- text
- rating
- label, where 0=genuine and 1=fake
"""
import argparse
import os
from pathlib import Path

import numpy as np

from train.data import load_text_dataset
from train.utils import compute_metrics, save_model_card


def main():
    parser = argparse.ArgumentParser(description="Fine-tune a transformer text classifier.")
    parser.add_argument("--text-data", required=True, help="CSV path for OPSpam/YelpZip-style text data.")
    parser.add_argument("--model-name", default="distilbert-base-uncased", help="HF model, e.g. distilbert-base-uncased or roberta-base.")
    parser.add_argument("--output-dir", default="saved_models/text_transformer", help="Directory for tokenizer/model artifacts.")
    parser.add_argument("--epochs", type=float, default=3)
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--max-length", type=int, default=256)
    parser.add_argument("--learning-rate", type=float, default=2e-5)
    parser.add_argument("--eval-split", type=float, default=0.2)
    args = parser.parse_args()

    from datasets import Dataset
    from sklearn.metrics import accuracy_score, precision_recall_fscore_support, roc_auc_score
    from sklearn.model_selection import train_test_split
    from transformers import (
        AutoModelForSequenceClassification,
        AutoTokenizer,
        DataCollatorWithPadding,
        Trainer,
        TrainingArguments,
    )

    df = load_text_dataset(args.text_data)
    train_df, eval_df = train_test_split(df, test_size=args.eval_split, random_state=42, stratify=df["label"])
    tokenizer = AutoTokenizer.from_pretrained(args.model_name)

    def tokenize(batch):
        return tokenizer(batch["text"], truncation=True, max_length=args.max_length)

    train_ds = Dataset.from_pandas(train_df[["text", "label"]], preserve_index=False).map(tokenize, batched=True)
    eval_ds = Dataset.from_pandas(eval_df[["text", "label"]], preserve_index=False).map(tokenize, batched=True)
    model = AutoModelForSequenceClassification.from_pretrained(args.model_name, num_labels=2)

    def compute_hf_metrics(eval_pred):
        logits, labels = eval_pred
        probs = np.exp(logits) / np.exp(logits).sum(axis=1, keepdims=True)
        preds = probs.argmax(axis=1)
        precision, recall, f1, _ = precision_recall_fscore_support(labels, preds, average="binary", zero_division=0)
        metrics = {
            "accuracy": float(accuracy_score(labels, preds)),
            "precision": float(precision),
            "recall": float(recall),
            "f1": float(f1),
        }
        try:
            metrics["roc_auc"] = float(roc_auc_score(labels, probs[:, 1]))
        except ValueError:
            metrics["roc_auc"] = 0.0
        return metrics

    training_args = TrainingArguments(
        output_dir=args.output_dir,
        learning_rate=args.learning_rate,
        per_device_train_batch_size=args.batch_size,
        per_device_eval_batch_size=args.batch_size,
        num_train_epochs=args.epochs,
        eval_strategy="epoch",
        save_strategy="epoch",
        load_best_model_at_end=True,
        metric_for_best_model="f1",
        report_to=["mlflow"] if os.getenv("MLFLOW_TRACKING_URI") else [],
    )
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_ds,
        eval_dataset=eval_ds,
        tokenizer=tokenizer,
        data_collator=DataCollatorWithPadding(tokenizer=tokenizer),
        compute_metrics=compute_hf_metrics,
    )
    trainer.train()
    metrics = trainer.evaluate()
    trainer.save_model(args.output_dir)
    tokenizer.save_pretrained(args.output_dir)

    save_model_card(
        str(Path(args.output_dir) / "model.card.json"),
        "text_transformer",
        metrics,
        ["transformer_logits", "transformer_cls_embedding"],
        {"0": "genuine", "1": "fake"},
    )
    print(metrics)


if __name__ == "__main__":
    main()
