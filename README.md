# Oscar Bait Prediction Pipeline

This project contains a clean, 5-step pipeline to extract film data from Wikidata and prepare it for Machine Learning.

## Folder Structure
- `data/`: Raw data from Wikidata (JSON/JSONL).
- `outputs/`: Final ML-ready datasets (CSV).
- `*.py`: The 5 sequential steps of the pipeline.

## How to run
Execute the scripts in order:

1. `python 01_collect_movie_ids.py`: Gathers film Q-IDs for 2011-2026.
2. `python 02_fetch_movie_features.py`: Fetches targeted features (Genre, Director, Cast, etc.).
3. `python 03_fetch_prestige_data.py`: Fetches Oscar history for all talent.
4. `python 04_build_final_dataset.py`: Integrates everything into a clean CSV.
5. `python 05_run_analysis.py`: Performs statistical analysis for RQ1.

## Key Features in Final Dataset
- `target_oscar_nom`: Binary (1 = Academy Award nomination/win).
- `director_prestige`: Number of previous Oscar nominations/wins for the director.
- `cast_prestige`: Combined Oscar history for the top 5 cast members.
- `month`: Release month (useful for Oscar Bait timing analysis).
- `genre_*`: Binary flags for the top 20 most frequent genres.
