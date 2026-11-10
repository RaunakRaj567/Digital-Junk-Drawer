# 🎤 Pitch Script: Digital Junk Drawer

> **Format:** about 12–15 minutes of talk + live demo, then Q&A.
> **What you need:** laptop with the web app running (`python app.py`), a projector, and the 11 files in `sample_unorganized_files/`.
> Lines in *italics* are stage directions. Lines in "quotes" are what you say. Change the wording to suit you, but keep the structure.

---

## ✅ Before you walk in (do this the day before)

- [ ] **Fix the model `.pkl` first.** As shipped, the app quietly uses its keyword fallback (every confidence shows exactly 85% or 50%, and `Drama_serial.txt` goes to Business). Re-run the notebook's training + export cells with the same Python the app uses. See [README_ML.md §8](README_ML.md). Then check: arranging the inbox should give confidences like 84.3%, 90.6%, not 85.0%.
- [ ] Run `python -m unittest test_dsa.py`; it should end with `Ran 24 tests ... OK`. Keep that terminal open; you'll show it.
- [ ] Start `python app.py` and do one full run: arrange → unlock vault → search → sort → tree. Then **re-copy the 11 files into the inbox** so the demo starts fresh.
- [ ] Have `README_DSA.md` open in a tab as backup slides, and keep a screen recording of the demo in case the projector or laptop misbehaves.
- [ ] Memorise the vault password. Don't put it on a slide.

---

## ⏱️ Timeline at a glance

| # | Section | Time | Goal |
| :---: | :--- | :---: | :--- |
| 1 | Opening: the "Guess the Folder" game | 2:00 | Wake the room up, get them participating |
| 2 | The problem + one-line pitch | 1:00 | Everyone knows why this exists |
| 3 | Architecture in one picture | 1:00 | Big picture before details |
| 4 | Live demo | 3:30 | Show it working |
| 5 | DSA deep-dive (HashMap → Tree → Merge Sort) | 4:00 | **This is where the marks are** |
| 6 | ML deep-dive | 2:00 | Show the model is real, measured, understood |
| 7 | Security vault | 0:45 | Shows range beyond the syllabus |
| 8 | Testing, honest limits, future work | 1:00 | Signals maturity |
| 9 | Closing callback | 0:30 | End on a memorable line |

---

## 1️⃣ Opening: "Guess the Folder" (2 min)

*Walk to the centre. Don't touch the laptop yet. Start with a question, not "Good morning, our project is…".*

> "Quick show of hands. Keep your hand up if your Downloads folder has more than **50** files in it."
>
> *(most hands go up)*
>
> "More than **200**?"
>
> *(fewer hands, some laughter)*
>
> "Keep it up if you have a file called something like **`final_FINAL_v2_really_final.pdf`**."
>
> *(laughter; you've got the room)*
>
> "Right. That's the problem we solved. But first, a game."

*Put this slide up. Four real filenames from the project's inbox:*

```
   1.  Runs_Cricket.txt
   2.  EVM_vote_hack.txt
   3.  Drama_serial.txt
   4.  Operating System.txt

   Folders:  Business · Tech · Politics · Sports · Entertainment
```

> "These are four messy files. You have **five folders**. Shout out where each one goes. Number one?"
>
> *(class: "Sports!")* "Easy. Number two, **EVM vote hack**?" *(class: "Politics!")*
>
> "Number three, **Drama serial**?" *(class: "Entertainment!")*
>
> "And number four, **Operating System**?" *(class: "Tech!")*
>
> "You got all four. It took this room about fifteen seconds, and you're thirty-odd humans with a lot of world knowledge.
>
> **Our program does the same thing, for a whole folder, in under a second. It has never read a filename in its life. It learned from 2,225 BBC news articles.**
>
> And once it has sorted them, it stores them in three data structures we wrote from scratch: no Python `dict`, no `sorted()`. Let me show you."

> 💡 **Why this works:** the audience commits to answers, so they're invested in whether the machine agrees with them. Tricky cases like *Drama serial* and *Operating System* are also exactly what the ML handles and the naive keyword fallback doesn't, which you can mention later.

---

## 2️⃣ The Problem & One-Line Pitch (1 min)

> "Everyone has a digital junk drawer: Downloads, Desktop, WhatsApp documents. Sorting it by hand is boring, so nobody does it, and then you can't find anything.
>
> **Digital Junk Drawer** is an organizer that:
> 1. **reads the filename** and predicts its topic with Machine Learning,
> 2. **moves it into the right folder** on disk,
> 3. **indexes it** in a custom HashMap and a folder Tree so you can find, move, search and sort instantly,
> 4. and **locks** the organized folders behind a SHA-256 password vault.
>
> It's a DSA project at its core, with ML deciding *where* things go and data structures making it fast to *find* them again."

---

## 3️⃣ Architecture in One Picture (1 min)

*Slide:*

```
  Inbox file ──▶ clean name ──▶ ML (TF-IDF + Naive Bayes) ──▶ "Sports", 90.6%
                                                                 │
                                                       DocumentManager
                                                  copies file to sports/
                                    ┌───────────────────┼───────────────────┐
                                    ▼                   ▼                   ▼
                             Custom HashMap       Folder Tree          Merge Sort
                           DOC_1011 → file     Root→Sports→file    name/size/date
                              O(1) lookup       move / list / draw   O(N log N), stable
                                    ▲
                          Desktop GUI (Tkinter)  +  Web App (Flask)  ──▶ 🔐 SHA-256 vault
```

> "One controller, the `DocumentManager`, is the only thing allowed to write to the structures, so the HashMap and the Tree can never disagree. Each structure answers a different question: the **HashMap** answers *'give me document 1011'*, the **Tree** answers *'what's in Sports?'*, and **Merge Sort** answers *'show me the biggest files first'*."

---

## 4️⃣ Live Demo (3.5 min)

*Switch to the browser at http://127.0.0.1:5000. Narrate what you click.*

| Step | Do | Say |
| :---: | :--- | :--- |
| 1 | Show **Page 1: Inbox** with 11 files | "Here's the junk drawer: 11 files, no order." |
| 2 | **Drag-and-drop** one extra file. *Ask a classmate to name it*, e.g. `ipl_auction_virat.txt` or `budget_gst_debate.pdf` | "Let's take one from the audience. Give me a filename." *(See the safety note below.)* |
| 3 | Click **⚡ Arrange into Organised Folders** | "Now the ML reads every name and the files physically move. Watch the confidence column: that's the model's probability, not a hard-coded number." |
| 4 | Click **View Organised Folders**, and the **vault** pops up. Type a wrong password first | "The output is locked. Wrong password: the app hashes what I typed with SHA-256 and compares it to the stored hash. It **never stores the actual password**." |
| 5 | Type the correct password | "Digests match, so access is granted." |
| 6 | Click the **Sports** folder card | "Folder contents come from the **Tree**. Note the hash-code: this is the bucket index from our own hash function." |
| 7 | Type `.txt` or `cricket` into **search**, scope = All Folders | "Global search across every folder." |
| 8 | **Sort** by File Size, Descending | "That's our recursive **Merge Sort** running on the backend." |
| 9 | Open **🌳 Visualise Folder Tree** | "And here's the Tree itself, drawn by a depth-first traversal." |
| 10 | Point at **HashMap diagnostics** pills | "Live internals: 11 items, capacity 16, load factor 0.69. The 12th file would make it 12/16 = **0.75**, so the table **doubles to 32** and every hash-code changes because everything gets rehashed." *(If the audience file from step 2 made it 12 items, the capacity already shows **32**. Point that out: it just happened live.)* |

> ⚠️ **Audience-filename safety note:** the model was trained on 2004–05 *British* news. Cricket, football, elections, budgets, films and software all work well. Very new or very Indian terms (*IPL, Kohli, ChatGPT*) may get low confidence or the wrong folder. If that happens, **turn it into a point**: "Good catch. That word didn't exist in the training data. That's called *domain shift*, and it's in our future work." Professors like hearing that.

---

## 5️⃣ DSA Deep-Dive (4 min) ⭐ the most important section

### 5a. Custom HashMap (≈ 2 min)

*Slide: the hash function + a chain diagram.*

```python
h = 0
for ch in key:
    h = (h * 31 + ord(ch)) % capacity     # polynomial rolling hash, Horner's method
```
```
bucket[7] → [DOC_1001 | doc] → [DOC_1042 | doc] → None      ← separate chaining
```

> "Three design decisions:
>
> **One, the hash function.** A polynomial rolling hash with base 31, an odd prime, the same constant Java uses for `String.hashCode`. We take the mod at every step so numbers stay small.
>
> **Two, collisions.** Two IDs can land in the same bucket. We use **separate chaining**: each bucket is a linked list, and new keys go in at the head in O(1).
>
> **Three, resizing.** We track the **load factor**, size over capacity. When it hits **0.75**, we **double** the array and **rehash** every key. Resizing is O(N), but because we double, it happens rarely enough that insert stays **amortized O(1)**."

*Slide: the benchmark. Real numbers from this code, 100,000 IDs:*

| | Time per operation |
| :--- | :---: |
| HashMap lookup | **≈ 1.2 µs** |
| Linear scan of a list (`list.index`, written in C) | **≈ 654 µs** |
| Max chain length after 100k inserts | **5** |

> "Our HashMap is **pure Python** and still about **500 times faster** than a linear scan that runs in C. And after 100,000 inserts the longest chain is 5, which tells you the hash function spreads keys well and the worst case, O(N), doesn't show up in practice."

### 5b. Folder Tree (≈ 1 min)

> "Folders are a hierarchy, so we used an **N-ary tree**: a root, five category nodes, and documents as leaves. Every node has a **parent pointer**. That's what makes *move* work: find the node with **DFS**, unlink it from the old parent, link it to the new one, and update the document's category, which the HashMap sees immediately because both hold the same object.
>
> Finding a file *inside* the tree is O(N), but we almost never need to, because the HashMap already gives us O(1) by ID. **Each structure does what it's best at.**"

### 5c. Merge Sort (≈ 1 min)

```python
if left_val <= right_val:     # '<=' not '<', and that one character makes it STABLE
    merged.append(left[i])
```

> "Why Merge Sort and not QuickSort? Two reasons.
>
> **Guaranteed O(N log N).** QuickSort can drop to O(N²) on already-sorted input, and file lists are often already partly sorted.
>
> **Stability.** If two files have the same size, they keep their previous order. The whole guarantee is in that **less-than-or-equal sign**: on a tie we always take from the left half. For descending order we flip the comparison *inside* the merge instead of reversing the output, because reversing would break stability.
>
> Recurrence: T(N) = 2T(N/2) + O(N), which gives O(N log N) in best, average and worst case, with O(N) extra space."

---

## 6️⃣ ML Deep-Dive (2 min)

*Slide: the pipeline.*

```
"QuarterlyEarningsReport_Q3_2024.xlsx"
   → clean  → "quarterly earnings report q"
   → TF-IDF (unigrams + bigrams, stop-words removed, sublinear TF)
   → Multinomial Naive Bayes (alpha = 0.05)
   → "business", 88.18%
```

> "**Data:** 2,225 BBC news articles in our exact five categories.
>
> **We didn't just pick a model, we compared options.** Plain counts, stop-word removal, lemmatization, stemming. Removing stop-words won at 97.67%. Lemmatization and stemming actually made it *worse* and slower, so we dropped them.
>
> **TF-IDF** gives rare, topical words like *parliament* high weight and common words like *said* low weight. Bigrams let it learn phrases like *'prime minister'* or *'world cup'*.
>
> **Naive Bayes** applies Bayes' theorem: prior times the product of word likelihoods, and pick the highest. It's fast, it handles sparse text well, and it gives a probability, which is our confidence score.
>
> **The trick that made it work on filenames:** a model trained on 400-word articles has never seen a 3-word input. So we **also trained on every article's headline**. Headlines are short and punchy, like filenames. That doubled the training set to 4,450 examples.
>
> **Results:** **97.08%** accuracy on a held-out test set, and **15 out of 15** on a filename test battery. Sports precision is 1.00."

*Optional honesty slide, which earns credibility:*

> "Where it struggles: `NBA_playoffs_lakers` is correct but only 43% confident, because *NBA* barely appears in British news from 2005. Data matters as much as the algorithm."

---

## 7️⃣ Security Vault (45 sec)

> "One more piece. The organized folders are protected. We store only the **SHA-256 hash** of the password. On login we hash the input and compare using `hmac.compare_digest`, a **constant-time** comparison, so an attacker can't time the response to work out how many characters were right.
>
> Fun connection to the syllabus: our HashMap uses a **fast** hash where collisions are *expected* and handled. The vault uses a **cryptographic** hash where collisions are *practically impossible*. Same concept, opposite goals."

---

## 8️⃣ Testing, Honest Limits, Future Work (1 min)

*Show the terminal with `Ran 24 tests ... OK`.*

> "We have **24 automated tests**: forced collisions with capacity 1, resize and rehash, tree move and delete, sort stability, empty lists, and integration tests that check the HashMap and Tree stay in sync after moves and deletes."

> "What we'd improve next:
> - store a pointer from the HashMap to the tree node, to make tree lookups O(1) too,
> - add an *Uncategorized* folder when the model's confidence is low,
> - retrain on recent and Indian news so *IPL* and *GST* are understood,
> - and learn from users: every time someone moves a file, that's a free training label."

---

## 9️⃣ Closing (30 sec)

*Go back to the opening slide with the four filenames.*

> "Remember the game? It took this room about fifteen seconds to sort four files.
>
> Our program sorts an entire folder in under a second, finds any file in about a microsecond, sorts thousands of files in guaranteed N-log-N time, and keeps it all behind a SHA-256 lock.
>
> **Your Downloads folder doesn't need more discipline. It needs better data structures.**
>
> Thank you. Happy to take questions."

---

## 🎯 Q&A Prep: likely professor questions

| Question | Strong answer |
| :--- | :--- |
| **Why not just use Python's `dict`?** | "The goal was to implement and understand hashing ourselves: hash function, chaining, load factor, rehashing. Python's `dict` uses open addressing; we chose separate chaining because deletion is simpler and the table degrades gracefully at high load." |
| **What's the worst case of your HashMap?** | "O(N), if every key hashes to one bucket. Base-31 hashing plus doubling at α = 0.75 makes that unlikely; at 100k keys our longest chain was 5." |
| **Why load factor 0.75?** | "It's the standard trade-off (Java's HashMap uses it too). Lower wastes memory; higher makes chains longer. With chaining the expected chain length is about α, so under 1." |
| **Prove insert is amortized O(1).** | "With doubling, the total rehash work over N inserts is N + N/2 + N/4 + … < 2N. Spread over N inserts, that's a constant per insert." |
| **Why 31?** | "It's an odd prime: multiplying by it spreads bits without losing information the way an even number would, and 31·x = (x << 5) − x is cheap to compute." |
| **Why does a hash-code change after resize?** | "The bucket index is `hash mod capacity`. When capacity doubles, the mod changes, so every key gets rehashed into the new array. You can see it happen live in the UI." |
| **Is your Merge Sort in-place?** | "No. It uses O(N) auxiliary space and returns a new list, which is also why sorting never disturbs the HashMap or Tree." |
| **Why not QuickSort or Heap Sort?** | "QuickSort has an O(N²) worst case and isn't stable; Heap Sort is O(N log N) but not stable. Merge Sort is the only one of the three that is both guaranteed O(N log N) and stable." |
| **Tree lookups are O(N); isn't that slow?** | "Only for finding a file by ID inside the tree, and we route those through the HashMap instead. Category lookups are O(C) with C = 5. A next step is storing a node pointer in the HashMap to make tree moves O(1)." |
| **What does 'naive' mean in Naive Bayes?** | "It assumes words are independent given the category. That's false (*'prime'* and *'minister'* are clearly related), but it works well for text classification, and bigrams recover some of the word-pair information." |
| **What is alpha = 0.05?** | "Lidstone smoothing. It stops an unseen word from giving zero probability. We kept it small so it doesn't drown out the few words in a short filename." |
| **How do you know you're not overfitting?** | "97.08% is on a held-out 20% split the model never saw. The headline augmentation is only added for the final production model, after evaluation." |
| **What if a filename means nothing, like `IMG_0042.jpg`?** | "After cleaning it becomes almost nothing, so the model has no signal and confidence is low. Future work: an *Uncategorized* folder below a confidence threshold, or reading the file's contents." |
| **Is SHA-256 enough for passwords?** | "For a demo, yes. In production we'd add a per-user **salt** and use a deliberately slow KDF like bcrypt or PBKDF2 to resist brute force, and keep the secret out of the source code." |
| **What was the hardest part?** | *Pick a true one*, e.g. "Keeping the HashMap, Tree and the real files on disk in sync when a user deletes a file in Explorer. That's why we wrote `sync_with_disk()`, which prunes and re-discovers before every listing." |
| **Who did what?** | *Have a clear, honest one-line split ready for each team member.* |

---

## 🧠 Delivery tips

- **Speak to the professor during section 5.** That's where the marks are; the opener is for the class.
- **Say the complexities out loud** ("O of one, amortized"). It shows fluency.
- **If the demo breaks, don't apologise for long.** Say "this is why we have 24 tests", switch to the screen recording, and carry on.
- **Point at the screen** when you mention load factor, hash-code or confidence, so people see the number you're talking about.
- **End on time.** Finishing 30 seconds early is much better than running over.
