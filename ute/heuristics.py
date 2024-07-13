def is_paragraph(text: str):
    """
    Handle paragraphs separately for Deepl. It does not handle newlines well
    within paragraphs. It adds extra words. This heuristic determines if a
    string is a paragraph or just some sparse words.
    """

    return len(text.split(" ")) >= 40
