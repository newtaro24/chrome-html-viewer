#!/bin/bash
# Simple script to remind about generating PNG icons

echo "Please generate PNG icons from icon.svg using one of these methods:"
echo ""
echo "1. Using librsvg:"
echo "   brew install librsvg"
echo "   rsvg-convert -w 16 -h 16 icon.svg -o icon16.png"
echo "   rsvg-convert -w 48 -h 48 icon.svg -o icon48.png"
echo "   rsvg-convert -w 128 -h 128 icon.svg -o icon128.png"
echo ""
echo "2. Using ImageMagick:"
echo "   brew install imagemagick"
echo "   convert -resize 16x16 icon.svg icon16.png"
echo "   convert -resize 48x48 icon.svg icon48.png"
echo "   convert -resize 128x128 icon.svg icon128.png"
echo ""
echo "3. Using an online converter like https://cloudconvert.com/svg-to-png"
