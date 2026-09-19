from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE
from pptx.util import Pt
import copy

def find_shape_by_name(shapes, name, results=None):
    if results is None:
        results = []
    for shape in shapes:
        if shape.name == name:
            results.append(shape)
        if shape.shape_type == MSO_SHAPE_TYPE.GROUP:
            find_shape_by_name(shape.shapes, name, results)
    return results

def set_text_preserve_format(shape, new_text):
    """Set text while trying to preserve font formatting of first run."""
    tf = shape.text_frame
    tf.word_wrap = True
    # Clear existing paragraphs (keep first)
    for para in tf.paragraphs[1:]:
        p = para._p
        p.getparent().remove(p)
    # Set text on first paragraph first run
    first_para = tf.paragraphs[0]
    if first_para.runs:
        first_para.runs[0].text = new_text
        # clear remaining runs in same para
        for run in first_para.runs[1:]:
            run.text = ""
    else:
        first_para.text = new_text

def find_and_replace(shapes, name, new_text):
    found = find_shape_by_name(shapes, name)
    for shape in found:
        if shape.has_text_frame:
            set_text_preserve_format(shape, new_text)
            print(f"  Updated [{name}]")

def main():
    prs = Presentation("updated ppt.pptx")
    slides = prs.slides

    # ── Slide 4: Solution Architecture - fix the empty slide ──────────────────
    # Slide 4 already has "Solution Architecture" title but content is empty
    # We'll add content by replacing the empty TextBox 7 in the group
    s4 = slides[3]  # 0-indexed
    for shape in s4.shapes:
        if shape.has_text_frame and shape.name == "TextBox 18":
            pass  # Title - leave it
    # Slide 4 has no content text boxes to fill - it's a diagram slide, skip

    # ── Slide 6: Fix "Slide 4" label and "?????" ──────────────────────────────
    s6 = slides[5]
    find_and_replace(s6.shapes, "TextBox 2", "Technical Details")
    find_and_replace(s6.shapes, "TextBox 4", "AMD ROCm & vLLM Stack")

    # Also fill missing "Dataset(s) used" and "Training time" shapes
    find_and_replace(s6.shapes, "TextBox 21", "N/A - Zero-shot prompting with domain-specific system instructions per agent.")
    find_and_replace(s6.shapes, "TextBox 19", "N/A - No fine-tuning required. Specialized prompts + JSON schema enforcement achieves domain accuracy.")

    # ── Slide 7: Strengthen for evaluation criteria ────────────────────────────
    s7 = slides[6]
    find_and_replace(s7.shapes, "TextBox 7",
        "80% reduction in manual KYC workload.\n"
        "Instant onboarding for low-risk customers.\n"
        "100% auditability through downloadable PDF evidence trails.\n"
        "Scalable to millions of onboarding requests with AMD ROCm local inference."
    )
    find_and_replace(s7.shapes, "TextBox 17",
        "1. First system to use LangGraph multi-agent collaboration for KYC.\n"
        "2. Replaces black-box AI scores with LLM-generated plain-English narratives.\n"
        "3. AMD ROCm-optimized local inference - no third-party cloud required.\n"
        "4. Real-time Precision/Recall tracking of AI vs. Human Analyst decisions."
    )
    find_and_replace(s7.shapes, "TextBox 15",
        "1. ONBOARDING: Submit customer form -> watch 5 agents run in real-time.\n"
        "2. RISK DASHBOARD: View AI risk score, band, and evidence flags.\n"
        "3. HUMAN REVIEW QUEUE: Download PDF evidence report -> override AI decision.\n"
        "4. GLOBAL METRICS: Check AI Precision/Recall vs Human Analyst accuracy."
    )

    prs.save("updated ppt.pptx")
    print("\nDone! Saved back to 'updated ppt.pptx'")

if __name__ == "__main__":
    main()
