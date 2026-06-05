# Oscar Bait Prediction Pipeline

This project builds a machine learning pipeline to predict Academy Award nominations using factual metadata from Wikidata. It analyzes global films released between 2011 and 2026 to identify patterns behind "Oscar bait" (RQ1).

## 🚀 The 5-Step Pipeline

Execute these scripts in order to build the dataset from scratch:

### 1. `01_collect_movie_ids.py`
- **Goal**: Build a baseline list of all film entities.
- **Action**: Queries the Wikidata SPARQL endpoint for items where `instance of = film` (P31/Q11424) and have a publication date within the 2011-2026 range.
- **Output**: `data/movie_ids.json`

### 2. `02_fetch_movie_features.py`
- **Goal**: Gather specific metadata for the collected films.
- **Action**: Uses the Wikidata Action API (`wbgetentities`) to fetch a targeted set of 13 core properties (Genre, Director, Cast, etc.).
- **Output**: `data/raw_movies.jsonl`

### 3. `03_fetch_prestige_data.py`
- **Goal**: Collect the "Prestige" history of talent.
- **Action**: Queries SPARQL for every person who has ever been nominated for or won an Academy Award. This creates a historical lookup table.
- **Output**: `data/talent_prestige.json` and `data/oscar_categories.json`

### 4. `04_build_final_dataset.py`
- **Goal**: Data Integration & Feature Engineering.
- **Action**: 
    - Translates Q-IDs to English labels.
    - **Calculates Prestige**: Counts previous Oscars/nominations for directors and cast *strictly before* the movie's release year (preventing data leakage).
    - **Temporal Engineering**: Extracts release month.
    - **Target Labeling**: Sets `target_oscar_nom = 1` if the movie matches any Oscar category.
    - **One-Hot Encoding**: Creates binary flags for the top 20 most frequent genres.
- **Output**: `outputs/final_dataset.csv`

### 5. `05_run_analysis.py`
- **Goal**: Statistical Validation.
- **Action**: Calculates correlations between engineered features and the target variable, providing immediate insights for RQ1.

---

## 📊 Feature Catalog (Data Dictionary)

The following Wikidata properties are extracted and processed:

### 🎬 Core Movie Features

| Property | Label | Description | Why it's relevant |
| :--- | :--- | :--- | :--- |
| **P31** | `instance_of` | Entity type (e.g., film, documentary). | Filters formats and identifies documentary/animation trends. |
| **P577** | `release_date` | Official publication date. | Used to extract **Release Month** (key for "Oscar Season" analysis). |
| **P136** | `genre` | Creative category (e.g., drama, comedy). | Identifies genres favored by the Academy (e.g., Biography, Drama). |
| **P57** | `director` | Creative lead. | Foundation for **Director Prestige** calculations. |
| **P161** | `cast_member` | Actors/Performers. | Foundation for **Cast Prestige** (Top 5 billed actors). |
| **P272** | `production_company`| Studio/Producer. | Identifies powerhouses like A24 or Searchlight. |
| **P2047** | `duration` | Length in minutes. | Explores the "epic" length vs. nomination probability. |
| **P2142** | `budget` | Production cost. | Correlates financial investment with critical recognition. |
| **P495** | `country_of_origin` | Production country. | Useful for International Feature Film analysis. |
| **P364** | `original_language` | Primary language. | Categorizes foreign language contenders. |
| **P144** | `based_on` | Source material. | Identifies **Adaptations** (books, plays), a staple of Oscar bait. |

### 🏆 Target & Award Features

| Property | Label | Description | Usage |
| :--- | :--- | :--- | :--- |
| **P1411** | `nominated_for` | Nominations received. | Primary source for `target_oscar_nom`. |
| **P166** | `award_received` | Awards won. | Secondary source for `target_oscar_nom`. |

### 🛠️ Engineered Features (Calculated)

- **director_prestige**: Cumulative count of Oscar nominations/wins the director had *before* the current movie.
- **cast_prestige**: Cumulative count of Oscar nominations/wins for the top 5 cast members *before* the current movie.
- **is_adaptation**: Binary flag (1 if movie is based on existing work).
- **genre_X**: Binary flags for the top 20 genres (One-Hot Encoding).

---

## 📂 Project Structure
- `data/`: Intermediate JSON/JSONL files (Raw Wikidata dumps).
- `outputs/`: Final ML-ready CSV files.
- `*.py`: Sequential pipeline scripts (01 to 05).
- `README.md`: Project documentation.
- `FEATURES.md`: Legacy feature documentation (merged into README).
