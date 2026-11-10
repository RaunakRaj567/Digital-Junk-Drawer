# 🤖 Digital Junk Drawer: Machine Learning Guide

This guide explains how Digital Junk Drawer **reads a filename and decides which folder it belongs in**. Every number here comes from the outputs saved in the training notebook [text-classification-using-naive-bayes.ipynb](text-classification-using-naive-bayes.ipynb) or from running the project's code.

> 📘 The data structures that store the classified files (HashMap, Folder Tree, Merge Sort, SHA-256 vault) are documented in [README_DSA.md](README_DSA.md).

---

## 🌟 1. The Problem

A Downloads folder full of files like these:
```
Runs_Cricket.txt      Stock_2026.txt      Party clash.txt
Software_malware.txt  Movie_rating.txt    EVM_vote_hack.txt
```
The model reads **only the name** (not the file contents) and predicts one of five folders:

📂 **Business** · 📂 **Tech** · 📂 **Politics** · 📂 **Sports** · 📂 **Entertainment**

Using only the name means it works on any file type (`.mp4`, `.zip`, `.xlsx`, a whole sub-folder) without opening it, and it is very fast.

---

## 📚 2. Training Data: BBC News Corpus

*(Notebook: "Loading Data")*

**2,225 real BBC news articles** (2004–2005) in five labelled folders, stored in [Dataset/bbc/](Dataset/bbc). The folder `sport` is renamed to `sports` during loading.

| Category | Articles | Typical words |
| :--- | :---: | :--- |
| Sports | 511 | football, league, match, cup, coach |
| Business | 510 | shares, market, profit, economy, bank |
| Politics | 417 | election, government, minister, party, vote |
| Tech | 401 | software, computer, mobile, broadband, virus |
| Entertainment | 386 | film, music, actor, awards, album |

The classes are roughly balanced (17%–23% each), so plain accuracy is a fair metric.

For every article, the loader also keeps its **first line, the headline** (e.g. *"Ad sales boost Time Warner profit"*). This becomes important in §5.

---

## 🔬 3. Baseline Experiments: Choosing the Text Pipeline

*(Notebook: "Training and Evaluating Model" → "With Simple Tokenizer")*

Before building the final model, the notebook compares preprocessing choices with a word-count (`CountVectorizer`) + `MultinomialNB` baseline. Split: 75% train (1,668 articles) / 25% test (557 articles), `random_state=123`.

| Variant | Vocabulary size | Train acc. | **Test acc.** |
| :--- | :---: | :---: | :---: |
| Plain word counts | 26,287 | 99.22% | 97.13% |
| **+ English stop-words removed** | 25,995 | 99.28% | **97.67%** ✅ best |
| + Lemmatization (WordNet + POS tags) | 25,894 | 99.22% | 96.77% |
| + Porter stemming | 22,714 | 98.92% | 96.95% |
| Whitespace-split tokenizer | 52,144 | 99.52% | 97.13% |

**Takeaways**
- Removing stop-words (*the, is, and…*) helped the most, so the final model keeps it.
- Lemmatization and stemming **slightly hurt** and are slow, so they were dropped.
- Only 0.77% of the document-term matrix is non-zero, so the data is very **sparse**, which suits Naive Bayes well.

---

## 🧹 4. The Final Pipeline

*(Notebook: "Meeting Future Demand: File & Folder Name Classification")*

### Step 4.1: Filename cleaning, `clean_filename` (also `clean_filename_for_ml` in [ml_classifier.py](ml_classifier.py))
```
"QuarterlyEarningsReport_Q3_2024.xlsx"
   │ strip path + extension
   ▼ "QuarterlyEarningsReport_Q3_2024"
   │ split camelCase / PascalCase  (regex ([a-z0-9])([A-Z]) → "\1 \2")
   ▼ "Quarterly Earnings Report_Q3_2024"
   │ replace everything that isn't a letter with a space
   ▼ "Quarterly Earnings Report Q"
   │ lowercase + collapse spaces
   ▼ "quarterly earnings report q"
```
Real notebook output:

| Input | Cleaned |
| :--- | :--- |
| `premier_league_football_final_highlights.mp4` | `premier league football final highlights` |
| `PresidentialElectionVotingResults.pdf` | `presidential election voting results` |
| `new-artificial-intelligence-gpu-architecture.docx` | `new artificial intelligence gpu architecture` |
| `CyberSecurityMalwareAttackDefense` | `cyber security malware attack defense` |

### Step 4.2: TF-IDF vectorization
Text becomes numbers using **Term Frequency × Inverse Document Frequency**:

$$\text{tfidf}(t, d) = \underbrace{(1 + \log \text{tf}_{t,d})}_{\text{sublinear TF}} \times \underbrace{\log\frac{1 + N}{1 + \text{df}_t} + 1}_{\text{IDF}}$$

- **TF**: how often the word appears in this text. `sublinear_tf=True` uses a log, so a word repeated 20 times isn't scored 20× higher.
- **IDF**: how rare the word is across all articles. *"said"* is everywhere, so it gets low weight; *"parliament"* is rare and topical, so it gets high weight.
- **`ngram_range=(1, 2)`**: learns single words **and** word pairs, so *"stock market"*, *"prime minister"* and *"world cup"* are features of their own.
- **`stop_words='english'`**: removes filler words (the winner from §3).

### Step 4.3: Multinomial Naive Bayes, `MultinomialNB(alpha=0.05)`
**Bayes' theorem** with the "naive" assumption that words are independent given the category:

$$P(\text{cat} \mid w_1 \dots w_n) \;\propto\; P(\text{cat}) \times \prod_{i=1}^{n} P(w_i \mid \text{cat})$$

In plain English:
1. **Prior** $P(\text{cat})$: how common each category is (about 20% each).
2. **Likelihood** $P(w \mid \text{cat})$: how typical the word is for that category. *"cricket"* is far more likely in Sports than in Politics.
3. Multiply (in practice, add logs) and **pick the largest**. `predict_proba` turns the scores into the **confidence %** shown in the app.

**Laplace / Lidstone smoothing (`alpha`)**: a word never seen in a category would give probability 0 and wipe out the whole product. `alpha` adds a small pseudo-count to every word. The notebook uses `alpha = 0.05` (the default is 1.0) so that the few, very informative words in a short filename aren't drowned out by smoothing.

**Why Naive Bayes rather than a neural network?** It trains in seconds on 2k documents, works well on sparse high-dimensional text, gives probabilities, and is easy to explain.

Both steps are wrapped in one scikit-learn `Pipeline([('tfidf', ...), ('clf', ...)])`, so cleaning → vectorizing → predicting is a single `.predict()` call.

---

## 💡 5. The Key Trick: Training on Headlines for Short Text

A model trained only on 400-word articles has never seen a 2–3 word input like `runs cricket`. Headlines, though, are short and dense, much like filenames.

So the **final production model** is trained on an **augmented dataset**:
```python
X_augmented = list(df['text']) + list(df['title'])    # 2,225 articles + 2,225 headlines
y_augmented = list(df['labels']) + list(df['labels']) # = 4,450 training examples
```
The model learns both long-form vocabulary and the short headline style.

---

## 📊 6. Evaluation

### 6.1 Held-out test set (articles)
*(Notebook cell after "Meeting Future Demand", 80/20 split, `random_state=42`, 445 test articles)*

**Test accuracy: 97.08%**

| Category | Precision | Recall | F1 | Support |
| :--- | :---: | :---: | :---: | :---: |
| Business | 0.98 | 0.96 | 0.97 | 115 |
| Entertainment | 0.99 | 0.94 | 0.96 | 72 |
| Politics | 0.93 | 0.99 | 0.96 | 76 |
| Sports | **1.00** | 0.99 | **1.00** | 102 |
| Tech | 0.95 | 0.97 | 0.96 | 80 |
| **Macro avg** | 0.97 | 0.97 | 0.97 | 445 |

- **Precision**: of the files put in a folder, how many belonged there.
- **Recall**: of the files that belong in a folder, how many ended up there.
- Sports is nearly perfect because its vocabulary is very distinctive. Politics has the lowest precision (0.93): some business/economy articles get pulled into Politics, since budgets and taxes are discussed in both.

> This 97.08% is measured **before** headline augmentation, on a clean split, so no test article leaked into training. The production model is then retrained on all 4,450 examples.

### 6.2 Filename test battery
*(Notebook: `predict_category` test cell)*. **15 / 15 correct (100%)**:

| Filename | Predicted | Confidence |
| :--- | :--- | :---: |
| `oscar_award_nominations_hollywood.txt` | entertainment | 99.45% |
| `cricket_world_cup_match_schedule` | sports | 99.13% |
| `apple_iphone_ios_software_update.zip` | tech | 99.03% |
| `labour_party_tax_budget_debate` | politics | 99.00% |
| `stock_market_inflation_and_interest_rates.csv` | business | 98.95% |
| `premier_league_football_final_highlights.mp4` | sports | 93.74% |
| `QuarterlyEarningsReport_Q3_2024.xlsx` | business | 88.18% |
| `cybersecurity_malware_ransomware_attack.log` | tech | **48.45%** |
| `new_artificial_intelligence_gpu_architecture.docx` | tech | **44.25%** |
| `NBA_playoffs_lakers_vs_warriors` | sports | **43.24%** |

*(10 of 15 shown.)* The low-confidence rows are worth discussing: words like *GPU*, *ransomware*, *NBA* and *Lakers* barely appear in **2004–2005 British** news, so the model is still right but unsure. That is a **dataset / domain-shift** limit, not a bug.

### 6.3 Folder organization demo
The notebook also creates 10 files + 5 sub-folders and auto-organizes them: **15 / 15 placed correctly**, including folders such as `senate_foreign_policy_debate/` → politics and `stock_market_investing_portfolio/` → business.

---

## 💾 7. Export & Integration

*(Notebook: "Exporting the Model to PKL File")*

| File | Size | Format | Used by |
| :--- | :---: | :--- | :--- |
| [file_classifier_model.pkl](file_classifier_model.pkl) | 8.77 MB | `joblib`, compressed (`compress=3`) | `MLClassifier` (tried first) |
| [model.pkl](model.pkl) | 38.90 MB | plain `pickle` | fallback |
| [model_metadata.json](model_metadata.json) | < 1 KB | JSON | classes + pipeline description |

The `.pkl` stores the **whole Pipeline** (fitted TF-IDF vocabulary with IDF weights + Naive Bayes probabilities), so the app needs no retraining.

```python
from ml_classifier import MLClassifier

clf = MLClassifier()                         # loads file_classifier_model.pkl
clf.predict("cristiano_ronaldo_fifa_world_cup_goals.mp4")
# → ('Sports', 99.25)    # notebook's verification cell
```

**Inside `MLClassifier.predict()`:**
1. Clean the name with `clean_filename_for_ml`.
2. `model.predict` + `model.predict_proba` → label + max probability as confidence.
3. Map labels to titles (`sports` → `Sports`; it also accepts the misspelling `buisness`).
4. **Safety net:** if the model is missing or throws, use `_heuristic_predict`, a keyword-voting fallback (≈14 keywords per category) that returns **85%** on a keyword hit and **Business / 50%** otherwise. The app keeps working with no model file.

The predicted category goes straight to `DocumentManager.upload_document()`, which stores the file in the **HashMap** and the **Folder Tree**.

---

## ⚠️ 8. Known Issue: Model Version Mismatch (fix before demoing)

The bundled `.pkl` files were exported from a newer scikit-learn than the one in the project's runtime (**Python 3.8 + scikit-learn 1.3.2**). Loading works, but prediction fails with:
```
sklearn.exceptions.NotFittedError: idf vector is not fitted
```
`MLClassifier` catches this and **silently uses the keyword fallback**. The giveaway is that every confidence in the app is exactly **85.0%** or **50.0%**.

Effect on the 11 files in `sample_unorganized_files/`:

| File | Keyword fallback (current) | Real model (retrained in this env) |
| :--- | :--- | :--- |
| Drama_serial.txt | Business 50% ❌ | **Entertainment 84.3%** ✅ |
| Operating System.txt | Business 50% ❌ | **Tech 44.1%** ✅ |
| Fundraise_society.txt | Business 50% | Politics 40.2% (debatable) |
| EVM_vote_hack.txt | Politics 85% | Politics 36.7% |
| Movie_rating.txt | Entertainment 85% | Entertainment 66.6% |
| Olympics_Hockey.txt | Sports 85% | Sports 67.5% |
| Party clash.txt | Politics 85% | Politics 75.2% |
| Runs_Cricket.txt | Sports 85% | Sports 48.3% |
| Software_malware.txt | Tech 85% | Tech 81.2% |
| Stock_2026.txt | Business 85% | Business 88.1% |
| football fixture.txt | Sports 85% | Sports 90.6% |

Retraining with the exact notebook pipeline in this environment reproduces **97.08%** test accuracy.

**Fix:** open the notebook with the **same Python interpreter that runs the app** (the one where `python -c "import sklearn; print(sklearn.__version__)"` prints the version the app uses), then re-run the loading cell, the training cell and the export cell. That rewrites both `.pkl` files in a compatible format. Pinning versions in a `requirements.txt` stops it from recurring.

---

## 🔭 9. Limitations & Future Work

- **Five fixed classes.** A file about cooking or health is still forced into one of the five (low confidence is the hint). Future: an *"Uncategorized"* folder when confidence < ~40%.
- **Domain shift.** 2004–05 UK news lacks modern terms (*ChatGPT, IPL, EVM, GST*). Future: add recent or Indian news headlines.
- **Name only.** `final_v2.pdf` carries no topic signal. Future: read the first page of text/PDF files when the name is ambiguous.
- **Learning from corrections.** When a user moves a file in the app, that (filename, correct folder) pair could be logged and used to fine-tune the model.
