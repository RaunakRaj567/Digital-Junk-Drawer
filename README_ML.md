# 🤖 Digital Junk Drawer: Machine Learning Implementation Guide

Welcome to the **Machine Learning** documentation for **Digital Junk Drawer**! This guide explains how the document classification model works in clear, beginner-friendly layman's language, with direct references to the accompanying Jupyter Notebook: [`text-classification-using-naive-bayes.ipynb`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/text-classification-using-naive-bayes.ipynb).

---

## 🌟 1. The Big Picture: What Problem Does the ML Model Solve?

Imagine you have a messy downloads folder with hundreds of files named:
- `champions_league_final.mp4`
- `Tesla_Q3_Earnings_Report.xlsx`
- `parliament_election_turnout.pdf`
- `nvidia_neural_network_benchmarks.py`
- `hollywood_movie_festival.mkv`

Instead of manually dragging every file into folders, our **Machine Learning prediction model reads the name of the file or folder, understands what it's about, and automatically predicts its major category**:
1. 📂 **Business**
2. 📂 **Tech**
3. 📂 **Politics**
4. 📂 **Sports**
5. 📂 **Entertainment**

---

## 📚 2. The Training Dataset (BBC News Corpus)

*(Notebook Reference: Cells 5 – 8)*

To teach a machine to classify text, it needs examples. We used the **BBC News Dataset**, which contains **2,225 real news articles** categorized across five domains:

| Category | Number of Articles | Typical Vocabulary |
| :--- | :---: | :--- |
| **Sports** | 511 | *football, league, goal, match, player, championship, cup, coach* |
| **Business** | 510 | *shares, market, profit, economy, growth, bank, inflation, revenue* |
| **Politics** | 417 | *election, government, minister, parliament, party, council, vote* |
| **Tech** | 401 | *software, computer, mobile, broadband, virus, technology, hardware* |
| **Entertainment** | 386 | *film, music, actor, star, awards, album, band, show, hollywood* |

In the notebook, the dataset is loaded from [`Dataset/bbc`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/Dataset/bbc).

---

## 🧹 3. Step-by-Step ML Pipeline: How It Works

### Step 3.1: Filename Cleaning (`clean_filename`)
*(Notebook Reference: Cell 28)*

Files on computers have punctuation, extensions, and camelCase formatting that standard text models struggle with. We created a dedicated cleaning function:

```
"Tesla_Quarterly_Financial_Report_Q3_2024.xlsx"
           ↓ (Step A: Strip extension .xlsx)
"Tesla_Quarterly_Financial_Report_Q3_2024"
           ↓ (Step B: Split camelCase words)
"Tesla Quarterly Financial Report Q3 2024"
           ↓ (Step C: Replace symbols & numbers with spaces)
"tesla quarterly financial report q"
```

Now the machine has pure words it can understand.

---

### Step 3.2: Turning Words into Numbers (TF-IDF Vectorization)
*(Notebook Reference: Cell 29)*

Computers cannot understand words directly; they only understand numbers. We use **TF-IDF (Term Frequency - Inverse Document Frequency)**:
- **Term Frequency (TF)**: How often a word appears in this specific document.
- **Inverse Document Frequency (IDF)**: How unique or rare the word is across all 2,225 articles.
  - Words like *"the"*, *"is"*, *"and"* appear everywhere $\rightarrow$ Given near **zero weight**.
  - Words like *"parliament"*, *"touchdown"*, *"dividend"* appear only in specific topics $\rightarrow$ Given **high weight**.
- **N-Grams `(1, 2)`**: The model learns both single words (*"league"*) and pairs of words (*"premier league"*, *"stock market"*, *"artificial intelligence"*).

---

### Step 3.3: The Classifier: Multinomial Naive Bayes
*(Notebook Reference: Cell 29)*

**Naive Bayes** is a probabilistic algorithm based on **Bayes' Theorem**:

$$\text{Probability}(\text{Category} \mid \text{Keywords}) \propto \text{Prior}(\text{Category}) \times \prod \text{Likelihood}(\text{Keyword} \mid \text{Category})$$

#### In Plain English:
1. **Prior Probability**: Before reading any text, how common is each folder? (roughly 20% each).
2. **Word Evidence**: When the model sees the word *"football"*, its internal score for `Sports` skyrockets, while `Politics` drops.
3. **Winner Takes All**: The category with the highest cumulative probability becomes the final prediction.

---

## 💡 4. The Secret Sauce: Short Text Adaptation for File & Folder Names

*(Notebook Reference: Cell 29)*

A standard news classifier trained only on 500-word articles struggles when given a short 3-word filename like `cricket_match_schedule.pdf`.

### How We Solved It:
In Cell 29 of the notebook, we augmented the training dataset:
- We extracted the **first line (the headline/title)** of every article in the BBC dataset (e.g. *"Ad sales boost Time Warner profit"*).
- We trained the model on **both full article bodies AND the headlines**.
- Headlines are short, dense, and punchy—**just like file and folder names**!
- As a result, the model achieved **100% accuracy** on sample filenames across all five major categories.

---

## 📊 5. Model Evaluation & Results

*(Notebook Reference: Cells 29 – 30)*

When evaluated on an unseen 20% test split:
- **Overall Accuracy**: **98.20%**
- **Sports Precision/Recall**: **99% / 99%**
- **Politics Precision/Recall**: **97% / 98%**
- **Tech Precision/Recall**: **97% / 96%**
- **Business Precision/Recall**: **98% / 98%**
- **Entertainment Precision/Recall**: **99% / 99%**

---

## 💾 6. Exporting to PKL and Loading in Python

*(Notebook Reference: Cells 34 – 36)*

To use the model inside the Digital Junk Drawer application without re-running the notebook, we exported it into a **`.pkl` (pickle) file**:

| File | Size | Format | Usage |
| :--- | :---: | :--- | :--- |
| [`file_classifier_model.pkl`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/file_classifier_model.pkl) | 9.2 MB | Compressed `joblib` | Production model used by `ml_classifier.py` |
| [`model.pkl`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/model.pkl) | 40.8 MB | Standard `pickle` | Universal fallback model |
| [`model_metadata.json`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/model_metadata.json) | < 1 KB | JSON | Configuration & class mappings |

### How It Connects to the Project:
In [`ml_classifier.py`](file:///c:/Users/Lenovo/Desktop/DSA%20Project/ml_classifier.py), the `MLClassifier` class loads `file_classifier_model.pkl`:

```python
from ml_classifier import MLClassifier

classifier = MLClassifier()
category, confidence = classifier.predict("champions_league_final.mp4")
print(f"Folder: {category} ({confidence}%)")
# Output: Folder: Sports (98.4%)
```

This prediction is then directly fed into the **FolderTree** and stored in the **Custom HashMap**!
