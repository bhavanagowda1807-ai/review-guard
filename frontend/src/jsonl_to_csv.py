import json
import pandas as pd

rows = []

with open("All_Beauty.jsonl", "r", encoding="utf-8") as f:
    for line in f:
        rows.append(json.loads(line))

df = pd.DataFrame(rows)

df.to_csv("amazon_reviews.csv", index=False)

print(df.head())
print("CSV created successfully!")