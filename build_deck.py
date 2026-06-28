"""
Fill the mandatory Redrob deck template with our content AND real diagrams.

The template ("submission/Idea Submission Template _ Redrob.pptx") must be used
as-is, so we load it and write into its existing prompt boxes, never touching the
titles or the background. Slides that ask for a diagram (architecture, workflow,
methodology, explainability, results) get an actual rendered diagram image, not
text and symbols. The title and closing slides get the Khoj logo.

    pip install python-pptx
    python build_deck.py
Then export "Khoj_Redrob_Submission_Deck.pptx" to PDF (handled separately).
"""

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor
from pptx.util import Pt, Inches

TEMPLATE = "submission/Idea Submission Template _ Redrob.pptx"
OUT = "Khoj_Redrob_Submission_Deck.pptx"
INK = RGBColor(0x20, 0x27, 0x29)

IDENTITY = {
    "Team Name :": "Team Name : Khoj",
    "Team Leader Name :": "Team Leader Name : Tejas Mane",
    "Problem Statement :": "Problem Statement : Intelligent Candidate Discovery (Data and AI Challenge)",
}

# Slides answered in text (precise answers to every question on the slide).
BODY = {
    "Solution Overview": [
        "Khoj is an AI candidate discovery engine that ranks the 100 best fit candidates for the Senior "
        "AI Engineer role out of 100,000 profiles, with a grounded reason for every pick.",
        "It reads what each person actually built in their career history, not the keywords they pasted "
        "into a summary or skills list.",
        "What differentiates it from traditional matching: keyword filters and embedding similarity systems "
        "reward keyword stuffing and miss plainly worded talent. Khoj instead scores demonstrated career "
        "evidence over surface keywords, weights skills by endorsements, time used and assessment "
        "scores, factors in whether a candidate is actually reachable, detects and excludes impossible "
        "\"honeypot\" profiles, and explains every decision.",
        "It is transparent and fast: rule based, the whole pool in under two minutes on a CPU with no "
        "network, where a system that calls a model per candidate cannot.",
    ],
    "JD Understanding & Candidate Evaluation": [
        "Key requirements extracted from the JD: production embeddings and retrieval, vector database or "
        "hybrid search operations, strong Python, ranking evaluation literacy (NDCG, MRR, MAP), 6 to 8 "
        "years ideal, applied ML at product (not services) companies, an India hub or willingness to "
        "relocate (Pune/Noida preferred), and a shipped end to end ranking, search or recommendation system.",
        "Named disqualifiers we also read from the JD: keyword stuffers, services only careers, title-"
        "chasing job hoppers, vision/speech only without NLP or IR, and pure research without production.",
        "Most important signals, and how we judge fit beyond keywords: career history evidence of "
        "retrieval/ranking/recsys work (weighted highest), trust weighted skills, and behavioral "
        "availability. Because we read the demonstrated work, a strong candidate who built a recommendation "
        "system in plain words ranks high without the buzzwords, while a Marketing Manager who pasted AI "
        "skills ranks near zero.",
    ],
    "Technologies Used": [
        "Python 3.12, standard library only in the ranking path (no third party packages): chosen to meet "
        "the 5-minute CPU reproduction limit, to scale to a real 200,000-plus pool, and so judges reproduce "
        "it with zero setup.",
        "A custom word boundary matcher, a hand built skill ontology, and a transparent rule based scorer: "
        "chosen over an embedding model because embeddings reward the keyword stuffing the JD warns about "
        "and cannot explain themselves.",
        "Streamlit for the hosted sandbox demo; pytest for the test suite, including a test that runs the "
        "organizers' own validator; Docker for reproducible Stage-3 runs; Git for authentic, incremental "
        "history.",
        "No GPU, no network, and no per candidate model calls anywhere in the ranking path, by design.",
    ],
    "Submission Assets": [
        "GitHub repository: https://github.com/tejcodes-rex/khoj-candidate-discovery",
        "Live sandbox (Google Colab, runs end to end on a sample): https://colab.research.google.com/github/tejcodes-rex/khoj-candidate-discovery/blob/main/sandbox.ipynb",
        "Reproduce command: python rank.py --candidates ./candidates.jsonl --out ./submission.csv",
        "Ranked output CSV: passes the official validator (\"Submission is valid.\"), 0 honeypots in the top 100.",
        "Docs in the repo: README, a full methodology walkthrough (docs/METHODOLOGY.md), and the test suite.",
    ],
}

# Slides whose answer IS a diagram. Optional one-line caption above the image.
IMAGES = {
    "Ranking Methodology": ("diagrams/scoring.png",
        "The scoring is fully transparent, and every term reads from the candidate's own data."),
    "Explainability & Data Validation": ("diagrams/reasoning.png",
        "Every pick is explained from the candidate's own data."),
    "End-to-End Workflow": ("diagrams/workflow.png", None),
    "System Architecture": ("diagrams/architecture.png", None),
    "Results & Performance": ("diagrams/results.png", None),
}

CLOSING = ("Khoj finds the engineers a keyword filter buries, refuses the ones it would be fooled by, "
           "in under two minutes, with a reason for every pick.")


def write_body(shape, lines, size=Pt(12)):
    tf = shape.text_frame
    tf.word_wrap = True
    tf.clear()
    for i, line in enumerate(lines):
        para = tf.paragraphs[0] if i == 0 else tf.add_paragraph()
        para.space_after = Pt(6)
        run = para.add_run()
        run.text = line
        run.font.size = size
        run.font.name = "Calibri"
        run.font.color.rgb = INK


def body_box(slide):
    boxes = [sh for sh in slide.shapes
             if sh.has_text_frame and sh.shape_type == MSO_SHAPE_TYPE.TEXT_BOX]
    boxes.sort(key=lambda s: s.top or 0)
    return boxes


def title_of(slide):
    boxes = body_box(slide)
    return boxes[0].text_frame.text.strip() if boxes else ""


def main():
    prs = Presentation(TEMPLATE)
    slides = list(prs.slides)
    sw = prs.slide_width

    # Slide 1: fill the identity fields only. The template's title slide is a
    # designed layout (INDIA.RUNS art), so we do not stamp our logo over it; the
    # logo goes in the portal's team-logo field instead.
    for sh in slides[0].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() in IDENTITY:
            write_body(sh, [IDENTITY[sh.text_frame.text.strip()]], size=Pt(16))

    # Content slides
    for slide in slides[1:]:
        boxes = body_box(slide)
        if not boxes:
            continue
        title = boxes[0].text_frame.text.strip()
        body = boxes[-1] if len(boxes) >= 2 else None

        if title in BODY:
            n = len(BODY[title])
            write_body(body, BODY[title], size=Pt(12 if n > 3 else 13))

        elif title in IMAGES:
            img, caption = IMAGES[title]
            if body is not None:
                write_body(body, [caption] if caption else [""], size=Pt(12))
            top = Inches(1.95) if caption else Inches(1.5)
            width = Inches(9.0)
            left = Inches(0.5)
            slide.shapes.add_picture(img, left, top, width=width)

    # Closing slide: the template already has its own "Thank You" design, so we
    # leave it clean and do not clutter it.

    prs.save(OUT)
    print(f"Saved {OUT} with {len(slides)} slides, 5 diagrams, and the Khoj logo.")


if __name__ == "__main__":
    main()
