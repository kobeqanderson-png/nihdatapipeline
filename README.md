# data analysis (sex-specific)
If you prefer conda, create a conda env and `pip install -r requirements.txt` there.

```
python src/quick_test.py
# Run the example quick test
pip install -r requirements.txt
python -m pip install --upgrade pip
.\.venv\Scripts\Activate.ps1
python -m venv .venv
```powershell
Quick start (PowerShell)

- run_analysis.ps1  # quick runner for Windows PowerShell
- requirements.txt
- src/              # reusable Python modules (data loading, cleaning, features, viz)
- notebooks/        # exploratory notebooks
- data/processed/   # cleaned outputs
- data/raw/         # place raw input files here (small examples ok)
Structure

Scaffold for data cleaning and analysis (pandas-based).



