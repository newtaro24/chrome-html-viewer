// WebSocket connection to MCP Server
let ws = null;
let reconnectInterval = null;

function connectToMCPServer() {
  if (ws && ws.readyState === WebSocket.OPEN) return;
  
  ws = new WebSocket('ws://localhost:8765');
  
  ws.onopen = () => {
    console.log('Connected to MCP Server');
    clearInterval(reconnectInterval);
    ws.send(JSON.stringify({ type: 'chrome_extension_connected' }));
  };
  
  ws.onmessage = async (event) => {
    const message = JSON.parse(event.data);
    console.log('Received from MCP:', message);
    
    switch (message.type) {
      case 'get_page_info':
        await getPageInfo(message.tabId);
        break;
      case 'get_element_styles':
        await getElementStyles(message.tabId, message.selector);
        break;
      case 'get_all_styles':
        await getAllStyles(message.tabId);
        break;
      case 'inject_css':
        await injectCSS(message.tabId, message.css);
        break;
      case 'get_screenshot':
        await getScreenshot(message.tabId);
        break;
    }
  };
  
  ws.onerror = (error) => {
    console.error('WebSocket error:', error);
  };
  
  ws.onclose = () => {
    console.log('Disconnected from MCP Server');
    // Reconnect after 5 seconds
    reconnectInterval = setInterval(connectToMCPServer, 5000);
  };
}

// Get page information including HTML and computed styles
async function getPageInfo(tabId) {
  try {
    const [tab] = tabId ? 
      await chrome.tabs.query({ active: true, currentWindow: true, id: tabId }) :
      await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;
    
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        // Get all stylesheets
        const stylesheets = Array.from(document.styleSheets).map(sheet => {
          try {
            return {
              href: sheet.href,
              rules: Array.from(sheet.cssRules || []).map(rule => rule.cssText)
            };
          } catch (e) {
            return { href: sheet.href, error: 'CORS blocked' };
          }
        });
        
        // Get inline styles
        const inlineStyles = Array.from(document.querySelectorAll('[style]')).map(el => ({
          selector: el.tagName + (el.id ? `#${el.id}` : '') + (el.className ? `.${el.className.split(' ').join('.')}` : ''),
          style: el.getAttribute('style')
        }));
        
        return {
          url: window.location.href,
          title: document.title,
          html: document.documentElement.outerHTML,
          stylesheets,
          inlineStyles,
          viewport: {
            width: window.innerWidth,
            height: window.innerHeight
          }
        };
      }
    });
    
    if (results[0].result) {
      ws.send(JSON.stringify({
        type: 'page_info',
        data: results[0].result
      }));
    }
  } catch (error) {
    console.error('Error getting page info:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: error.message
    }));
  }
}

// Get computed styles for specific elements
async function getElementStyles(tabId, selector) {
  try {
    const [tab] = tabId ? 
      await chrome.tabs.query({ active: true, currentWindow: true, id: tabId }) :
      await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;
    
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: (sel) => {
        const elements = document.querySelectorAll(sel);
        return Array.from(elements).map(el => {
          const computed = window.getComputedStyle(el);
          const rect = el.getBoundingClientRect();
          
          // Extract key style properties
          const styles = {};
          const properties = [
            'display', 'position', 'width', 'height', 'margin', 'padding',
            'color', 'backgroundColor', 'font', 'fontSize', 'fontWeight',
            'border', 'borderRadius', 'boxShadow', 'opacity', 'transform'
          ];
          
          properties.forEach(prop => {
            styles[prop] = computed.getPropertyValue(prop);
          });
          
          return {
            tagName: el.tagName,
            id: el.id,
            className: el.className,
            rect: {
              top: rect.top,
              left: rect.left,
              width: rect.width,
              height: rect.height
            },
            computedStyles: styles,
            innerHTML: el.innerHTML.substring(0, 100) + '...'
          };
        });
      },
      args: [selector]
    });
    
    if (results[0].result) {
      ws.send(JSON.stringify({
        type: 'element_styles',
        selector,
        data: results[0].result
      }));
    }
  } catch (error) {
    console.error('Error getting element styles:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: error.message
    }));
  }
}

// Get all styles from the page
async function getAllStyles(tabId) {
  try {
    const [tab] = tabId ? 
      await chrome.tabs.query({ active: true, currentWindow: true, id: tabId }) :
      await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;
    
    const results = await chrome.scripting.executeScript({
      target: { tabId: tab.id },
      func: () => {
        const allStyles = [];
        
        // Collect all CSS rules
        Array.from(document.styleSheets).forEach(sheet => {
          try {
            Array.from(sheet.cssRules || []).forEach(rule => {
              if (rule.selectorText) {
                allStyles.push({
                  selector: rule.selectorText,
                  styles: rule.style.cssText,
                  source: sheet.href || 'inline'
                });
              }
            });
          } catch (e) {
            console.log('Cannot access stylesheet:', sheet.href);
          }
        });
        
        return allStyles;
      }
    });
    
    if (results[0].result) {
      ws.send(JSON.stringify({
        type: 'all_styles',
        data: results[0].result
      }));
    }
  } catch (error) {
    console.error('Error getting all styles:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: error.message
    }));
  }
}

// Inject CSS into the page
async function injectCSS(tabId, css) {
  try {
    const [tab] = tabId ? 
      await chrome.tabs.query({ active: true, currentWindow: true, id: tabId }) :
      await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;
    
    await chrome.scripting.insertCSS({
      target: { tabId: tab.id },
      css: css
    });
    
    ws.send(JSON.stringify({
      type: 'css_injected',
      success: true
    }));
  } catch (error) {
    console.error('Error injecting CSS:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: error.message
    }));
  }
}

// Take screenshot
async function getScreenshot(tabId) {
  try {
    const [tab] = tabId ? 
      await chrome.tabs.query({ active: true, currentWindow: true, id: tabId }) :
      await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (!tab) return;
    
    const dataUrl = await chrome.tabs.captureVisibleTab(null, { format: 'png' });
    
    ws.send(JSON.stringify({
      type: 'screenshot',
      data: dataUrl
    }));
  } catch (error) {
    console.error('Error taking screenshot:', error);
    ws.send(JSON.stringify({
      type: 'error',
      message: error.message
    }));
  }
}

// Listen for messages from popup or content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.type) {
    case 'check_connection':
      sendResponse({ connected: ws && ws.readyState === WebSocket.OPEN });
      break;
      
    case 'send_to_mcp':
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify(request.data));
        sendResponse({ success: true });
      } else {
        sendResponse({ success: false, error: 'Not connected to MCP server' });
      }
      break;
      
    case 'take_screenshot':
      getScreenshot();
      sendResponse({ success: true });
      break;
      
    case 'element_selected':
      if (ws && ws.readyState === WebSocket.OPEN) {
        ws.send(JSON.stringify({
          type: 'element_data',
          element: request.data
        }));
      }
      break;
  }
  
  return true; // Keep message channel open for async response
});

// Listen for tab updates
chrome.tabs.onUpdated.addListener((tabId, changeInfo, tab) => {
  if (changeInfo.status === 'complete' && ws && ws.readyState === WebSocket.OPEN) {
    ws.send(JSON.stringify({
      type: 'tab_updated',
      tabId,
      url: tab.url,
      title: tab.title
    }));
  }
});

// Initialize connection
connectToMCPServer();
