# Khoj: Submission Package

Team: **Khoj**, Track 1, Data and AI Challenge (Intelligent Candidate Discovery), India Runs by Redrob AI

Everything the portal needs is in this folder. Follow the steps at the bottom.

## What's in this folder

| File | What it is | Where it goes on the portal |
|---|---|---|
| `khoj_submission.csv` | The top-100 ranked candidates. Passes the official validator. | "A ranked output file (CSV/XLSX)" upload |
| `Khoj_Redrob_Submission_Deck.pdf` | The deck on the mandatory Redrob template (0.33 MB, under the 5 MB limit). | "PPT/deck converted to PDF" upload |
| `submission_metadata.yaml` | Team and reproducibility metadata. Mirror these into the portal fields. | Portal metadata fields |
| `logo/khoj-logo.png` + `.svg` | Team logo (wordmark + mark). | Wherever a logo/avatar is requested |
| `logo/khoj-icon.png` + `.svg` | Square icon version (for sandbox/app/avatar). | Square logo slots |

## The three things the portal asks for (from the dashboard)

1. **GitHub repository URL** (must be public).
2. **The deck as a PDF** (this folder, under 5 MB). The template was mandatory and is used as-is.
3. **The ranked output CSV** (this folder, validator-clean).
Plus the metadata fields (team name, contact, AI-tools declaration, sandbox link).

## Before you upload (do these in order)

1. **Rename the CSV to your registered Team ID** if the portal requires it, for example `team_xxx.csv`. The validator only checks the format, but the spec says the filename should be your participant/team ID. The content is final and valid as-is.
2. **Push the code to a public GitHub repo** (from the project root):
   ```
   git remote add origin https://github.com/YOUR_USERNAME/khoj-candidate-discovery.git
   git branch -M main
   git push -u origin main
   ```
3. **Deploy the sandbox** (Streamlit Cloud → New app → this repo → `app.py`) and copy the public URL.
4. **Fill the remaining metadata** in `submission_metadata.yaml` and on the portal: phone, teammate name and email, the GitHub URL, the sandbox URL, and the AI-tools declaration. Reconcile the contact email (use whichever is registered).
5. **Re-run the validator one last time** on the exact CSV you will upload:
   ```
   python "data/raw/official/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" submission/khoj_submission.csv
   ```
   You should see "Submission is valid."
6. **Submit on the portal.** Note: three submissions maximum, the last valid one counts, no live leaderboard.

## What I still need from you to finish the metadata and deck

- Your **registered Team ID** (for the CSV filename, if it differs from "Khoj").
- **Teammate name and email**.
- A **contact phone number**.

Give me those and I will finalize the metadata file and the deck so this folder is 100 percent upload-ready.
