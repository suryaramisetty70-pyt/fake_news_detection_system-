"""
Headless Training Script for Fallback Model (TF-IDF + Logistic Regression)
Runs locally on the user's CPU and trains in under 2 minutes.
No emojis to avoid Windows terminal encoding errors.
"""
import os
import pandas as pd
import pickle
from sklearn.model_selection import train_test_split
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, classification_report

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, 'data')
MODELS_DIR = os.path.join(BASE_DIR, 'models')

true_path = os.path.join(DATA_DIR, 'True.csv')
fake_path = os.path.join(DATA_DIR, 'Fake.csv')

print("Loading dataset files...")
if not os.path.exists(true_path) or not os.path.exists(fake_path):
    print("Error: True.csv or Fake.csv not found in data/ directory!")
    exit(1)

# Load data
df_true = pd.read_csv(true_path)
df_fake = pd.read_csv(fake_path)

# Labeling
df_true['label'] = 1
df_fake['label'] = 0

# Combine
df = pd.concat([df_true, df_fake], ignore_index=True)
df['content'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
df = df[['content', 'label']].dropna()
df = df[df['content'].str.len() > 20]  # Clean very short text

# Shuffle
df = df.sample(frac=1, random_state=42).reset_index(drop=True)
print(f"Dataset prepared with {len(df)} articles.")

# Split
print("Splitting dataset...")
train_texts, val_texts, train_labels, val_labels = train_test_split(
    df['content'].tolist(),
    df['label'].tolist(),
    test_size=0.2,
    random_state=42,
)

# Vectorize
print("Vectorizing text (TF-IDF)...")
vectorizer = TfidfVectorizer(
    max_features=50000,
    ngram_range=(1, 2),
    stop_words='english',
    min_df=2,
    max_df=0.95,
)
X_train = vectorizer.fit_transform(train_texts)
X_val = vectorizer.transform(val_texts)

# Train model
print("Training Logistic Regression model...")
model = LogisticRegression(
    max_iter=1000,
    C=1.0,
    solver='lbfgs',
    n_jobs=-1,
)
model.fit(X_train, train_labels)

# Evaluate
val_preds = model.predict(X_val)
accuracy = accuracy_score(val_labels, val_preds)
print(f"Training completed! Validation Accuracy: {accuracy:.2%}")
print("\nClassification Report:")
print(classification_report(val_labels, val_preds, target_names=['FAKE', 'REAL']))

# Save
model_path = os.path.join(MODELS_DIR, 'fallback_model.pkl')
vectorizer_path = os.path.join(MODELS_DIR, 'tfidf_vectorizer.pkl')

print("Saving models...")
with open(model_path, 'wb') as f:
    pickle.dump(model, f)
with open(vectorizer_path, 'wb') as f:
    pickle.dump(vectorizer, f)

print(f"Saved successfully to:\n   - {model_path}\n   - {vectorizer_path}")
