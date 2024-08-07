from pathlib import Path

import click
from PIL import Image
from pdf2image import convert_from_path

from . import ute


def pdf_to_images(path: Path):
    pages = convert_from_path(path, 300)
    return pages


@click.group()
def cli():
    pass


@cli.command()
@click.argument("input-file", required=True)
@click.argument("output-file", required=True)
def translate_image(input_file: str, output_file: str):
    result = ute.translate_image(image=Image.open(input_file))
    result.save(output_file)


@cli.command()
@click.argument("input-file", required=True)
@click.argument("output-file", required=True)
def translate_pdf(input_file, output_file):
    input_path = Path(input_file)
    pages = pdf_to_images(path=input_path)
    ute.translate_pdf_pages(pages=pages, output=output_file)


@cli.command()
def serve():
    pass


if __name__ == "__main__":
    cli()
