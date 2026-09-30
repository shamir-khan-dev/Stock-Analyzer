/**
 * AlphaPulse Vision & TradeBot Controller
 */
class BotAndVisionManager {
  constructor(app) {
    this.app = app;
    this.lastVisionContext = null;

    // Elements
    this.dropzone = document.getElementById('pasteDropzone');
    this.dropzoneEmpty = document.getElementById('dropzoneEmpty');
    this.dropzonePreview = document.getElementById('dropzonePreview');
    this.previewImg = document.getElementById('pastedImgPreview');
    this.clearImgBtn = document.getElementById('clearImgBtn');
    this.fileInput = document.getElementById('fileInput');

    this.visionResults = document.getElementById('visionResults');
    this.visionBadge = document.getElementById('visionVerdictBadge');
    this.visionConf = document.getElementById('visionConfText');
    this.visionTrendTitle = document.getElementById('visionTrendTitle');
    this.visionBullets = document.getElementById('visionBullets');

    this.chatLog = document.getElementById('chatLog');
    this.chatForm = document.getElementById('chatForm');
    this.chatInput = document.getElementById('chatInput');

    this.initPasteEvents();
    this.initChatEvents();
  }

  initPasteEvents() {
    // 1. Listen for global window Ctrl+V paste
    window.addEventListener('paste', (e) => {
      const items = (e.clipboardData || (e.originalEvent && e.originalEvent.clipboardData)) ? (e.clipboardData || e.originalEvent.clipboardData).items : null;
      if (!items) return;
      for (const item of items) {
        if (item.type && item.type.indexOf('image') !== -1) {
          const blob = item.getAsFile();
          this.handleImageFile(blob);
          break;
        }
      }
    });

    // 2. Click on dropzone to upload file
    if (this.dropzone && this.fileInput) {
      this.dropzone.addEventListener('click', (e) => {
        if (e.target !== this.clearImgBtn) {
          this.fileInput.click();
        }
      });
    }

    if (this.fileInput) {
      this.fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files[0]) {
          this.handleImageFile(e.target.files[0]);
        }
      });
    }

    // 3. Drag & Drop events
    if (this.dropzone) {
      this.dropzone.addEventListener('dragover', (e) => {
        e.preventDefault();
        this.dropzone.classList.add('dragover');
      });

      this.dropzone.addEventListener('dragleave', () => {
        this.dropzone.classList.remove('dragover');
      });

      this.dropzone.addEventListener('drop', (e) => {
        e.preventDefault();
        this.dropzone.classList.remove('dragover');
        if (e.dataTransfer && e.dataTransfer.files && e.dataTransfer.files[0]) {
          this.handleImageFile(e.dataTransfer.files[0]);
        }
      });
    }

    // 4. Clear button
    if (this.clearImgBtn) {
      this.clearImgBtn.addEventListener('click', (e) => {
        e.stopPropagation();
        this.clearImage();
      });
    }
  }

  handleImageFile(file) {
    const reader = new FileReader();
    reader.onload = (e) => {
      const base64Data = e.target.result;
      this.displayImagePreview(base64Data);
      this.analyzeChartImage(base64Data);
    };
    reader.readAsDataURL(file);
  }

  displayImagePreview(base64Data) {
    this.previewImg.src = base64Data;
    this.dropzoneEmpty.classList.add('hidden');
    this.dropzonePreview.classList.remove('hidden');
  }

  clearImage() {
    this.previewImg.src = '';
    this.dropzoneEmpty.classList.remove('hidden');
    this.dropzonePreview.classList.add('hidden');
    this.visionResults.classList.add('hidden');
    this.lastVisionContext = null;
    this.fileInput.value = '';
  }

  async analyzeChartImage(base64Data) {
    this.visionResults.classList.remove('hidden');
    this.visionBadge.textContent = 'ANALYZING...';
    this.visionBadge.style.background = 'rgba(255, 255, 255, 0.1)';
    this.visionBadge.style.color = '#ffffff';
    this.visionConf.textContent = 'Processing Computer Vision...';
    this.visionBullets.innerHTML = '<li>Analyzing candlestick distribution and trend vectors...</li>';

    try {
      const res = await fetch('/api/vision/analyze-chart', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          image: base64Data,
          ticker: this.app.currentSymbol
        })
      });

      if (!res.ok) throw new Error('Vision analysis request failed');
      const data = await res.json();
      this.lastVisionContext = data;

      // Update vision results UI
      this.visionBadge.textContent = data.verdict;
      this.visionBadge.style.background = `${data.verdict_color}25`;
      this.visionBadge.style.color = data.verdict_color;
      this.visionConf.textContent = `${data.confidence_pct}% Confidence`;
      this.visionTrendTitle.textContent = data.trend_name || 'Price Structure Diagnostic';

      const findings = data.key_findings || [];
      this.visionBullets.innerHTML = findings.map(f => `<li>${f}</li>`).join('');

      // Notify TradeBot in chat
      this.appendBotMessage(`📷 <strong>Pasted Chart Diagnostic Complete!</strong><br>Verdict: <span style="color:${data.verdict_color}; font-weight:bold;">${data.verdict}</span> (${data.confidence_pct}% Confidence).<br>${data.trade_recommendation ? data.trade_recommendation.rationale : ''}`);
    } catch (err) {
      console.error(err);
      this.visionBadge.textContent = 'ANALYSIS ERROR';
      this.visionBullets.innerHTML = `<li class="text-danger">Failed to process image: ${err.message}</li>`;
    }
  }

  initChatEvents() {
    if (this.chatForm) {
      this.chatForm.addEventListener('submit', (e) => {
        e.preventDefault();
        const msg = this.chatInput ? this.chatInput.value.trim() : '';
        if (!msg) return;
        this.sendMessage(msg);
        if (this.chatInput) this.chatInput.value = '';
      });
    }

    // Support send button click directly as well
    const sendBtn = document.getElementById('sendBtn');
    if (sendBtn && this.chatInput && !this.chatForm) {
      sendBtn.addEventListener('click', (e) => {
        e.preventDefault();
        const msg = this.chatInput.value.trim();
        if (!msg) return;
        this.sendMessage(msg);
        this.chatInput.value = '';
      });
    }

    // Quick suggestion chips — support both .quick-chip and .prompt-chip
    document.querySelectorAll('.quick-chip, .prompt-chip').forEach(btn => {
      btn.addEventListener('click', () => {
        const sym = this.app.currentSymbol || 'NVDA';
        const queryTemplate = btn.dataset.query || btn.dataset.prompt || btn.textContent.trim();
        const query = queryTemplate.replace(/\bNVDA\b/g, sym).replace(/\bTSLA\b/g, sym);
        this.sendMessage(query);
      });
    });
  }

  appendUserMessage(text) {
    const div = document.createElement('div');
    div.className = 'chat-msg user-msg';
    div.innerHTML = `
      <div class="msg-avatar">👤</div>
      <div class="msg-bubble">${text}</div>
    `;
    this.chatLog.appendChild(div);
    this.chatLog.scrollTop = this.chatLog.scrollHeight;
  }

  appendBotMessage(htmlContent) {
    const div = document.createElement('div');
    div.className = 'chat-msg bot-msg';
    div.innerHTML = `
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble">${htmlContent}</div>
    `;
    this.chatLog.appendChild(div);
    this.chatLog.scrollTop = this.chatLog.scrollHeight;
  }

  async sendMessage(userText) {
    this.appendUserMessage(userText);

    // Show typing placeholder
    const typingId = 'typing-' + Date.now();
    const typingDiv = document.createElement('div');
    typingDiv.className = 'chat-msg bot-msg';
    typingDiv.id = typingId;
    typingDiv.innerHTML = `
      <div class="msg-avatar">🤖</div>
      <div class="msg-bubble text-secondary">TradeBot is thinking...</div>
    `;
    this.chatLog.appendChild(typingDiv);
    this.chatLog.scrollTop = this.chatLog.scrollHeight;

    try {
      const res = await fetch('/api/bot/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({
          message: userText,
          ticker: this.app.currentSymbol,
          chart_context: this.lastVisionContext
        })
      });

      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();

      if (!res.ok) throw new Error('Chat failed');
      const data = await res.json();

      // Format markdown-like bold and bullet text
      let formattedMsg = data.message
        .replace(/\n\n/g, '<br><br>')
        .replace(/\n/g, '<br>')
        .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
        .replace(/`([^`]+)`/g, '<kbd>$1</kbd>');

      this.appendBotMessage(formattedMsg);

      // If response references a different ticker, prompt or switch if desired
      if (data.referenced_ticker && data.referenced_ticker !== this.app.currentSymbol) {
        // Optionally switch symbol
      }
    } catch (err) {
      const typingEl = document.getElementById(typingId);
      if (typingEl) typingEl.remove();
      this.appendBotMessage(`<span class="text-danger">Error communicating with TradeBot: ${err.message}</span>`);
    }
  }
}

window.BotAndVisionManager = BotAndVisionManager;
