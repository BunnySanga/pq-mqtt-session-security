# Reproducibility

Use the project directory as the working directory and keep `PYTHONPATH=.` when running scripts directly.

Mac uses `.venv`; Kaggle uses its notebook Python environment. Install the exact declared dependencies from `requirements.txt`. Retain the raw CSV files in `results/raw/` and generated figures in `results/figures/`.

Report only executed measurements. Mac and Kaggle timings are software-environment measurements, not AVR measurements. `avr_sim/simulated_timing.py` is a model based on assumed cycle counts and must be labeled `SIMULATED`.
