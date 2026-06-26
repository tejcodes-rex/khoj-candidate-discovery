# Reproduces the ranking step exactly as Stage 3 does: CPU only, no network.
# The ranker uses only the Python standard library, so there is nothing to pip
# install for reproduction.
#
# Build:
#   docker build -t khoj .
# Run (mount the folder holding candidates.jsonl):
#   docker run --rm -v "$PWD":/data khoj --candidates /data/candidates.jsonl --out /data/submission.csv

FROM python:3.12-slim
WORKDIR /app
COPY khoj/ ./khoj/
COPY rank.py .
ENTRYPOINT ["python", "rank.py"]
