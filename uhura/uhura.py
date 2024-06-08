import sys
import itertools
from pathlib import Path
from typing import cast
from itertools import pairwise

import click
import numpy as np
import pandas as pd
import deepl
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import pytesseract
from pdf2image import convert_from_path


FROM_LANGUAGE = "deu"
ROOT = Path(__file__).parent.parent


def get_auth_key():
    with open(ROOT / "api_key.txt") as f:
        return f.read().strip()

# font = ImageFont.truetype("sans-serif.ttf", 16)
font = ImageFont.load_default(16)
translator = deepl.Translator(get_auth_key())

def pdf_to_images(path: Path):
    pages = convert_from_path(path, 500)
    return pages


def draw_text(group: pd.DataFrame, text: str, draw: ImageDraw.ImageDraw):
    font_size = group["height"].mean()
    font = ImageFont.load_default(font_size)

    lines = [line for _, line in group.groupby("line_num")]
    line_extents = [(line.left.min(), max(seg.left + seg.width for _, seg in line.iterrows()))
                    for line in lines]
    line_widths = [line[1] - line[0] for line in line_extents]

    def split_into_lines(line_widths, words):
        if 1 >= len(line_widths):
            return [" ".join(words)]
        for i in range(len(words)):
            if font.getlength(" ".join(words[:i+1])) > line_widths[0]:
                return [
                    " ".join(words[:i]),
                    *split_into_lines(line_widths=line_widths[1:], words=words[i:]),
                ]
        return [" ".join(words)]

    text_lines = split_into_lines(line_widths=line_widths, words=text.split(" "))
    for text, line, extent in itertools.zip_longest(text_lines, lines, line_extents):
        text = text or ""
        top = line.top.min()
        left = extent[0]
        right = max(extent[1], left + font.getlength(text))
        bottom = line.top.min() + font_size * 1.2
        draw.rounded_rectangle(
            xy=[(left, top), (right, bottom)],
            fill=(255, 255, 255),
            radius=int(font_size * 0.2),
        )
        draw.text(
            xy=(line.left.min(), line.top.min()),
            text=text,
            fill=(0, 0, 0),
            font=font,
        )


def split_group(group: pd.DataFrame):
    result = []

    for _, item in group.iterrows():
        if not result:
            result.append([item])
            continue

        for candidate in result:
            candidate_left = candidate[0].left
            candidate_right = candidate[-1].left + candidate[-1].width
            candidate_width = candidate_right - candidate_left
            if item.left < candidate_left + candidate_width * 1.5:
                candidate.append(item)
                break
        else:
            result.append([item])

    return [pd.DataFrame(r) for r in result]



def ocr_page(page: Image.Image):
    # df = pd.read_csv("/tmp/test_data.csv")
    df = pytesseract.image_to_data(page, lang=FROM_LANGUAGE,
                                   output_type=pytesseract.Output.DATAFRAME)
    df.to_csv("/tmp/test_data.csv", index=False)
    assert {1} == set(df["page_num"])
    df.drop(columns="page_num", inplace=True)

    df.drop(index=df[
        df.text.isnull() | df.text.map(lambda t: "" == str(t).strip())
    ].index, inplace=True)

    print(df.to_string())

    def recalculate_line_numbers(group):
        line_num = group.iloc[0].line_num
        yield line_num
        for (i, prev_row), (_, row) in pairwise(group.iterrows()):
            # if row.line_num > prev_row.line_num:
            if row.top > prev_row.top + prev_row.height * 0.5:
                line_num += 1
            yield line_num

    def transform_group(group):
        print(group)
        group["line_num"] = list(recalculate_line_numbers(group))
        group.sort_values(by=["line_num", "word_num"], inplace=True)
        return group

    groups = [transform_group(g) for _, g in df.groupby("block_num")]
    groups = list(itertools.chain.from_iterable(split_group(g) for g in groups))

    texts = ["\n".join(" ".join(line.text) for _, line in g.groupby("line_num"))
             for g in groups]
    # texts = [" ".join(g["text"]) for g in groups]
    for g, t in zip(groups, texts):
        print(g)
        print(t)

    translations = translator.translate_text(texts, source_lang="de",
                                             target_lang="en-gb")
    translations = [result.text.replace("\n", " ") for result in translations]
    print(translations)

    draw = ImageDraw.Draw(page)
    for translation, group in zip(translations, groups):
        draw_text(group=group, text=translation, draw=draw)

    return page

@click.group()
def main():
    pass


@main.command()
@click.argument("file")
def translate_pdf(file):
    path = Path(file)
    pages = pdf_to_images(path=path)
    # for i, page in enumerate(pages):
    #     ocr_page(page)
    #     page.save(f"/tmp/uhura/{path.name}_page{i}.png")
    pages = [ocr_page(page) for page in pages]
    pages[0].save("/tmp/test.pdf", "PDF", resolution=100.0, save_all=True,
                  append_images=pages[1:])


if __name__ == "__main__":
    main()

# ocr_page(Image.open("/tmp/zoll.pdf_page0.png"))
