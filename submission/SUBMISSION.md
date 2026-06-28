# Khoj: Submission Package

Team: **Khoj**, Track 1, Data and AI Challenge (Intelligent Candidate Discovery), India Runs by Redrob AI

Everything the portal needs is in this folder. Follow the steps at the bottom.

## What's in this folder

| File | What it is | Where it goes on the portal |
|---|---|---|
| `khoj_submission.xlsx` | The top 100 ranked candidates, excel format. **Upload this one**, the portal asks for XLSX. | "A ranked output file in XLSX format" upload |
| `khoj_submission.csv` | Same top 100, csv. Backup, and it passes the official validator. | keep as backup |
| `Khoj_Redrob_Submission_Deck.pdf` | The deck on the mandatory Redrob template. | "PPT/deck converted to PDF" upload |
| `submission_metadata.yaml` | Team and reproducibility metadata. Mirror these into the portal fields. | Portal metadata fields |
| `logo/khoj-logo.png` + `.svg` | Team logo (wordmark + mark). | Wherever a logo/avatar is requested |
| `logo/khoj-icon.png` + `.svg` | Square icon version (for sandbox/app/avatar). | Square logo slots |

## The three things the portal asks for (from the dashboard)

1. **GitHub repository URL** (must be public): https://github.com/tejcodes-rex/khoj-candidate-discovery
2. **The deck as a PDF** (this folder, under 5 MB). The template was mandatory and is used as-is.
3. **The ranked output file in XLSX format**: upload `khoj_submission.xlsx` from this folder.

## Before you upload (do these in order)

1. **The ranked file is XLSX.** The portal field says "XLSX format" and accepts excel/spreadsheet files, so upload `khoj_submission.xlsx`. The `.csv` is kept as a backup only. If the portal wants the filename to be your registered Team ID, rename it first.
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
