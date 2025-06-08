// Content script for advanced features

// Visual overlay for element inspection
class ElementInspector {
  constructor() {
    this.overlay = null;
    this.tooltip = null;
    this.isActive = false;
  }
  
  activate() {
    this.isActive = true;
    this.createOverlay();
    document.addEventListener('mousemove', this.handleMouseMove.bind(this));
    document.addEventListener('click', this.handleClick.bind(this));
  }
  
  deactivate() {
    this.isActive = false;
    this.removeOverlay();
    document.removeEventListener('mousemove', this.handleMouseMove);
    document.removeEventListener('click', this.handleClick);
  }
  
  createOverlay() {
    this.overlay = document.createElement('div');
    this.overlay.style.cssText = `
      position: fixed;
      border: 2px solid #4285f4;
      background: rgba(66, 133, 244, 0.1);
      pointer-events: none;
      z-index: 10000;
      transition: all 0.1s ease;
    `;
    
    this.tooltip = document.createElement('div');
    this.tooltip.style.cssText = `
      position: fixed;
      background: #333;
      color: white;
      padding: 8px 12px;
      border-radius: 4px;
      font-size: 12px;
      font-family: monospace;
      z-index: 10001;
      pointer-events: none;
      max-width: 300px;
    `;
    
    document.body.appendChild(this.overlay);
    document.body.appendChild(this.tooltip);
  }
  
  removeOverlay() {
    if (this.overlay) this.overlay.remove();
    if (this.tooltip) this.tooltip.remove();
  }
  
  handleMouseMove(e) {
    if (!this.isActive) return;
    
    const element = document.elementFromPoint(e.clientX, e.clientY);
    if (!element) return;
    
    const rect = element.getBoundingClientRect();
    this.overlay.style.top = rect.top + 'px';
    this.overlay.style.left = rect.left + 'px';
    this.overlay.style.width = rect.width + 'px';
    this.overlay.style.height = rect.height + 'px';
    
    // Update tooltip
    const selector = this.getSelector(element);
    const styles = window.getComputedStyle(element);
    this.tooltip.innerHTML = `
      <div>${selector}</div>
      <div style="margin-top: 4px; color: #aaa;">
        ${Math.round(rect.width)} × ${Math.round(rect.height)}
      </div>
    `;
    
    this.tooltip.style.top = (e.clientY + 20) + 'px';
    this.tooltip.style.left = (e.clientX + 20) + 'px';
  }
  
  handleClick(e) {
    e.preventDefault();
    e.stopPropagation();
    
    const element = document.elementFromPoint(e.clientX, e.clientY);
    if (!element) return;
    
    const data = this.getElementData(element);
    chrome.runtime.sendMessage({
      type: 'element_selected',
      data: data
    });
    
    this.deactivate();
  }
  
  getSelector(element) {
    if (element.id) return `#${element.id}`;
    if (element.className) {
      const classes = element.className.split(' ').filter(c => c).join('.');
      return `${element.tagName.toLowerCase()}.${classes}`;
    }
    return element.tagName.toLowerCase();
  }
  
  getElementData(element) {
    const computed = window.getComputedStyle(element);
    const rect = element.getBoundingClientRect();
    
    // Extract all computed styles
    const styles = {};
    for (let i = 0; i < computed.length; i++) {
      const prop = computed[i];
      styles[prop] = computed.getPropertyValue(prop);
    }
    
    return {
      selector: this.getSelector(element),
      tagName: element.tagName,
      id: element.id,
      className: element.className,
      attributes: Array.from(element.attributes).map(attr => ({
        name: attr.name,
        value: attr.value
      })),
      rect: {
        top: rect.top,
        left: rect.left,
        width: rect.width,
        height: rect.height
      },
      computedStyles: styles,
      innerHTML: element.innerHTML,
      outerHTML: element.outerHTML
    };
  }
}

// CSS differ and live editor
class CSSLiveEditor {
  constructor() {
    this.styleSheet = null;
    this.originalStyles = new Map();
  }
  
  init() {
    // Create a style element for live edits
    const style = document.createElement('style');
    style.id = 'mcp-live-editor';
    document.head.appendChild(style);
    this.styleSheet = style.sheet;
  }
  
  addRule(selector, cssText) {
    try {
      const ruleIndex = this.styleSheet.insertRule(`${selector} { ${cssText} }`, this.styleSheet.cssRules.length);
      return ruleIndex;
    } catch (e) {
      console.error('Failed to add CSS rule:', e);
      return -1;
    }
  }
  
  removeRule(index) {
    try {
      this.styleSheet.deleteRule(index);
    } catch (e) {
      console.error('Failed to remove CSS rule:', e);
    }
  }
  
  captureOriginalStyles(selector) {
    const elements = document.querySelectorAll(selector);
    elements.forEach(el => {
      const computed = window.getComputedStyle(el);
      const styles = {};
      
      // Capture important properties
      const properties = [
        'display', 'position', 'width', 'height', 'margin', 'padding',
        'color', 'backgroundColor', 'font', 'border', 'transform'
      ];
      
      properties.forEach(prop => {
        styles[prop] = computed.getPropertyValue(prop);
      });
      
      this.originalStyles.set(el, styles);
    });
  }
  
  compareStyles(selector) {
    const elements = document.querySelectorAll(selector);
    const differences = [];
    
    elements.forEach(el => {
      const original = this.originalStyles.get(el);
      if (!original) return;
      
      const current = window.getComputedStyle(el);
      const diff = {};
      
      Object.keys(original).forEach(prop => {
        const currentValue = current.getPropertyValue(prop);
        if (original[prop] !== currentValue) {
          diff[prop] = {
            original: original[prop],
            current: currentValue
          };
        }
      });
      
      if (Object.keys(diff).length > 0) {
        differences.push({
          element: el,
          selector: this.getElementSelector(el),
          differences: diff
        });
      }
    });
    
    return differences;
  }
  
  getElementSelector(element) {
    if (element.id) return `#${element.id}`;
    
    let selector = element.tagName.toLowerCase();
    if (element.className) {
      selector += '.' + element.className.split(' ').filter(c => c).join('.');
    }
    
    // Add nth-child if needed
    const parent = element.parentElement;
    if (parent) {
      const index = Array.from(parent.children).indexOf(element);
      if (index > 0) {
        selector += `:nth-child(${index + 1})`;
      }
    }
    
    return selector;
  }
}

// Design comparison with visual diff
class DesignComparator {
  constructor() {
    this.comparisonMode = false;
    this.referenceImage = null;
  }
  
  async compareWithReference(referenceUrl) {
    // Create comparison overlay
    const overlay = document.createElement('div');
    overlay.style.cssText = `
      position: fixed;
      top: 0;
      left: 0;
      width: 100%;
      height: 100%;
      z-index: 9999;
      pointer-events: none;
    `;
    
    const img = document.createElement('img');
    img.src = referenceUrl;
    img.style.cssText = `
      position: absolute;
      top: 0;
      left: 0;
      opacity: 0.5;
      mix-blend-mode: difference;
    `;
    
    overlay.appendChild(img);
    document.body.appendChild(overlay);
    
    this.referenceImage = overlay;
  }
  
  toggleOpacity(value) {
    if (this.referenceImage) {
      this.referenceImage.querySelector('img').style.opacity = value;
    }
  }
  
  removeComparison() {
    if (this.referenceImage) {
      this.referenceImage.remove();
      this.referenceImage = null;
    }
  }
}

// Initialize components
const inspector = new ElementInspector();
const cssEditor = new CSSLiveEditor();
const comparator = new DesignComparator();

cssEditor.init();

// Listen for messages from background script
chrome.runtime.onMessage.addListener((request, sender, sendResponse) => {
  switch (request.type) {
    case 'activate_inspector':
      inspector.activate();
      sendResponse({ success: true });
      break;
      
    case 'inject_css':
      const ruleIndex = cssEditor.addRule(request.selector, request.css);
      sendResponse({ success: ruleIndex !== -1, ruleIndex });
      break;
      
    case 'capture_styles':
      cssEditor.captureOriginalStyles(request.selector);
      sendResponse({ success: true });
      break;
      
    case 'compare_styles':
      const differences = cssEditor.compareStyles(request.selector);
      sendResponse({ differences });
      break;
      
    case 'compare_design':
      comparator.compareWithReference(request.referenceUrl);
      sendResponse({ success: true });
      break;
      
    case 'toggle_comparison_opacity':
      comparator.toggleOpacity(request.value);
      sendResponse({ success: true });
      break;
      
    case 'remove_comparison':
      comparator.removeComparison();
      sendResponse({ success: true });
      break;
      
    case 'get_page_metrics':
      const metrics = getPageMetrics();
      sendResponse(metrics);
      break;
  }
  
  return true; // Keep message channel open for async response
});

// Get page performance and design metrics
function getPageMetrics() {
  const metrics = {
    performance: {
      loadTime: performance.timing.loadEventEnd - performance.timing.navigationStart,
      domReady: performance.timing.domContentLoadedEventEnd - performance.timing.navigationStart,
      resources: performance.getEntriesByType('resource').map(r => ({
        name: r.name,
        duration: r.duration,
        size: r.transferSize
      }))
    },
    design: {
      fonts: getUsedFonts(),
      colors: getUsedColors(),
      spacings: getCommonSpacings(),
      breakpoints: detectBreakpoints()
    },
    accessibility: {
      contrastIssues: checkContrastIssues(),
      missingAltText: checkMissingAltText(),
      headingStructure: analyzeHeadingStructure()
    }
  };
  
  return metrics;
}

function getUsedFonts() {
  const fonts = new Set();
  const elements = document.querySelectorAll('*');
  
  elements.forEach(el => {
    const computed = window.getComputedStyle(el);
    const fontFamily = computed.fontFamily;
    if (fontFamily) {
      fonts.add(fontFamily);
    }
  });
  
  return Array.from(fonts);
}

function getUsedColors() {
  const colors = new Map();
  const elements = document.querySelectorAll('*');
  
  elements.forEach(el => {
    const computed = window.getComputedStyle(el);
    
    ['color', 'backgroundColor', 'borderColor'].forEach(prop => {
      const value = computed[prop];
      if (value && value !== 'rgba(0, 0, 0, 0)' && value !== 'transparent') {
        colors.set(value, (colors.get(value) || 0) + 1);
      }
    });
  });
  
  // Sort by usage frequency
  return Array.from(colors.entries())
    .sort((a, b) => b[1] - a[1])
    .map(([color, count]) => ({ color, count }));
}

function getCommonSpacings() {
  const spacings = new Map();
  const elements = document.querySelectorAll('*');
  
  elements.forEach(el => {
    const computed = window.getComputedStyle(el);
    
    ['margin', 'padding', 'gap'].forEach(prop => {
      ['Top', 'Right', 'Bottom', 'Left'].forEach(side => {
        const value = computed[prop + side] || computed[prop];
        if (value && value !== '0px') {
          spacings.set(value, (spacings.get(value) || 0) + 1);
        }
      });
    });
  });
  
  return Array.from(spacings.entries())
    .sort((a, b) => b[1] - a[1])
    .slice(0, 10)
    .map(([spacing, count]) => ({ spacing, count }));
}

function detectBreakpoints() {
  // Analyze media queries in stylesheets
  const breakpoints = new Set();
  
  Array.from(document.styleSheets).forEach(sheet => {
    try {
      Array.from(sheet.cssRules || []).forEach(rule => {
        if (rule.type === CSSRule.MEDIA_RULE) {
          const match = rule.conditionText.match(/\d+px/g);
          if (match) {
            match.forEach(bp => breakpoints.add(bp));
          }
        }
      });
    } catch (e) {
      // CORS restriction
    }
  });
  
  return Array.from(breakpoints).sort((a, b) => {
    return parseInt(a) - parseInt(b);
  });
}

function checkContrastIssues() {
  // Simplified contrast check
  const issues = [];
  const elements = document.querySelectorAll('*');
  
  elements.forEach(el => {
    const computed = window.getComputedStyle(el);
    const color = computed.color;
    const bgColor = computed.backgroundColor;
    
    if (color && bgColor && bgColor !== 'rgba(0, 0, 0, 0)') {
      // Here you would implement actual contrast calculation
      // For now, just flag potential issues
      if (el.textContent && el.textContent.trim()) {
        issues.push({
          element: el.tagName,
          selector: getElementSelector(el),
          color,
          backgroundColor: bgColor
        });
      }
    }
  });
  
  return issues.slice(0, 10); // Limit to first 10 issues
}

function checkMissingAltText() {
  const images = document.querySelectorAll('img:not([alt])');
  return Array.from(images).map(img => ({
    src: img.src,
    selector: getElementSelector(img)
  }));
}

function analyzeHeadingStructure() {
  const headings = document.querySelectorAll('h1, h2, h3, h4, h5, h6');
  const structure = [];
  let lastLevel = 0;
  
  headings.forEach(h => {
    const level = parseInt(h.tagName[1]);
    structure.push({
      level,
      text: h.textContent.trim(),
      skipLevel: level - lastLevel > 1
    });
    lastLevel = level;
  });
  
  return structure;
}

// Helper function to get element selector
function getElementSelector(element) {
  if (element.id) return `#${element.id}`;
  
  let selector = element.tagName.toLowerCase();
  if (element.className) {
    selector += '.' + element.className.split(' ').filter(c => c).join('.');
  }
  
  return selector;
}

// Export for use in popup or background script
window.MCPChromebridge = {
  inspector,
  cssEditor,
  comparator,
  getPageMetrics
};
