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
