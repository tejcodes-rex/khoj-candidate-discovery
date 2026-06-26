# Submission handoff: the steps only you can do

The engine, the CSV, the repo, the docs, the tests, the sandbox app, and the deck
content are all done. What remains needs your accounts and logins. Do these in
order. Budget about an hour.

## 0. Generate the final CSV (30 seconds)

From the project folder, with the candidate file in place:

```
python rank.py --candidates "data/raw/official/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/candidates.jsonl" --out submission.csv
```

Then rename it to your registered Team ID, for example `team_xxx.csv`, and confirm
it passes:

```
python "data/raw/official/[PUB] India_runs_data_and_ai_challenge/India_runs_data_and_ai_challenge/validate_submission.py" team_xxx.csv
```

You should see "Submission is valid." This is the file you upload.

## 1. Push the code to a public GitHub repo (10 minutes)

Create a new public repo on github.com (for example `khoj-candidate-discovery`),
then from the project folder:

```
git remote add origin https://github.com/YOUR_USERNAME/khoj-candidate-discovery.git
git branch -M main
git push -u origin main
```

The large dataset and the deck template are gitignored on purpose, so only code
and docs are pushed. Confirm the repo is set to public.

## 2. Deploy the sandbox demo (15 minutes)

Easiest option is Streamlit Cloud:

1. Go to share.streamlit.io and sign in with GitHub.
2. New app, pick your repo, branch `main`, main file `app.py`.
3. Deploy. It installs from requirements.txt and serves the demo on the bundled
   80-candidate sample.
4. Copy the public URL.

HuggingFace Spaces works too: create a Space (SDK: Streamlit), point it at the
repo, set the app file to `app.py`.

## 3. Fill in the metadata (5 minutes)

Edit `submission_metadata.yaml` and replace every `TODO`:

- team_name: your registered Team ID
- primary_contact phone, and confirm the registered email
- teammate name and email
- github_repo: the URL from step 1
- sandbox_link: the URL from step 2
- ai_tools_used: see the note below

Commit and push the update so the repo metadata matches the portal.

## 4. Deck (already built, just finish two fields)

The deck is generated for you from the mandatory template by `build_deck.py`. The
files `Khoj_Redrob_Submission_Deck.pptx` and `.pdf` (0.33 MB, under the 5 MB
limit) are in the project folder.

Two TODOs remain:
- Slide 1: replace `TODO_TEAM_ID` with your registered Team ID.
- Slide 10: replace `TODO_repo_url` and `TODO_sandbox_url` with the URLs from
  steps 1 and 2.

Easiest path: tell me your Team ID and the two URLs and I will rebuild the PDF in
one step. Or edit `build_deck.py` (the `IDENTITY` and `BODY["Submission Assets"]`
entries), run `python build_deck.py`, and re-export. The slide-by-slide source
text also lives in `docs/DECK.md` if you prefer to edit in PowerPoint directly.

## 5. The AI-tools declaration (decide now)

The rules say declared AI use is not penalized, and that a declaration that
contradicts your Stage 5 interview is the bigger risk. My recommendation is to
declare honestly whatever tools you actually used and keep the one-line note in
the yaml truthful (no candidate data left your machine; ranking is fully offline).
The decks and docs stay in your own plain voice regardless.

## 6. Submit on the portal

Upload three things plus the metadata fields:

- the CSV (named as your Team ID)
- the deck PDF
- the GitHub repo URL, sandbox URL, team and contact details, AI declaration

Remember: 3 submissions maximum, the last valid one counts, and there is no
leaderboard, so submit when you are confident rather than iterating blindly.

## Before you hit submit, the final checklist

- [ ] CSV named as Team ID, validator prints "Submission is valid."
- [ ] GitHub repo is public and the reproduce command in the README works on a clean clone
- [ ] Sandbox URL loads and ranks the sample
- [ ] submission_metadata.yaml has no TODOs left and is pushed
- [ ] Deck PDF is under 5 MB and uses the official template
- [ ] You can explain the four scoring components and the honeypot logic out loud (see docs/METHODOLOGY.md)
