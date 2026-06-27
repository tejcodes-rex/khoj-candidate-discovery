"""
Fill the mandatory Redrob deck template with our content.

The template ("Idea Submission Template _ Redrob.pptx") must be used as-is, so we
load it and write into its existing prompt boxes, never touching the titles or the
background. Slides that have only a title (architecture, closing) get a new body
box that matches the template's dark text on its light background.

Output: "Khoj_Redrob_Submission_Deck.pptx". Review it, fill the TODOs on slides 1
and 10, then export to PDF (under 5 MB).

    pip install python-pptx
    python build_deck.py
"""

from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.dml.color import RGBColor
from pptx.util import Pt, Inches

TEMPLATE = "Idea Submission Template _ Redrob.pptx"
OUT = "Khoj_Redrob_Submission_Deck.pptx"
INK = RGBColor(0x20, 0x27, 0x29)  # the template's text color

IDENTITY = {
    "Team Name :": "Team Name : TODO_TEAM_ID",
    "Team Leader Name :": "Team Leader Name : Tejas Mane",
    "Problem Statement :": "Problem Statement : Intelligent Candidate Discovery (Data and AI Challenge)",
}

BODY = {
    "Solution Overview": [
        "Khoj ranks the best-fit candidates for the Senior AI Engineer role out of 100,000 profiles.",
        "It reads what each person actually built in their career history, not the keywords they listed.",
        "What sets it apart: the job description is the rubric, skills are trust-weighted so keyword "
        "stuffers score near zero, behavioral availability is factored in, impossible honeypot profiles "
        "are excluded, and every pick comes with a grounded reason.",
        "It ranks the whole pool in about 40 seconds on a laptop CPU with no network, where a system "
        "that calls a model per candidate cannot.",
    ],
    "JD Understanding & Candidate Evaluation": [
        "Key requirements read from the JD: production embeddings and retrieval, vector-database and "
        "hybrid-search experience, strong Python, ranking-evaluation literacy (NDCG, MRR, MAP), 6 to 8 "
        "years ideal, product-company background, an India hub or willingness to relocate.",
        "Most important signals: career-history evidence of retrieval, ranking and recommendation work "
        "(weighted highest); skills trust-weighted by endorsements, months used and assessment scores; "
        "behavioral availability such as recent activity, recruiter response rate and open-to-work.",
        "Explicit disqualifiers applied: off-role keyword stuffers, services-only careers, job-hoppers, "
        "vision or speech-only profiles, and pure-research backgrounds with no production work.",
    ],
    "Ranking Methodology": [
        "Fit score from four weighted parts: career evidence 0.40, skill trust 0.22, title 0.18, "
        "experience 0.20.",
        "Two multipliers then scale it: behavioral availability and location.",
        "Named JD disqualifiers apply real penalties, and honeypots are forced to a score of zero.",
        "We chose transparent rule-based scoring over embedding similarity for three reasons: similarity "
        "rewards the keyword stuffing the JD warns about, the 5-minute CPU budget rules out per-candidate "
        "models, and we must be able to explain every rank.",
        "Output is sorted by score then candidate id, which guarantees the validator's tie-break rule.",
        "Because the ground truth is hidden, we built an independent gold-labeler and an offline NDCG "
        "harness to validate and calibrate the weights, with ablations proving each signal earns its place.",
    ],
    "Explainability & Data Validation": [
        "Each of the 100 rows carries a one-line reason built only from the candidate's own fields and "
        "the score breakdown: title, years, the specific career evidence, the trust-verified skills, and "
        "the activity signals.",
        "Honest concerns are surfaced and the tone matches the rank; nothing is templated.",
        "Hallucination is prevented by construction: a reason can only cite values that exist in the "
        "profile, and skill matching is word-boundary based so no false skills are attributed.",
        "Honeypots, the internally-impossible profiles, are detected by consistency checks and kept out "
        "of the shortlist entirely.",
    ],
    "End-to-End Workflow": [
        "1. Read candidates.jsonl, streamed and parsed line by line.",
        "2. Score each candidate: career evidence, skill trust, title, experience.",
        "3. Apply disqualifier penalties, then behavioral and location multipliers.",
        "4. Exclude honeypots.",
        "5. Sort by score (ties broken by candidate id) and take the top 100.",
        "6. Generate a grounded reason for each and write the validator-compliant CSV.",
        "One command, about 40 seconds, CPU only, fully offline.",
    ],
    "System Architecture": [
        "Profiles  >  ingest and normalize  >  feature and signal extraction  >  four-component fit "
        "score  >  behavioral and location multipliers  >  honeypot guard  >  ranked top 100 with "
        "reasoning.",
        "",
        "Modules: lexicons (the JD encoded as terms), scoring (the core), honeypot (consistency checks), "
        "reasoning (grounded explanations), and rank.py (the entrypoint).",
        "Standard library only, so it reproduces anywhere with no setup.",
    ],
    "Results & Performance": [
        "Passes the official validator. Ranks 100,000 candidates in about 40 seconds, CPU only, no "
        "network. The limit is 5 minutes.",
        "0 honeypots in the top 100. Disqualification is above 10 percent.",
        "Our top 100: 100 of 100 India-based, 0 keyword stuffers, 0 services-only careers, mean "
        "experience 6.0 years, mean recruiter response rate 0.74.",
        "A naive keyword-count ranking fills its top 100 with 85 keyword stuffers and 70 unreachable "
        "candidates. Ours has zero stuffers.",
        "Against our own gold-labeler (the real labels are hidden): internal NDCG@10 of 0.96, and a "
        "top 10 made up entirely of ideal-tier candidates.",
        "Meets the brief: it ranks rather than filters, reads the JD deeply, integrates all three signal "
        "families, and is both fast and explainable.",
    ],
    "Technologies Used": [
        "Python 3.12, standard library only for the ranker: no GPU, no network, no paid APIs. Chosen to "
        "meet the 5-minute CPU reproduction limit and to scale to a real 200,000-plus production pool.",
        "Streamlit for the hosted sandbox demo.",
        "pytest for the test suite, including a test that runs the organizers' own validator.",
        "Git for authentic, incremental development history.",
        "No per-candidate model calls anywhere in the ranking path, by design.",
    ],
    "Submission Assets": [
        "GitHub repository: TODO_repo_url",
        "Live sandbox demo: TODO_sandbox_url",
        "Reproduce command: python rank.py --candidates ./candidates.jsonl --out ./submission.csv",
        "Validator: passes with \"Submission is valid.\"",
        "Docs in the repo: README, a full methodology walkthrough, and the test suite.",
    ],
}

CLOSING = ("Khoj finds the engineers a keyword filter buries, and refuses the ones it would be "
           "fooled by, in about 40 seconds, with a reason for every pick.")


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


def main():
    prs = Presentation(TEMPLATE)
    slides = list(prs.slides)

    # Slide 1: identity labels
    for sh in slides[0].shapes:
        if sh.has_text_frame and sh.text_frame.text.strip() in IDENTITY:
            write_body(sh, [IDENTITY[sh.text_frame.text.strip()]], size=Pt(16))

    # Content slides: the title is the upper text box, the prompt box is the
    # lower one. Match the slide by its title text, then write into the LOWER box
    # (or a fresh box if the slide has only a title, like Architecture).
    for slide in slides[1:]:
        boxes = [sh for sh in slide.shapes
                 if sh.has_text_frame and sh.shape_type == MSO_SHAPE_TYPE.TEXT_BOX]
        if not boxes:
            continue
        boxes.sort(key=lambda s: s.top or 0)
        title = boxes[0].text_frame.text.strip()
        if title not in BODY:
            continue
        if len(boxes) >= 2:
            body_shape = boxes[-1]            # the lowest box is the prompt box
        else:
            body_shape = slide.shapes.add_textbox(Inches(0.4), Inches(1.7), Inches(9.3), Inches(3.3))
        n = len(BODY[title])
        write_body(body_shape, BODY[title], size=Pt(12 if n > 4 else 13))

    # Closing slide
    box = slides[-1].shapes.add_textbox(Inches(0.8), Inches(2.3), Inches(8.4), Inches(1.6))
    write_body(box, [CLOSING], size=Pt(18))

    prs.save(OUT)
    titles_ok = all(
        any(sh.has_text_frame and sh.text_frame.text.strip() in BODY for sh in s.shapes)
        for s in slides[1:10]
    )
    print(f"Saved {OUT} ({len(slides)} slides). Titles preserved: {titles_ok}.")


if __name__ == "__main__":
    main()
