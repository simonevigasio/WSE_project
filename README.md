# Oscar Bait Prediction Pipeline

This project builds a machine learning pipeline to predict Academy Award nominations using factual metadata from Wikidata. It analyzes films (primarily from USA and Europe) released between 2011 and 2026 to identify patterns behind "Oscar bait" (RQ1).

## 🚀 The 7-Step Pipeline

Execute these scripts in order to build the dataset from scratch:

### 1. `01_collect_movie_ids.py`
- **Goal**: Build a baseline list of all film entities.
- **Action**: Queries the Wikidata SPARQL endpoint for items where `instance of = film` (P31/Q11424). Filters for films released in USA or Europe.
- **Output**: `data/movie_ids.json`

### 2. `02_fetch_movie_features.py`
- **Goal**: Gather specific metadata for the collected films.
- **Action**: Uses the Wikidata Action API (`wbgetentities`) to fetch a targeted set of 14 core properties (Genre, Director, Cast, etc.).
- **Output**: `data/raw_movies.jsonl`

### 3. `03_fetch_prestige_data.py`
- **Goal**: Collect the "Prestige" history of talent.
- **Action**: Queries SPARQL for every person who has ever been nominated for or won an Academy Award. This creates a historical lookup table.
- **Output**: `data/talent_prestige.json` and `data/oscar_categories.json`

### 4. `04_fetch_labels.py`
- **Goal**: Resolve entity Q-IDs to English labels.
- **Action**: Translates numeric IDs for genres, directors, and studios into human-readable strings using the Wikidata API.
- **Output**: `data/wikidata_english_labels.json`

### 5. `05_build_final_dataset.py`
- **Goal**: Data Integration & Feature Engineering.
- **Action**: 
    - Merges movie features with English labels.
    - **Calculates Prestige**: Counts previous Oscars/nominations for directors and cast *strictly before* the movie's release year.
    - **Temporal Engineering**: Extracts release year and month (uses "Unknown_month" for missing months).
    - **Data Imputation**: Fills missing durations with the **genre-specific median** and missing languages with the **global mode**.
    - **One-Hot Encoding**: Creates binary flags for the top 20 most frequent genres.
- **Output**: 
    - `outputs/final_dataset_with_financials.csv`: Raw sparse financials.
    - `outputs/final_dataset_with_financial_flag.csv`: Replaces financials with a binary `has_financial_data` flag (Zero NULLs).

### 6. `06_null_value_analysis.py`
- **Goal**: Quality Control.
- **Action**: Analyzes both versions of the final dataset for missing values (NULLs), verifying data completeness.

### 7. `07_run_analysis.py`
- **Goal**: Statistical Validation.
- **Action**: Calculates correlations and nomination rates specifically for the `final_dataset_with_financial_flag.csv` version. Generates visual plots for financial impact, production company performance, top correlations, and monthly trends.
- **Output**: Visualizations in `outputs/plots/` (including `studio_impact.png`).

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
| **P2130** | `cost` | Production budget. | Correlates financial investment with critical recognition. |
| **P2142** | `box_office` | Total revenue. | Explores the relationship between commercial success and awards. |
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
- **duration (imputed)**: Missing values filled using the median runtime of the movie's primary genre.
- **original_language (imputed)**: Missing values filled using the most frequent language in the dataset.
- **has_financial_data**: (Flag version only) Binary indicator of whether budget or box office data was available.

---

## 📂 Project Structure
- `data/`: Intermediate JSON/JSONL files (Raw Wikidata dumps).
- `outputs/`: Final ML-ready CSV files.
    - `final_dataset_with_financials.csv` (Raw numeric financials)
    - `final_dataset_with_financial_flag.csv` (Binary financial flag)
- `*.py`: Sequential pipeline scripts (01 to 07).
- `README.md`: Project documentation.
