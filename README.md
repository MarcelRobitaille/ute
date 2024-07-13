# UTE

UTE (Universal Translation Engine) is a tool for translating images and documents into a different language.
It is similar to popular phone apps in that it overlays the translated text in the correct place.
All of the pieces of desktop software I have tried put the translation in a separate box
or do not properly overlay it onto the original image, making it hard to understand the structure of the document.
Unlike these phone apps, UTE is an open-source, embeddable engine, allowing it to be used in other tools.

## Roadmap

- [x] Engine and basic CLI
- [ ] Integration into [Paperless-ngx](https://github.com/paperless-ngx/paperless-ngx/discussions/269)
- [ ] Screen overlay to translate a region of your screen, like taking a screenshot
- [ ] Live screen overlay. Like above, but live instead of one time. This will probably require major performance improvements and diffing of the changed regions of the image

## Other todos

UTE is a work in progress.
For example, it only works with pre-straightened images.
This section tracks some general improvements that do not really fit as roadmap items.

- [ ] Performance (profiling or rewrite in not python)
- [ ] Better config handling
- [ ] Straighten
