# ResearchPulse

ResearchPulse is a research-literature exploration prototype that I developed during my work at Rajaie Cardiovascular Center. It was part of my work on tools for finding and exploring scientific papers.

This public repository is a snapshot of an early Streamlit implementation. It should not be treated as a complete release of the system or as a production research platform.

## What is included

- `researchPulse/research_dashboard.py` — the Streamlit dashboard and paper explorer.
- `researchPulse/utils/PMC_API.py` — code for retrieving literature data from PubMed Central-related sources.
- `researchPulse/utils/visuals.py` — visualizations used by the dashboard.
- `researchPulse/articles.db` — a local SQLite database used by the prototype.
- `researchPulse/requierments.txt` — the historical dependency list (the filename is spelled this way in the repository).

The dashboard includes literature search controls, filters, paper details, charts, and CSV export. Some features use local data and some depend on external services.

## Running the historical prototype

The main entry point is `researchPulse/research_dashboard.py`. From the `researchPulse/` application directory, the intended launch command is:

```bash
streamlit run research_dashboard.py
```

This is an older prototype, and I have not provided a verified clean-environment installation procedure. The dependency file may require maintenance before the application runs on a current Python environment.

## Scope

The public snapshot is intended to show part of my work on research retrieval and exploration. It is not a validated source of medical advice or a substitute for verifying information against the original publications.
