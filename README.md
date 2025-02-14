# UTE

UTE (Universal Translation Engine) is a tool for translating images and documents into a different language.
It is similar to popular phone apps in that it overlays the translated text in the correct place.
All of the pieces of desktop software I have tried put the translation in a separate box
or do not properly overlay it onto the original image, making it hard to understand the structure of the document.
Unlike these phone apps, UTE is an open-source, embeddable engine, allowing it to be used in other tools.

## How it works

The pipeline is essentially: [tesseract](https://github.com/tesseract-ocr/tesseract) (OCR) -> [Deepl API](https://www.deepl.com) -> annotate image/document.
Other translation services to come.

## Usage

Download the repo and install dependencies (proper packaging to come):
```bash
git clone https://github.com/MarcelRobitaille/ute.git
cd ute
pip install -r requirements.txt
```

Currently the command-line interface supports two commands.

```bash
python -m ute.ute translate-image <Source> <Destination>
python -m ute.ute translate-pdf <Source> <Destination>
```

Starting the REST API:
```bash
fastapi dev ute --app fastapi_app
```

Requirements that are not in pip
- poppler
- tesseract

## Roadmap

- [x] Engine and basic CLI
- [x] Rest API
- [ ] Integration into [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx/discussions/269)
- [ ] Other translation engines (like libretranslate)
- [ ] Screen overlay to translate a region of your screen, like taking a screenshot
- [ ] Live screen overlay. Like above, but live instead of one time. This will probably require major performance improvements and diffing of the changed regions of the image

## Other todos

UTE is a work in progress.
For example, it only works with pre-straightened (de-skewed) images.
This section tracks some general improvements that do not really fit as roadmap items.

- [ ] Performance (profiling or rewrite in not python)
- [ ] Better config handling
- [ ] Straighten (de-skew)
- [ ] Packaging in package repositories
