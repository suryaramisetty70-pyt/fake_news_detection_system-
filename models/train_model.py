"""
🔍 Fake News Detection — Model Training Script
================================================
Run this on Google Colab (FREE GPU) to train the DistilBERT model.

Instructions:
1. Go to https://colab.research.google.com
2. Upload this file or copy-paste the code
3. Change runtime to GPU: Runtime → Change runtime type → T4 GPU
4. Run all cells
5. Download the saved model folder and place it in models/saved_model/

Dataset: ISOT Fake News Dataset (download from Kaggle)
Model: Multilingual DistilBERT
Expected Accuracy: 93-97%
Cost: ₹0 (Google Colab free GPU)
"""

# ====================================================================
# CELL 1: Install Dependencies
# ====================================================================
# !pip install transformers datasets accelerate scikit-learn pandas

# ====================================================================
# CELL 2: Import Libraries
# ====================================================================
import os
import pandas as pd
import numpy as np
from sklearn.model_selection import train_test_split
from sklearn.metrics import (
    accuracy_score, precision_score, recall_score,
    f1_score, classification_report, confusion_matrix
)
import torch
from torch.utils.data import Dataset, DataLoader
from transformers import (
    AutoTokenizer,
    AutoModelForSequenceClassification,
    TrainingArguments,
    Trainer,
    EarlyStoppingCallback,
)

print("✅ All libraries imported successfully!")
print(f"🖥️ GPU Available: {torch.cuda.is_available()}")
if torch.cuda.is_available():
    print(f"🎮 GPU Name: {torch.cuda.get_device_name(0)}")


# ====================================================================
# CELL 3: Download & Load Dataset
# ====================================================================
# Option A: Download from Kaggle (recommended)
# Upload True.csv and Fake.csv to Colab, or use kaggle API:
# !pip install kaggle
# !kaggle datasets download -d clmentbisaillon/fake-and-real-news-dataset

# Option B: Load from uploaded files
# Upload True.csv and Fake.csv to your Colab session

def load_dataset(true_path='True.csv', fake_path='Fake.csv'):
    """Load and prepare the ISOT Fake News Dataset."""
    
    # Check if files exist
    if not os.path.exists(true_path) or not os.path.exists(fake_path):
        print("⚠️ Dataset files not found!")
        print("📥 Please download from Kaggle:")
        print("   https://www.kaggle.com/datasets/clmentbisaillon/fake-and-real-news-dataset")
        print("   Upload True.csv and Fake.csv to this Colab session.")
        return None
    
    # Load data
    df_true = pd.read_csv(true_path)
    df_fake = pd.read_csv(fake_path)
    
    # Add labels: 1 = Real, 0 = Fake
    df_true['label'] = 1
    df_fake['label'] = 0
    
    # Combine
    df = pd.concat([df_true, df_fake], ignore_index=True)
    
    # Combine title and text for better features
    df['content'] = df['title'].fillna('') + ' ' + df['text'].fillna('')
    
    # Clean
    df = df[['content', 'label']].dropna()
    df = df[df['content'].str.len() > 20]  # Remove very short texts
    
    # Shuffle
    df = df.sample(frac=1, random_state=42).reset_index(drop=True)
    
    print(f"✅ Dataset loaded: {len(df)} articles")
    print(f"   Real: {(df['label'] == 1).sum()} | Fake: {(df['label'] == 0).sum()}")
    
    return df

# Uncomment when running on Colab:
# df = load_dataset()


# ====================================================================
# CELL 4: Prepare Dataset Class
# ====================================================================
class NewsDataset(Dataset):
    """Custom PyTorch Dataset for news articles."""
    
    def __init__(self, texts, labels, tokenizer, max_length=512):
        self.texts = texts
        self.labels = labels
        self.tokenizer = tokenizer
        self.max_length = max_length
    
    def __len__(self):
        return len(self.texts)
    
    def __getitem__(self, idx):
        text = str(self.texts[idx])
        label = int(self.labels[idx])
        
        encoding = self.tokenizer(
            text,
            add_special_tokens=True,
            max_length=self.max_length,
            padding='max_length',
            truncation=True,
            return_attention_mask=True,
            return_tensors='pt',
        )
        
        return {
            'input_ids': encoding['input_ids'].flatten(),
            'attention_mask': encoding['attention_mask'].flatten(),
            'labels': torch.tensor(label, dtype=torch.long),
        }


# ====================================================================
# CELL 5: Train the Model
# ====================================================================
def train_model(df, model_name='distilbert-base-multilingual-cased', epochs=3):
    """Fine-tune Multilingual DistilBERT on the fake news dataset."""
    
    print(f"🚀 Training with model: {model_name}")
    print(f"📊 Dataset size: {len(df)} articles")
    
    # Split data
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['content'].tolist(),
        df['label'].tolist(),
        test_size=0.2,
        random_state=42,
        stratify=df['label']
    )
    
    print(f"   Train: {len(train_texts)} | Validation: {len(val_texts)}")
    
    # Load tokenizer and model
    tokenizer = AutoTokenizer.from_pretrained(model_name)
    model = AutoModelForSequenceClassification.from_pretrained(
        model_name,
        num_labels=2,
        id2label={0: 'FAKE', 1: 'REAL'},
        label2id={'FAKE': 0, 'REAL': 1},
    )
    
    # Create datasets
    train_dataset = NewsDataset(train_texts, train_labels, tokenizer)
    val_dataset = NewsDataset(val_texts, val_labels, tokenizer)
    
    # Training arguments (optimized for Colab free GPU)
    training_args = TrainingArguments(
        output_dir='./results',
        num_train_epochs=epochs,
        per_device_train_batch_size=16,
        per_device_eval_batch_size=32,
        warmup_steps=500,
        weight_decay=0.01,
        logging_dir='./logs',
        logging_steps=100,
        eval_strategy='epoch',
        save_strategy='epoch',
        load_best_model_at_end=True,
        metric_for_best_model='f1',
        greater_is_better=True,
        fp16=torch.cuda.is_available(),  # Mixed precision on GPU
        report_to='none',  # Don't report to wandb
    )
    
    # Metrics function
    def compute_metrics(pred):
        labels = pred.label_ids
        preds = pred.predictions.argmax(-1)
        return {
            'accuracy': accuracy_score(labels, preds),
            'f1': f1_score(labels, preds, average='weighted'),
            'precision': precision_score(labels, preds, average='weighted'),
            'recall': recall_score(labels, preds, average='weighted'),
        }
    
    # Trainer
    trainer = Trainer(
        model=model,
        args=training_args,
        train_dataset=train_dataset,
        eval_dataset=val_dataset,
        compute_metrics=compute_metrics,
        callbacks=[EarlyStoppingCallback(early_stopping_patience=2)],
    )
    
    # Train!
    print("🏋️ Training started...")
    trainer.train()
    
    # Evaluate
    print("\n📊 Evaluation Results:")
    results = trainer.evaluate()
    for key, value in results.items():
        if isinstance(value, float):
            print(f"   {key}: {value:.4f}")
    
    # Detailed classification report
    predictions = trainer.predict(val_dataset)
    preds = predictions.predictions.argmax(-1)
    print("\n📋 Classification Report:")
    print(classification_report(
        val_labels, preds,
        target_names=['FAKE', 'REAL']
    ))
    
    return model, tokenizer, trainer


# ====================================================================
# CELL 6: Save Model
# ====================================================================
def save_model(model, tokenizer, save_path='./saved_model'):
    """Save the fine-tuned model and tokenizer."""
    
    model.save_pretrained(save_path)
    tokenizer.save_pretrained(save_path)
    
    print(f"✅ Model saved to: {save_path}")
    print(f"📦 Files saved:")
    for f in os.listdir(save_path):
        size = os.path.getsize(os.path.join(save_path, f))
        print(f"   {f} ({size / (1024*1024):.1f} MB)")
    
    print("\n📥 Download this folder and place it in your project:")
    print("   fake-news-detector/models/saved_model/")


# ====================================================================
# CELL 7: Train Fallback Model (TF-IDF + Logistic Regression)
# ====================================================================
def train_fallback_model(df, save_dir='./'):
    """Train a lightweight TF-IDF + Logistic Regression model.
    
    This runs on CPU and is used as a fallback when the
    transformer model is not available.
    """
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    import pickle
    
    print("🔧 Training fallback model (TF-IDF + Logistic Regression)...")
    
    # Split
    train_texts, val_texts, train_labels, val_labels = train_test_split(
        df['content'].tolist(),
        df['label'].tolist(),
        test_size=0.2,
        random_state=42,
    )
    
    # TF-IDF Vectorizer
    vectorizer = TfidfVectorizer(
        max_features=50000,
        ngram_range=(1, 2),
        stop_words='english',
        min_df=2,
        max_df=0.95,
    )
    
    # Fit and transform
    X_train = vectorizer.fit_transform(train_texts)
    X_val = vectorizer.transform(val_texts)
    
    # Train Logistic Regression
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
    f1 = f1_score(val_labels, val_preds, average='weighted')
    
    print(f"✅ Fallback model trained!")
    print(f"   Accuracy: {accuracy:.4f}")
    print(f"   F1-Score: {f1:.4f}")
    print(f"\n📋 Classification Report:")
    print(classification_report(val_labels, val_preds, target_names=['FAKE', 'REAL']))
    
    # Save
    model_path = os.path.join(save_dir, 'fallback_model.pkl')
    vectorizer_path = os.path.join(save_dir, 'tfidf_vectorizer.pkl')
    
    with open(model_path, 'wb') as f:
        pickle.dump(model, f)
    with open(vectorizer_path, 'wb') as f:
        pickle.dump(vectorizer, f)
    
    print(f"\n💾 Saved: {model_path}")
    print(f"💾 Saved: {vectorizer_path}")
    print("\n📥 Download these files and place them in:")
    print("   fake-news-detector/models/")
    
    return model, vectorizer


# ====================================================================
# CELL 8: Run Everything
# ====================================================================
# Uncomment the lines below when running on Google Colab:

# # Step 1: Load dataset
# df = load_dataset('True.csv', 'Fake.csv')
#
# # Step 2: Train DistilBERT (needs GPU, ~30-45 min on Colab T4)
# model, tokenizer, trainer = train_model(df, epochs=3)
# save_model(model, tokenizer, './saved_model')
#
# # Step 3: Train fallback model (CPU, ~2 min)
# fallback_model, vectorizer = train_fallback_model(df, './')
#
# # Step 4: Download files
# # On Colab: Right-click saved_model folder → Download
# # Or use: !zip -r saved_model.zip saved_model/
# print("\n🎉 All done! Download the model files and place them in your project.")
