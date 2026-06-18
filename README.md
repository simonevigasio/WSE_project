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
- **Goal**: Data Integration, Filtering & Feature Engineering.
- **Action**: 
    - **Filters Eligibility**: Discards TV movies, short films, adult films, and films lacking commercial proxies (budget/box office/studio).
    - Merges movie features with English labels.
    - **Calculates Prestige**: Counts previous Oscars/nominations for directors and cast *strictly before* the movie's release year.
    - **Temporal Engineering**: Extracts release year and month (uses "Unknown_month" for missing months from the earliest release).
    - **One-Hot Encoding**: Creates binary flags for the top 20 most frequent **genres, countries, languages, and production companies**, as well as **release months**, to handle categorical data and multi-value entries (e.g., co-productions).
    - **Data Imputation**: Fills missing durations with the **genre-specific median**.
- **Output**: `outputs/final_dataset.csv` (Zero NULLs).

### 6. `06_null_value_analysis.py`
- **Goal**: Quality Control.
- **Action**: Analyzes the final dataset for missing values (NULLs), verifying data completeness.

### 7. `07_run_analysis.py`
- **Goal**: Feature Frequency Analysis.
- **Action**: Analyzes the frequency of binary features (genres, countries, languages, studios, months) within the `final_dataset.csv`. It identifies which features are most common and provides a summary by category.
- **Output**: `outputs/binary_feature_frequencies.csv` containing counts and percentages for all engineered binary features.

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
| **P2130** | `cost` | Production budget. | Foundation for the `has_financial_data` flag. |
| **P2142** | `box_office` | Total revenue. | Foundation for the `has_financial_data` flag. |
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
- **has_financial_data**: Binary indicator of whether budget or box office data was available (original values are dropped to maintain a clean dataset).
- **month_X**: Binary flags for each release month (1-12 and `unknown`).
- **genre_X**: Binary flags for the top 20 genres (includes `genre_other_or_unknown`).
- **country_X**: Binary flags for the top 20 countries of origin (includes `country_other_or_unknown`).
- **lang_X**: Binary flags for the top 20 original languages (includes `lang_other_or_unknown`).
- **studio_X**: Binary flags for the top 20 production companies (includes `studio_other_or_unknown`).
- **duration**: Missing values are imputed using the average of the medians of the movie's genres. If no genre data is available, the global median is used.

---

## 📂 Project Structure
- `data/`: Intermediate JSON/JSONL files (Raw Wikidata dumps).
- `outputs/`: Final ML-ready CSV files and analysis reports.
    - `final_dataset.csv` (Fully processed, zero NULLs)
    - `binary_feature_frequencies.csv` (Summary of engineered feature occurrences)
- `*.py`: Sequential pipeline scripts (01 to 07).
- `README.md`: Project documentation.
