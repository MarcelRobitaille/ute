import pandas as pd


def is_paragraph(text: str):
    """
    Handle paragraphs separately for Deepl. It does not handle newlines well
    within paragraphs. It adds extra words. This heuristic determines if a
    string is a paragraph or just some sparse words.
    """

    return len(text.split(" ")) >= 40


def is_sparse(group: pd.DataFrame) -> bool:
    """
    Detect if a group is sparse text as opposed to a paragraph.
    """
    return group.word_num.max() < 5


def filter_group(group):
    """
    Ignore vertical text for now. Usually it's not useful, just like a
    serial number on the side.
    """

    def is_vertical(group):
        if 0 == len(group):
            return False
        if 1 == len(group):
            return group.iloc[0].height / group.iloc[0].width > 10
        return group[["left", "top"]].diff().dropna() \
            .apply(lambda row: abs(row.top) > abs(row.left), axis=1).median()

    result = not is_vertical(group)
    if not result:
        print(f"WARN: Ignoring group '{' '.join(group.text)}'")
    return result
