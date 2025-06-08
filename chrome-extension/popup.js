// Popup script for Chrome extension

let connectionStatus = false;

// Check connection status
function checkConnection() {
  chrome.runtime.sendMessage({ type: 'check_connection' }, (response) => {
    if (chrome.runtime.lastError) {
      console.error('Connection check error:', chrome.runtime.lastError);
      updateConnectionStatus(false);
      return;
    }
    updateConnectionStatus(response && response.connected);
  });
}

function updateConnectionStatus(connected) {
  connectionStatus = connected;
  const statusDot = document.getElementById('statusDot');
  const statusText = document.getElementById('statusText');
  
  if (connected) {
    statusDot.classList.add('connected');
    statusText.textContent = 'Connected';
  } else {
    statusDot.classList.remove('connected');
    statusText.textContent = 'Disconnected';
  }
  
  // Enable/disable buttons based on connection
  document.querySelectorAll('button').forEach(btn => {
    if (btn.id !== 'reconnect') {
      btn.disabled = !connected;
    }
  });
}

// Add log entry
function addLog(message) {
  const log = document.getElementById('log');
  const entry = document.createElement('div');
  const time = new Date().toLocaleTimeString();
  entry.textContent = `[${time}] ${message}`;
  log.appendChild(entry);
  log.scrollTop = log.scrollHeight;
  
  // Keep only last 10 entries
  while (log.children.length > 10) {
    log.removeChild(log.firstChild);
  }
}

// Initialize popup
document.addEventListener('DOMContentLoaded', () => {
  checkConnection();
  
  // Delay loading metrics to give content script time to initialize
  setTimeout(() => {
    loadMetrics();
  }, 500);
  
  // Check connection every 2 seconds
  setInterval(checkConnection, 2000);
  
  // Button handlers
  document.getElementById('inspectElement').addEventListener('click', async () => {
    addLog('要素検査モードを開始');
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, { type: 'activate_inspector' }, (response) => {
      if (response && response.success) {
        window.close(); // Close popup to allow interaction with page
      }
    });
  });
  
  document.getElementById('captureStyles').addEventListener('click', async () => {
    addLog('スタイルを記録中...');
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, { 
      type: 'capture_styles',
      selector: '*' // Capture all elements
    }, (response) => {
      if (response && response.success) {
        addLog('スタイルの記録が完了しました');
      }
    });
  });
  
  document.getElementById('compareStyles').addEventListener('click', async () => {
    addLog('スタイルを比較中...');
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, {
      type: 'compare_styles',
      selector: '*'
    }, (response) => {
      if (response && response.differences) {
        const count = response.differences.length;
        addLog(`${count}個の要素に変更が見つかりました`);
        
        // Send to MCP server
        chrome.runtime.sendMessage({
          type: 'send_to_mcp',
          data: {
            type: 'style_differences',
            differences: response.differences
          }
        });
      }
    });
  });
  
  document.getElementById('takeScreenshot').addEventListener('click', () => {
    addLog('スクリーンショットを撮影中...');
    
    chrome.runtime.sendMessage({ type: 'take_screenshot' }, (response) => {
      if (response && response.success) {
        addLog('スクリーンショットを保存しました');
      }
    });
  });
  
  // Overlay controls
  const overlayToggle = document.getElementById('overlayToggle');
  const opacitySlider = document.getElementById('opacitySlider');
  const opacityValue = document.getElementById('opacityValue');
  
  overlayToggle.addEventListener('change', async (e) => {
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    
    if (e.target.checked) {
      // For demo, use a placeholder reference image
      chrome.tabs.sendMessage(tab.id, {
        type: 'compare_design',
        referenceUrl: 'data:image/png;base64,iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChwGA60e6kgAAAABJRU5ErkJggg=='
      });
      addLog('デザイン比較モードを有効化');
    } else {
      chrome.tabs.sendMessage(tab.id, {
        type: 'remove_comparison'
      });
      addLog('デザイン比較モードを無効化');
    }
  });
  
  opacitySlider.addEventListener('input', async (e) => {
    const value = e.target.value;
    opacityValue.textContent = `${value}%`;
    
    const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
    chrome.tabs.sendMessage(tab.id, {
      type: 'toggle_comparison_opacity',
      value: value / 100
    });
  });
});

// Load page metrics
async function loadMetrics() {
  const [tab] = await chrome.tabs.query({ active: true, currentWindow: true });
  
  chrome.tabs.sendMessage(tab.id, { type: 'get_page_metrics' }, (response) => {
    if (chrome.runtime.lastError) {
      console.log('Metrics not available yet:', chrome.runtime.lastError.message);
      return;
    }
    
    if (response) {
      // Update load time
      if (response.performance && response.performance.loadTime) {
        document.getElementById('loadTime').textContent = 
          `${Math.round(response.performance.loadTime)}ms`;
      }
      
      // Count DOM elements
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.querySelectorAll('*').length
      }, (results) => {
        if (chrome.runtime.lastError) {
          console.log('Script execution error:', chrome.runtime.lastError);
          return;
        }
        if (results && results[0]) {
          document.getElementById('domElements').textContent = results[0].result;
        }
      });
      
      // Count CSS rules
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => {
          let count = 0;
          Array.from(document.styleSheets).forEach(sheet => {
            try {
              count += sheet.cssRules.length;
            } catch (e) {}
          });
          return count;
        }
      }, (results) => {
        if (chrome.runtime.lastError) {
          console.log('Script execution error:', chrome.runtime.lastError);
          return;
        }
        if (results && results[0]) {
          document.getElementById('cssRules').textContent = results[0].result;
        }
      });
      
      // Count images
      chrome.scripting.executeScript({
        target: { tabId: tab.id },
        func: () => document.querySelectorAll('img').length
      }, (results) => {
        if (chrome.runtime.lastError) {
          console.log('Script execution error:', chrome.runtime.lastError);
          return;
        }
        if (results && results[0]) {
          document.getElementById('images').textContent = results[0].result;
        }
      });
    }
  });
}

// Listen for messages from content script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  if (request.type === 'element_selected') {
    addLog(`要素を選択: ${request.data.selector}`);
    
    // Send to MCP server
    chrome.runtime.sendMessage({
      type: 'send_to_mcp',
      data: {
        type: 'element_data',
        element: request.data
      }
    });
  }
});
