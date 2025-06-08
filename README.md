# Chrome HTML Viewer

A Chrome extension and MCP (Model Context Protocol) server that enables Claude Desktop to interact with Chrome browser resources, inspect web pages, and compare designs with Figma or local source code.

## Overview

This project provides a bridge between Claude Desktop and Chrome browser, allowing:
- Real-time HTML/CSS inspection
- Element style comparison
- Live CSS editing
- Design comparison with Figma
- Screenshot capture
- Performance metrics analysis

## Architecture

```
Claude Desktop → MCP Server (localhost:8765) → Chrome Extension → Web Page
     ↓                    ↓                         ↓
  Git/Figma          WebSocket/HTTP         Content Script
```

## Components

### 1. Chrome Extension
- **Background Script**: Manages WebSocket connection to MCP server
- **Content Script**: Handles page inspection and manipulation
- **Popup UI**: Provides user interface for manual control

### 2. MCP Server
- Python-based server implementing the MCP protocol
- WebSocket server for Chrome extension communication
- Tools for page inspection, style comparison, and design analysis

## Installation

### Chrome Extension

1. Clone this repository
2. Open Chrome and navigate to `chrome://extensions/`
3. Enable "Developer mode"
4. Click "Load unpacked" and select the `chrome-extension` directory

### MCP Server

1. Install dependencies:
   ```bash
   pip install websockets mcp
   ```

2. Configure Claude Desktop:
   - Add the MCP server configuration to your Claude Desktop settings
   - Update the path to `mcp_chrome_server.py`

3. Start the server:
   ```bash
   python mcp-server/mcp_chrome_server.py
   ```

## Usage

### Basic Commands in Claude Desktop

1. **Get current page information:**
   ```
   Claude: Show me the HTML structure and CSS of the current page
   ```

2. **Inspect specific elements:**
   ```
   Claude: What are the styles applied to .header-navigation?
   ```

3. **Compare with Figma design:**
   ```
   Claude: Compare this page with the Figma design at [URL]
   ```

4. **Live CSS editing:**
   ```
   Claude: Change the header background color to #f0f0f0
   ```

5. **Take screenshot:**
   ```
   Claude: Take a screenshot of the current page
   ```

## Features

- **Real-time Inspection**: Get complete HTML structure and computed styles
- **Element Inspector**: Visual element selection with hover effects
- **Style Comparison**: Track and compare style changes
- **Live CSS Injection**: Preview CSS changes in real-time
- **Design Overlay**: Compare with reference designs using transparency overlay
- **Performance Metrics**: Analyze load times, DOM complexity, and resource usage
- **Accessibility Analysis**: Check contrast ratios and heading structure

## Development

### Project Structure
```
chrome-html-viewer/
├── chrome-extension/
│   ├── manifest.json
│   ├── background.js
│   ├── content.js
│   ├── popup.html
│   ├── popup.js
│   └── icons/
├── mcp-server/
│   └── mcp_chrome_server.py
├── docs/
│   └── example_workflow.md
└── README.md
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## License

MIT License

## Acknowledgments

- Built using the MCP (Model Context Protocol) by Anthropic
- Chrome Extensions API
- WebSocket protocol for real-time communication
