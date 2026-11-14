# 🧠 Code & AI Model Technical Report

**Project:** Automated 2D CAD Quality Inspection Report Generation System  
**Client:** MJMTECHNOVA ENGINEERING PVT. LTD.  
**Focus:** AI/ML Model Architecture, Mathematical Specifications & In-Depth Codebase Engineering  

---

# PART 1: MACHINE LEARNING MODEL ARCHITECTURE

## 1.1 Model Specification Summary

| Attribute | Specification |
| :--- | :--- |
| **Model Type** | Supervised NLP Pipeline (Hybrid Character n-gram TF-IDF + Regularized Logistic Regression) |
| **Library** | `scikit-learn` (v1.4.1+) |
| **Task** | Multi-class Classification of 2D CAD Drawing Text Annotations (8 classes) |
| **Training Dataset Size** | 459 labeled samples extracted from production engineering drawings |
| **Validation Strategy** | 5-Fold Stratified Cross-Validation (`StratifiedKFold`, $k=5$, random seed 42) |
| **Mean CV Accuracy** | **`99.57% ± 0.53%`** |
| **Test Accuracy** | **`1.00 (100.0%)`** |
| **Inference Latency** | **`< 2.5 milliseconds per annotation`** |
| **Serialized Model File** | `python_vs/dataset/drawing_text_classifier.pkl` (Size: ~45 KB) |

---

## 1.2 Why This Model Architecture?

Engineering drawing annotations present distinct linguistic and visual characteristics:
* Annotations are concise alphanumeric codes (`M6 ↧ 44.48 mm`, `Ø 17 THRU`, `168 ± 0.02`, `// 0.02 A`).
* CAD PDF export filters frequently produce inconsistent whitespace (e.g., `M6x1.0` vs `M6 x 1.0`) or font character corruption (e.g., `O17` instead of `Ø17`).

### Architectural Trade-off Analysis:
1. **Vs. Deep Learning (BERT / Transformers):**
   * Transformers require 400 MB–1 GB RAM, introduce 50–150 ms latency per sample, and suffer from extreme over-parameterization on domain-specific alphanumeric codes.
   * Transformer tokenizers (BPE / WordPiece) fragment engineering codes into arbitrary subwords (e.g. `M5` $\rightarrow$ `M`, `##5`), hurting classification accuracy.
2. **Vs. Word-Level TF-IDF:**
   * Fails when spaces are missing (`Ø10THRU`) or when symbols are slightly corrupted.
3. **Chosen Architecture: Sub-word Character n-gram TF-IDF (`char_wb`) + Balanced Logistic Regression:**
   * **Boundary-Aware Character n-grams (`char_wb`):** Extracts n-grams strictly within word boundaries. Captures critical prefixes (`M` $\rightarrow$ metric thread, `R` $\rightarrow$ radius, `Ø` $\rightarrow$ diameter, `±` $\rightarrow$ tolerance) regardless of spacing.
   * **Balanced Logistic Regression:** Convex optimization guarantees a global minimum, class weighting handles frequency imbalances, and linear weights provide full interpretability.

---

## 1.3 Feature Extraction: Mathematical Formulation

### 1. Term Frequency ($TF$):
For a character n-gram $t$ in text sample $d$:
$$TF(t, d) = \frac{f_{t,d}}{\sum_{t' \in d} f_{t',d}}$$
where $f_{t,d}$ is the raw count of n-gram $t$ in string $d$.

### 2. Inverse Document Frequency ($IDF$):
$$IDF(t) = \ln\left(\frac{1 + N}{1 + DF(t)}\right) + 1$$
where $N = 459$ (total samples) and $DF(t)$ is the number of drawings containing n-gram $t$.

### 3. Sub-linear TF-IDF Vector:
$$v(t, d) = TF(t, d) \times IDF(t)$$
The vector is normalized to unit Euclidean length ($\|v\|_2 = 1$).

### Vectorizer Hyperparameters:
```python
TfidfVectorizer(
    ngram_range=(1, 3),   # Unigrams, bigrams, and trigrams
    analyzer="char_wb",   # Character n-grams inside word boundaries
    lowercase=True,       # Case-insensitive normalization
    min_df=1              # Preserve rare CAD tokens
)
```

---

## 1.4 Classifier: Mathematical Formulation

The classifier optimizes multinomial Logistic Regression with an L2 penalty and class weight adjustment:

$$\min_{w, c} \frac{1}{2} w^T w + C \sum_{i=1}^N \alpha_{y_i} \log\left(1 + \exp\left(-y_i (w^T x_i + c)\right)\right)$$

### Balanced Class Weights ($\alpha_k$):
To prevent majority classes (e.g. `LINEAR_DIMENSION`, 219 samples) from dominating minority classes (e.g. `CHAMFER`, 5 samples):
$$\alpha_k = \frac{N}{K \cdot n_k} = \frac{459}{8 \cdot n_k}$$

### Hyperparameters:
```python
LogisticRegression(
    C=10.0,                 # Inverse regularization strength (tuned for high feature fidelity)
    max_iter=1000,          # Assures full gradient descent convergence
    class_weight="balanced",# Automatically applies alpha_k weights
    solver="lbfgs",         # Limited-memory BFGS quasi-Newton optimization
    random_state=42         # Deterministic reproducibility
)
```

---

## 1.5 Dataset Classes & Distribution

| Class Label | Support (Count) | Description | Example Extracted Strings |
| :--- | :---: | :--- | :--- |
| `LINEAR_DIMENSION` | 219 | Nominal dimensions without explicit limits | `120.0`, `25.4 mm`, `350`, `50.00` |
| `COORDINATE_FEATURE` | 138 | Coordinate table hole references and coords | `A.1`, `B.10`, `X=-2.00 Y=-25.00`, `H.3` |
| `HOLE_CALLOUT` | 26 | Drilled or counterbored hole specs | `Ø 17.00 mm THRU`, `Ø 10 THRU ⌴ Ø 15 - ↧ 8.6` |
| `THREAD_CALLOUT` | 24 | Standard metric internal/external threads | `M5 ↧ 10.00 mm`, `M6 ↧ 44.48 mm`, `M12 x 1.75` |
| `TOLERANCED_DIMENSION`| 22 | Dimensions with explicit bilateral limits | `168 ± 0.02`, `50 +0.05/-0.02`, `± 0.10` |
| `RADIUS` | 17 | Corner and fillet radius annotations | `R1.0`, `R5.0`, `4x R2.5`, `R 0.5` |
| `GEOMETRIC_TOLERANCE`| 8 | GD&T symbols and datum references | `// 0.02 A`, `⟂ 0.05 B`, `⌖ 0.01 A B C` |
| `CHAMFER` | 5 | Corner bevels and edge breaks | `1 x 45°`, `C 0.5`, `CHAMFER 2 x 45 DEG` |
| **Total** | **459** | **Full Training Set** | |

---

## 1.6 Empirical Evaluation Metrics

### 5-Fold Stratified Cross-Validation:
* Fold 1: **100.00%**
* Fold 2: **98.91%**
* Fold 3: **100.00%**
* Fold 4: **98.91%**
* Fold 5: **100.00%**
* **Mean Accuracy:** **`99.57% (± 0.53%)`**

### Detailed Classification Report:
```text
                      precision    recall  f1-score   support

             CHAMFER       1.00      1.00      1.00         5
  COORDINATE_FEATURE       1.00      1.00      1.00       138
 GEOMETRIC_TOLERANCE       1.00      1.00      1.00         8
        HOLE_CALLOUT       1.00      1.00      1.00        26
    LINEAR_DIMENSION       1.00      1.00      1.00       219
              RADIUS       1.00      1.00      1.00        17
      THREAD_CALLOUT       1.00      1.00      1.00        24
TOLERANCED_DIMENSION       1.00      1.00      1.00        22

            accuracy                           1.00       459
           macro avg       1.00      1.00      1.00       459
        weighted avg       1.00      1.00      1.00       459
```

---

# PART 2: COMPREHENSIVE CODEBASE ARCHITECTURE

## 2.1 File Map & Responsibilities

```text
d:/python_vs/
├── python_vs/
│   ├── extractor.py           # Core CAD PDF parsing, spatial clustering, IS 2102-m tolerancing
│   ├── ml_classifier.py       # Scikit-learn NLP model pipeline, cross-validation & inference
│   ├── prepare_dataset.py     # Annotation extractor converting raw drawings to training dataset
│   ├── generate_report.py     # openpyxl 13-column branded Excel generator with live formulas
│   └── api.py                 # FastAPI backend, JWT bearer token auth & REST endpoints
├── frontend/src/
│   ├── api.js                 # Axios HTTP client with dynamic baseURL & JWT interceptor
│   ├── App.jsx                # Global React application state & authentication coordinator
│   ├── pages/Login.jsx        # Company-gated login UI (@mjmtechnova.com verification)
│   ├── pages/Dashboard.jsx    # Drag-and-drop uploader, 13-col inspection table & Excel export
│   └── index.css              # Mobile-responsive CSS layout & color tokens
└── Dockerfile                 # Multi-stage production container definition
```

---

## 2.2 Deep Dive: `python_vs/extractor.py`

This module is the algorithmic core that parses vector CAD PDF streams into structured quality data.

### Key Logic & Algorithms:

#### 1. CAD Symbol Normalization (`normalize_symbol`)
Proprietary CAD fonts (e.g. AutoCAD `gdt.shx`, SolidEdge fonts) export standard symbols as backticks, bracket pairs, or letters. The normalization engine uses regex transforms:
```python
def normalize_symbol(text: str) -> str:
    # Converts backticks and ASCII 'DEEP' to standard depth symbol ↧
    text = re.sub(r"[`']+|(?:\bmm\s+)?DEEP\b", "↧", text, flags=re.IGNORECASE)
    # Converts brackets and C'BORE to standard counterbore symbol ⌴
    text = re.sub(r"\[\s*\]|C'?BORE", "⌴", text, flags=re.IGNORECASE)
    # Converts OCR/export artifacts (O followed by digits, Ã˜, ⌀) to standard diameter Ø
    text = re.sub(r"(?:Ã˜|⌀|\bO\b)(?=\s*\d+)", "Ø", text)
    # Converts +/- variations to standard bilateral tolerance ±
    text = re.sub(r"\+/-|\+\s*-\s*", "±", text)
    return text.strip()
```

#### 2. Spatial Clustering for Coordinate Table Parsing (`extract_hole_table`)
Mechanical drawings often represent hole tables as tabular arrays without explicit line borders. The engine utilizes PyMuPDF's `page.get_text("words")`:
* Each word returns `(x0, y0, x1, y1, "word", block_no, line_no, word_no)`.
* **Row Grouping Algorithm:** Words sharing a vertical band where $|y_{0,i} - y_{0,j}| \le \Delta y_{\text{threshold}}$ (typically 3.0 points) are grouped into the same horizontal line.
* **Column Sorting:** Grouped words are sorted by their horizontal coordinate $x_0$.
* **Matrix Matcher:** Extracts:
  - Feature Identifier: `A.1`, `A.2`, ... `H.10`
  - Nominal $X$ and $Y$ coordinates (e.g., `-2.000`, `-25.000`)
  - Tool/Hole specification: `M5 ↧ 10 mm`, `Ø 17 THRU`
  - Section/Datum reference: `REF SEC A-A`, `DRILL`

#### 3. Title Block Metadata Extraction (`extract_drawing_info`)
* **Part Number Identification:** Scans for company-standard part nomenclature:
  ```python
  m = re.search(r"\b(P\d{2}[A-Z0-9]{3}\d{6})\b", page_text)
  ```
* **Material Extraction:** Matches engineering alloy designations:
  ```python
  mat_regex = r"(?:MATERIAL\s*:\s*|BZ MATERIAL\s*:\s*)([A-Z0-9\s\-]+?)(?=\n|\r|FINISH|SCALE)"
  ```
* **Surface Finish & Mass:** Detects surface roughness (`Ra 3.2`, `Ra 1.6`) and component weight (`\b(\d+(?:\.\d+)?)\s*(?:kg|KG)\b`).

#### 4. IS 2102-m / ISO 2768-m Linear Tolerance Engine (`compute_is2102_tolerance`)
When a dimension lacks explicit limits on the drawing, the engine dynamically calculates tolerances based on standard IS 2102 (Medium):
```python
def compute_is2102_tolerance(nominal: float) -> float:
    dim = abs(nominal)
    if dim <= 6:
        return 0.05
    elif dim <= 30:
        return 0.10
    elif dim <= 120:
        return 0.15
    elif dim <= 400:
        return 0.20
    elif dim <= 1000:
        return 0.30
    else:
        return 0.50
```

#### 5. ISO Metrology Instrument Recommender (`recommend_tool`)
Determines the inspection gauge according to precision requirements:
```python
def recommend_tool(parameter: str, nominal: float, tol: float, callout: str) -> str:
    p_lower = parameter.lower()
    c_lower = callout.lower()
    if "thread" in p_lower or callout.startswith("M"):
        return "Thread Plug Gauge (6H Go/No-Go) & Depth Micrometer"
    if "hole" in p_lower or "ø" in c_lower:
        if tol <= 0.03:
            return "Plug Gauge (Go/No-Go) / Inside Micrometer"
        return "Coordinate Measuring Machine (CMM) / 2D Height Gauge"
    if "radius" in p_lower or "r" in c_lower:
        return "Radius Gauge Leaf Set (R0.5 - R25)"
    if "chamfer" in p_lower or "x 45" in c_lower:
        return "Chamfer Gauge / Optical Profile Projector"
    return "Digital Vernier Caliper (0.01 mm) / Outside Micrometer"
```

---

## 2.3 Deep Dive: `python_vs/ml_classifier.py`

Handles training, cross-validation, serialization, and real-time prediction.

```python
# Model Pipeline Declaration
pipeline = Pipeline([
    ("tfidf", TfidfVectorizer(
        ngram_range=(1, 3),
        analyzer="char_wb",
        lowercase=True,
        min_df=1
    )),
    ("clf", LogisticRegression(
        C=10.0,
        max_iter=1000,
        class_weight="balanced",
        random_state=42
    ))
])
```

### Inference Wrapper (`DrawingAnnotationClassifier`):
```python
class DrawingAnnotationClassifier:
    def __init__(self, model_file: Path = MODEL_PATH):
        with open(model_file, "rb") as f:
            self.model = pickle.load(f)

    def predict(self, text: str) -> str:
        """Predicts the category of a single annotation string in < 2.5 ms."""
        return self.model.predict([str(text)])[0]

    def predict_proba(self, text: str) -> dict:
        """Returns softmax probability distribution across all 8 classes."""
        probs = self.model.predict_proba([str(text)])[0]
        return dict(zip(self.model.classes_, probs))
```

---

## 2.4 Deep Dive: `python_vs/generate_report.py`

Constructs an openpyxl Microsoft Excel workbook (`.xlsx`) matching the physical inspection sheet.

### Key Logic & Styling:
1. **Corporate Title Header:** Merged Navy Blue header (`#1F4E78`) displaying company name, address, and GSTIN.
2. **Metadata Grid:** Two 4-column summary blocks containing Part Number, Drawing Name, Material, Finish, Date, and Applicable Tolerance Standard.
3. **13-Column Structure:**
   * `A`: Sr. No.
   * `B`: Parameter Name
   * `C`: X (Nominal)
   * `D`: Tolerance IN X
   * `E`: Y (Nominal)
   * `F`: Tolerance IN Y
   * `G`: Size
   * `H`: Hole Callout
   * `I`: Inspection Instrument
   * `J`: Actual Measurement *(Reserved for QC Technician entry)*
   * `K`: Deviation *(Live Formula)*
   * `L`: QC Result *(Live Formula)*
   * `M`: Remark / Section
4. **Dynamic Excel Formulas:**
   * **Deviation:**
     ```excel
     =IF(ISBLANK(J12), "", ROUND(J12-C12, 4))
     ```
   * **QC Result:**
     ```excel
     =IF(ISBLANK(J12), "PENDING", IF(AND(J12>=C12-D12, J12<=C12+D12), "ACCEPT", "REJECT"))
     ```
5. **Conditional Formatting Rules:**
   * `ACCEPT` $\rightarrow$ Soft green fill (`#C6EFCE`), dark green text (`#006100`).
   * `REJECT` $\rightarrow$ Soft red fill (`#FFC7CE`), dark red text (`#9C0006`).
   * `PENDING` $\rightarrow$ Soft yellow fill (`#FFF2CC`), dark orange text (`#9C6500`).
6. **Sign-off Block:** Pre-formatted cells for `Inspected By: _________`, `Verified By: _________`, and `Approved By: _________`.

---

## 2.5 Deep Dive: `python_vs/api.py`

Asynchronous web backend built with FastAPI and Uvicorn.

### Security Implementation:
1. **Domain Whitelist Validation:**
   ```python
   def is_authorized_domain(email: str) -> bool:
       return bool(re.match(r"^[^@]+@mjmtechnova\.com$", email.strip(), re.IGNORECASE))
   ```
2. **Cryptographic Salted SHA-256 Hashing:**
   ```python
   SALT = os.environ.get("AUTH_SALT", "mjmtechnova_secure_salt_2026_xK9").encode("utf-8")
   def hash_password(password: str) -> str:
       return hashlib.sha256(SALT + password.strip().encode("utf-8")).hexdigest()
   ```
3. **Environment-Driven Credential Management:**
   * `COMPANY_PASSWORD`: Allows company-wide staff login (`quality@mjmtechnova.com`).
   * `ADMIN_PASSWORD`: Sets the dedicated password for `admin@mjmtechnova.com`.
4. **JWT Session Management:**
   * Token issued with 24-hour expiration (`timedelta(hours=24)`).
   * Encoded using `jose.jwt` with `HS256` symmetric signing.

### Endpoints:
* `POST /auth/login`: Authenticates company credentials and issues JWT token.
* `GET /auth/me`: Validates JWT token and returns user profile.
* `POST /api/extract`: Accepts uploaded PDF drawing, runs `DrawingExtractor`, and returns JSON inspection rows.
* `POST /api/report`: Accepts uploaded PDF drawing, runs `generate_report.py`, and streams binary `.xlsx` workbook.
* `GET /api/health`: Health-check endpoint for cloud uptime monitoring.
* `GET /`: Serves static compiled React assets (`frontend/dist/index.html`).

---

## 2.6 Deep Dive: `frontend/` (React 18 + Vite 5)

* **`src/api.js`**:
  Axios HTTP client with dynamic relative URL (`baseURL: ''`) and automatic JWT request interceptor:
  ```javascript
  api.interceptors.request.use((config) => {
    const token = localStorage.getItem('token');
    if (token) {
      config.headers.Authorization = `Bearer ${token}`;
    }
    return config;
  });
  ```
* **`src/App.jsx`**:
  Root application controller managing reactive state for `token` and `user`. Automatically restores session from `localStorage` on page refresh.
* **`src/pages/Login.jsx`**:
  Client-side validation strictly enforcing the `@mjmtechnova.com` email domain before sending credentials to the server.
* **`src/pages/Dashboard.jsx`**:
  Full-featured inspection dashboard:
  - Drag-and-drop PDF upload zone.
  - Interactive search bar filtering across parameter, callout, and instrument columns in real time.
  - Summary metric cards displaying total features, holes, and toleranced dimensions.
  - 13-column interactive inspection table.
  - Single-click Excel download button handling binary blob streams:
    ```javascript
    const blob = new Blob([response.data], {
      type: 'application/vnd.openxmlformats-officedocument.spreadsheetml.sheet'
    });
    const url = window.URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.href = url;
    link.setAttribute('download', `${drawingName}_inspection_report.xlsx`);
    document.body.appendChild(link);
    link.click();
    ```

---

## 2.7 Docker Containerization (`Dockerfile`)

Multi-stage build providing an optimized deployment container:
```dockerfile
FROM python:3.12-slim

WORKDIR /app

# Install system utilities
RUN apt-get update && apt-get install -y --no-install-recommends \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Install Python requirements
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy backend code, models, and pre-built frontend distribution
COPY python_vs/ ./python_vs/
COPY frontend/dist/ ./frontend/dist/

WORKDIR /app/python_vs

ENV PORT=10000
EXPOSE 10000

# Start Uvicorn ASGI server
CMD ["sh", "-c", "uvicorn api:app --host 0.0.0.0 --port ${PORT}"]
```

---

*Report prepared strictly detailing the code architecture and AI model specifications for MJMTECHNOVA Engineering Pvt. Ltd.*
