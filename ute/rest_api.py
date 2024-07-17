import io

from PIL import Image
from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.responses import Response
import pdf2image

from .ute import translate_pdf_pages, ocr_page, PillowRenderer

app = FastAPI()

@app.post("/translate-image", response_class=Response,
          responses={200: {"content": {"image/png": {}}}})
async def translate_image(image: UploadFile = File(...)):
    contents = Image.open(io.BytesIO(await image.read()))
    output = io.BytesIO()

    ocr_page(page=contents, renderer=PillowRenderer()) \
        .save(output, format='PNG')

    return Response(content=output.getvalue(), media_type="image/png")


@app.post("/translate-pdf", response_class=Response,
          responses={200: {"content": {"application/pdf": {}}}})
async def translate_pdf(pdf: UploadFile = File(...)):
    contents = await pdf.read()

    try:
        pages = pdf2image.convert_from_bytes(contents, dpi=300)
    except:
        raise HTTPException(status_code=400,
                            detail="Could not extract PDF pages.")

    output = io.BytesIO()
    translate_pdf_pages(pages=pages, output=output)

    return Response(content=output.getvalue(), media_type="application/pdf")


__all__ = ("app",)
