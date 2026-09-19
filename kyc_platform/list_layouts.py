from pptx import Presentation
from pptx.enum.shapes import MSO_SHAPE_TYPE

def main():
    prs = Presentation("updated ppt.pptx")
    print(f"Available slide layouts ({len(prs.slide_layouts)}):")
    for i, layout in enumerate(prs.slide_layouts):
        print(f"  [{i}] {layout.name}")

if __name__ == "__main__":
    main()
