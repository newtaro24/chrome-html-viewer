# Chrome HTML Viewer Icons

This directory contains the icon files for the Chrome extension.

## Current Files:
- `icon.svg` - Source SVG file for the icon

## Required PNG Files:
- `icon16.png` - 16x16 pixels (for browser toolbar)
- `icon48.png` - 48x48 pixels (for extension management page)
- `icon128.png` - 128x128 pixels (for Chrome Web Store)

## How to Generate PNG files:

### Option 1: Using librsvg (Recommended)
```bash
brew install librsvg
rsvg-convert -w 16 -h 16 icon.svg -o icon16.png
rsvg-convert -w 48 -h 48 icon.svg -o icon48.png
rsvg-convert -w 128 -h 128 icon.svg -o icon128.png
```

### Option 2: Using ImageMagick
```bash
brew install imagemagick
convert -resize 16x16 icon.svg icon16.png
convert -resize 48x48 icon.svg icon48.png
convert -resize 128x128 icon.svg icon128.png
```

### Option 3: Using online converter
Visit https://cloudconvert.com/svg-to-png or similar service to convert the SVG to PNG at different sizes.

## Icon Design
The icon features:
- Chrome browser colors (blue, red, yellow, green)
- A bridge/connection symbol in the center
- Represents the connection between Chrome and Claude Desktop
