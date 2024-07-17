import itertools
from pathlib import Path
from itertools import pairwise
from typing import Optional
from abc import ABC, abstractmethod

import cv2
import numpy as np
import pandas as pd
import deepl
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw
import pytesseract
from reportlab.pdfgen import canvas
from reportlab.lib.utils import ImageReader

from . import heuristics


FROM_LANGUAGE = "deu"
ROOT = Path(__file__).parent.parent


class Renderer(ABC):
    @abstractmethod
    def set_page(self, page: Image.Image):
        ...

    @abstractmethod
    def render_text(self, text: str, x: float, y: float, font_size: int):
        ...

    @abstractmethod
    def render_rect(self, left: float, right: float, top: float, bottom: float,
                    radius: int):
        ...


class PillowRenderer(Renderer):
    def __init__(self):
        self.draw: Optional[ImageDraw.ImageDraw] = None

    def set_page(self, page: Image.Image):
        self.draw = ImageDraw.Draw(page)

    def render_rect(self, left: float, right: float, top: float, bottom: float,
                    radius: int):
        assert self.draw

        self.draw.rounded_rectangle(
            xy=((left, top), (right, bottom)),
            fill=(255, 255, 255),
            radius=radius,
        )

    def render_text(self, text: str, x: float, y: float, font_size: int):
        assert self.draw

        font = ImageFont.load_default(font_size)
        self.draw.text(xy=(x, y), text=text, fill=(0, 0, 0), font=font)


class PDFRenderer(Renderer):
    def __init__(self, output_file: str):
        self.canvas = canvas.Canvas(output_file)
        self.page: Optional[Image.Image] = None

    def set_page(self, page: Image.Image):
        self.canvas.setPageSize((page.width, page.height))
        self.canvas.drawImage(ImageReader(page), x=0, y=0)
        self.page = page

    def render_rect(self, left: float, right: float, top: float, bottom: float,
                    radius: int):
        assert self.page
        x = left
        width = right - left
        height = bottom - top
        y = self.page.height - top - height

        self.canvas.setFillColorRGB(1, 1, 1)
        self.canvas.roundRect(
            x=x,
            y=y,
            width=width,
            height=height,
            radius=radius,
            stroke=0,
            fill=1,
        )

    def render_text(self, text: str, x: float, y: float, font_size: int):
        assert self.page

        self.canvas.setFillColorRGB(0, 0, 0)
        self.canvas.setFontSize(font_size)
        self.canvas.drawString(x, self.page.height - y - font_size, text)

    def save(self):
        self.canvas.save()

    def next_page(self):
        self.canvas.showPage()

def get_auth_key():
    with open(ROOT / "api_key.txt") as f:
        return f.read().strip()

translator = deepl.Translator(get_auth_key())


def draw_text(group: pd.DataFrame, text: str, renderer: Renderer):
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
        top: float = line.top.min()
        left: float = extent[0]
        right: float = max(extent[1], left + font.getlength(text))
        bottom: float = line.top.min() + font_size * 1.2
        renderer.render_rect(top=top, left=left, right=right, bottom=bottom,
                             radius=int(font_size * 0.2))
        renderer.render_text(
            x=line.left.min(),
            y=line.top.min(),
            text=text,
            font_size=font_size,
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


def ocr_page(page: Image.Image, renderer: Renderer):
    renderer.set_page(page)

    clean_image = page.copy()
    qrCodeDetector = cv2.QRCodeDetector()
    _, codes, _ = qrCodeDetector.detectAndDecode(np.array(page))
    for qrcode in ([] if codes is None else codes):
        left = qrcode[:, 0].min()
        right = qrcode[:, 0].max()
        top = qrcode[:, 1].min()
        bottom = qrcode[:, 1].max()
        width = right - left
        height = bottom - top
        draw = ImageDraw.Draw(clean_image)
        draw.rectangle((
            (left - width * 0.1, top - height * 0.1),
            (right + width * 0.1, bottom + height * 0.1)
        ), fill="white")

    # df = pd.read_csv("/tmp/test_data.csv")
    df = pytesseract.image_to_data(clean_image, lang=FROM_LANGUAGE,
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

    def filter_group(group):
        # Ignore vertical text for now. Usually it's not useful, just like a
        # serial number on the side.
        is_vertical = group[["left", "top"]].diff().dropna() \
            .apply(lambda row: abs(row.top) > abs(row.left), axis=1).median()
        if is_vertical:
            print("Ignoring vertical group", group)
        return not is_vertical

    def transform_group(group):
        print(group)
        group["line_num"] = list(recalculate_line_numbers(group))
        group.sort_values(by=["line_num", "word_num"], inplace=True)
        return group

    groups = [transform_group(g) for _, g in df.groupby("block_num")
              if filter_group(g)]
    groups = list(itertools.chain.from_iterable(split_group(g) for g in groups))

    texts = ["\n".join(" ".join(line.text) for _, line in g.groupby("line_num"))
             for g in groups]

    def transform_text(text: str):
        """
        Handle paragraphs separately for Deepl. It does not handle newlines well
        within paragraphs. It adds extra words. If the text is a paragraph,
        remove the newlines.
        """

        if heuristics.is_paragraph(text):
            text = "\n".join(line.strip() for line in text.split("\n"))

            # Join words broken onto two lines then join lines by spaces
            return text.replace("-\n", "").replace("\n", " " )

        return text

    texts = [transform_text(text) for text in texts]

    # texts = [" ".join(g["text"]) for g in groups]
    for g, t in zip(groups, texts):
        print(g)
        print(t)

    translations = translator.translate_text(texts, source_lang="de",
                                             target_lang="en-gb")
    translations = [result.text.replace("\n", " ") for result in translations]
    print(translations)

    for translation, group in zip(translations, groups):
        draw_text(group=group, text=translation, renderer=renderer)

    return page


def translate_pdf_pages(pages: Sequence[Image.Image], output_file: str):
    renderer = PDFRenderer(output_file=output_file)

    for page in pages:
        ocr_page(page=page, renderer=renderer)
        renderer.next_page()

    renderer.save()
