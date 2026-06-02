# WSE_project
# Technical Project Summary: Oscar Bait Prediction Pipeline

This project builds a machine learning pipeline to predict Academy Award nominations using structured metadata from Wikidata. The study analyzes global films released over a 15-year window (2011–2026). Instead of using text-based critical reviews, the model relies entirely on factual graph features to identify patterns behind "Oscar bait" (RQ1) and measure data gaps in the knowledge graph (RQ2).

The data engineering workflow is divided into three concrete phases.

---

## Phase 1: Film ID Collection & Error Mitigation

The first step was building a baseline dataset of all relevant film entities. We queried the Wikidata SPARQL endpoint to find items matching specific semantic criteria:

* **Target Criteria:** Items must be an instance of a film (`wdt:P31 wd:Q11424`) and possess a valid publication date (`wdt:P577`).
* **Pipeline Challenges:** Requesting an entire year of global cinema caused severe server strain, resulting in HTTP 429 (Rate Limit Hit) and HTTP 502 (Bad Gateway) timeouts.
* **The Solution:** We deployed a Python patch script that isolated the broken years (2013 and 2018) and queried them in smaller, monthly increments.

By sub-dividing the workload into 12 monthly chunks, the query size dropped significantly, bypassing server timeouts. The script combined, deduplicated, and validated the records, saving a finalized list of approximately 75,000 unique film Q-IDs into `movie_ids_2011_2026.json`.

---

## Phase 2: Dynamic Feature Harvesting

Instead of guessing which features matter, we designed a pipeline for **Dynamic Feature Discovery** to harvest every single piece of data available for these 75,000 films.

### Data Flow Architecture

[Master Q-ID List] ➔ [Batching (50 IDs)] ➔ [Wikidata API Call] ➔ [Data Type Parser] ➔ [Checkpoint Verification] ➔ [Append to JSONL]

```markdown
# Technical Project Summary: Oscar Bait Prediction Pipeline

This project builds a machine learning pipeline to predict Academy Award nominations using structured metadata from Wikidata. The study analyzes global films released over a 15-year window (2011–2026). Instead of using text-based critical reviews, the model relies entirely on factual graph features to identify patterns behind "Oscar bait" (RQ1) and measure data gaps in the knowledge graph (RQ2).

The data engineering workflow is divided into three concrete phases.

---

## Phase 1: Film ID Collection & Error Mitigation

The first step was building a baseline dataset of all relevant film entities. We queried the Wikidata SPARQL endpoint to find items matching specific semantic criteria:

* **Target Criteria:** Items must be an instance of a film (`wdt:P31 wd:Q11424`) and possess a valid publication date (`wdt:P577`).
* **Pipeline Challenges:** Requesting an entire year of global cinema caused severe server strain, resulting in HTTP 429 (Rate Limit Hit) and HTTP 502 (Bad Gateway) timeouts.
* **The Solution:** We deployed a Python patch script that isolated the broken years (2013 and 2018) and queried them in smaller, monthly increments.

By sub-dividing the workload into 12 monthly chunks, the query size dropped significantly, bypassing server timeouts. The script combined, deduplicated, and validated the records, saving a finalized list of approximately 75,000 unique film Q-IDs into `movie_ids_2011_2026.json`.

---

## Phase 2: Dynamic Feature Harvesting

Instead of guessing which features matter, we designed a pipeline for **Dynamic Feature Discovery** to harvest every single piece of data available for these 75,000 films.

### Data Flow Architecture

```

[Master Q-ID List] ➔ [Batching (50 IDs)] ➔ [Wikidata API Call] ➔ [Data Type Parser] ➔ [Checkpoint Verification] ➔ [Append to JSONL]

```

* **API Protocol:** The script sends requests to the Wikidata Action API using the `wbgetentities` endpoint, processing films in optimal chunks of 50 items.
* **Data Extraction:** The code extracts the entire `claims` dictionary. It automatically loops through every property ID (`P-number`) present on an entity page, parsing four data types: `wikibase-entityid` (categorical links), `quantity` (numeric values like budget), `time` (dates), and standard strings.
* **Fault Tolerance:** To protect against network drops during the 20-to-30-minute extraction process, the script writes data sequentially to a JSON Lines file (`raw_movie_features.jsonl`). A built-in checkpoint system reads the file upon startup, logs already completed Q-IDs, and automatically resumes processing remaining items without duplicating API calls.

---

## Phase 3: Matrix Structuring & Downstream Analytics

Once the raw extraction completes, the pipeline shifts from collection to preparation:

* **Data Flattening:** The `.jsonl` file will be loaded into a `pandas` DataFrame where rows represent individual films and columns represent the discovered `P-numbers`.
* **Label Mapping:** A utility SPARQL query will translate abstract columns (e.g., mapping `P1040` to "Film Editor" and `P2515` to "Costume Designer") to make the dataset human-readable.
* **Analysis:** Missing data points will remain as `None` values. We will calculate the missingness percentage across nominated versus non-nominated films to statistically track knowledge graph bias (RQ2). Finally, this matrix will be fed into a tree-based classifier (like Random Forest or XGBoost) to calculate feature importance scores and isolate the true structural signals of an Oscar contender (RQ1/RQ3).

```