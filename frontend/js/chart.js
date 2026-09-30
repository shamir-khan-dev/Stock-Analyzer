/**
 * AlphaPulse High-Performance Candlestick & Volume Canvas Chart
 */
class TechnicalChart {
  constructor(canvasId, tooltipId) {
    this.canvas = document.getElementById(canvasId);
    this.tooltip = document.getElementById(tooltipId);
    this.ctx = this.canvas.getContext('2d');
    this.bars = [];
    this.hoverIndex = -1;

    this.initEvents();
  }

  setData(chartData) {
    this.bars = chartData || [];
    this.render();
    // Re-render after a tick to ensure CSS layout has applied
    requestAnimationFrame(() => this.render());
  }

  showLoading() {
    if (!this.canvas) return;
    const ctx = this.ctx;
    const w = this.canvas.offsetWidth || 800;
    const h = this.canvas.offsetHeight || 380;
    this.canvas.width = w;
    this.canvas.height = h;
    ctx.clearRect(0, 0, w, h);
    ctx.fillStyle = 'rgba(87, 101, 126, 0.5)';
    ctx.font = '14px JetBrains Mono, monospace';
    ctx.textAlign = 'center';
    ctx.fillText('Loading chart data...', w / 2, h / 2);
    ctx.textAlign = 'left';
  }

  initEvents() {
    window.addEventListener('resize', () => this.render());

    this.canvas.addEventListener('mousemove', (e) => {
      if (!this.bars.length) return;
      const rect = this.canvas.getBoundingClientRect();
      const mouseX = e.clientX - rect.left;
      const mouseY = e.clientY - rect.top;

      const paddingLeft = 15;
      const paddingRight = 65;
      const chartWidth = (rect.width || 800) - paddingLeft - paddingRight;
      const barWidth = chartWidth / this.bars.length;

      const idx = Math.floor((mouseX - paddingLeft) / barWidth);
      if (idx >= 0 && idx < this.bars.length) {
        this.hoverIndex = idx;
        const b = this.bars[idx];
        const dateStr = new Date(b.time * 1000).toLocaleDateString();
        this.tooltip.classList.remove('hidden');
        this.tooltip.innerHTML = `
          <strong>${dateStr}</strong> | 
          O: <span>$${b.open.toFixed(2)}</span> 
          H: <span>$${b.high.toFixed(2)}</span> 
          L: <span>$${b.low.toFixed(2)}</span> 
          C: <span style="color:${b.close >= b.open ? '#00e676' : '#ff1744'}">$${b.close.toFixed(2)}</span> | 
          Vol: <span>${(b.volume).toLocaleString()}</span>
        `;
        this.render();
      }
    });

    this.canvas.addEventListener('mouseleave', () => {
      this.hoverIndex = -1;
      this.tooltip.classList.add('hidden');
      this.render();
    });
  }

  render() {
    if (!this.canvas) return;
    if (!this.bars.length) {
      this.showLoading();
      return;
    }

    const dpr = window.devicePixelRatio || 1;
    const rect = this.canvas.getBoundingClientRect();
    const width = Math.floor((rect.width > 0 ? rect.width : this.canvas.offsetWidth) || 800);
    const height = Math.floor((rect.height > 0 ? rect.height : this.canvas.offsetHeight) || 380);

    const targetW = Math.floor(width * dpr);
    const targetH = Math.floor(height * dpr);

    if (this.canvas.width !== targetW || this.canvas.height !== targetH) {
      this.canvas.width = targetW;
      this.canvas.height = targetH;
      this.ctx.setTransform(dpr, 0, 0, dpr, 0, 0);
    }

    const ctx = this.ctx;
    ctx.clearRect(0, 0, width, height);

    const padding = { top: 20, right: 65, bottom: 40, left: 15 };
    const chartW = width - padding.left - padding.right;
    const chartH = height - padding.top - padding.bottom;
    const volumeH = chartH * 0.22;
    const priceH = chartH * 0.78;

    // Find min and max price
    let minPrice = Infinity;
    let maxPrice = -Infinity;
    let maxVol = 0;

    for (const b of this.bars) {
      if (b.low < minPrice) minPrice = b.low;
      if (b.high > maxPrice) maxPrice = b.high;
      if (b.volume > maxVol) maxVol = b.volume;
    }

    const priceBuffer = (maxPrice - minPrice) * 0.05 || 1.0;
    minPrice -= priceBuffer;
    maxPrice += priceBuffer;

    const getY = (p) => padding.top + priceH - ((p - minPrice) / (maxPrice - minPrice)) * priceH;
    const getVolY = (v) => padding.top + chartH - (v / (maxVol || 1)) * volumeH;

    // Draw horizontal grid lines and price labels
    const gridSteps = 5;
    ctx.font = '10px JetBrains Mono, monospace';
    ctx.fillStyle = '#57657e';
    ctx.strokeStyle = 'rgba(255, 255, 255, 0.05)';
    ctx.lineWidth = 1;

    for (let i = 0; i <= gridSteps; i++) {
      const priceVal = minPrice + (i / gridSteps) * (maxPrice - minPrice);
      const y = getY(priceVal);

      ctx.beginPath();
      ctx.moveTo(padding.left, y);
      ctx.lineTo(width - padding.right, y);
      ctx.stroke();

      ctx.fillText(`$${priceVal.toFixed(2)}`, width - padding.right + 8, y + 3);
    }

    const barW = chartW / this.bars.length;
    const candleW = Math.max(2, barW * 0.65);

    // 1. Draw Volume Bars at bottom
    for (let i = 0; i < this.bars.length; i++) {
      const b = this.bars[i];
      const x = padding.left + i * barW + barW / 2;
      const vY = getVolY(b.volume);
      const isUp = b.close >= b.open;

      ctx.fillStyle = isUp ? 'rgba(0, 230, 118, 0.22)' : 'rgba(255, 23, 68, 0.22)';
      ctx.fillRect(x - candleW / 2, vY, candleW, (padding.top + chartH) - vY);
    }

    // 2. Draw Candlesticks (Wicks & Bodies)
    for (let i = 0; i < this.bars.length; i++) {
      const b = this.bars[i];
      const x = padding.left + i * barW + barW / 2;
      const isUp = b.close >= b.open;
      const color = isUp ? '#00e676' : '#ff1744';

      const highY = getY(b.high);
      const lowY = getY(b.low);
      const openY = getY(b.open);
      const closeY = getY(b.close);

      // Wick
      ctx.strokeStyle = color;
      ctx.lineWidth = 1.2;
      ctx.beginPath();
      ctx.moveTo(x, highY);
      ctx.lineTo(x, lowY);
      ctx.stroke();

      // Body
      const bodyTop = Math.min(openY, closeY);
      const bodyH = Math.max(2, Math.abs(openY - closeY));
      ctx.fillStyle = color;
      ctx.fillRect(x - candleW / 2, bodyTop, candleW, bodyH);
    }

    // 3. Draw EMA 21 line
    this.drawLine(ctx, this.bars, (b) => b.ema20, getY, '#00f2fe', 1.5, padding.left, barW);

    // 4. Draw EMA 50 line
    this.drawLine(ctx, this.bars, (b) => b.ema50, getY, '#ffb300', 1.5, padding.left, barW);

    // 5. Draw Target Levels Overlay (Entry, Stop Loss, Take Profit) if provided
    if (this.targetLevels) {
      const { entry, stopLoss, tp1, tp2, action = 'BUY' } = this.targetLevels;
      const isSell = action.includes('SELL');
      const isHold = action.includes('WAIT') || action.includes('HOLD');

      if (entry) {
        const lbl = isSell ? `SELL / EXIT NOW: $${entry.toFixed(2)}` : (isHold ? `PIVOT: $${entry.toFixed(2)}` : `BUY ENTRY: $${entry.toFixed(2)}`);
        const col = isSell ? '#ff5252' : (isHold ? '#b0bec5' : '#00e676');
        this.drawPriceLevel(ctx, entry, getY(entry), lbl, col, width, padding.right);
      }
      if (stopLoss) {
        const lbl = isSell ? `INVALIDATION STOP: $${stopLoss.toFixed(2)}` : `STOP-LOSS (SELL): $${stopLoss.toFixed(2)}`;
        const col = isSell ? '#ff7043' : '#ff1744';
        this.drawPriceLevel(ctx, stopLoss, getY(stopLoss), lbl, col, width, padding.right);
      }
      if (tp1) {
        const lbl = isSell ? `DOWNSIDE TARGET 1: $${tp1.toFixed(2)}` : (isHold ? `RESISTANCE 1: $${tp1.toFixed(2)}` : `TAKE PROFIT 1 (SELL): $${tp1.toFixed(2)}`);
        const col = isSell ? '#ffb300' : '#00f2fe';
        this.drawPriceLevel(ctx, tp1, getY(tp1), lbl, col, width, padding.right);
      }
      if (tp2) {
        const lbl = isSell ? `DOWNSIDE TARGET 2: $${tp2.toFixed(2)}` : (isHold ? `RESISTANCE 2: $${tp2.toFixed(2)}` : `TAKE PROFIT 2 (SELL): $${tp2.toFixed(2)}`);
        const col = isSell ? '#ffe082' : '#00b0ff';
        this.drawPriceLevel(ctx, tp2, getY(tp2), lbl, col, width, padding.right);
      }
    }

    // 6. Draw Crosshair if hovering
    if (this.hoverIndex >= 0 && this.hoverIndex < this.bars.length) {
      const hX = padding.left + this.hoverIndex * barW + barW / 2;
      ctx.strokeStyle = 'rgba(255, 255, 255, 0.25)';
      ctx.setLineDash([4, 4]);
      ctx.beginPath();
      ctx.moveTo(hX, padding.top);
      ctx.lineTo(hX, padding.top + chartH);
      ctx.stroke();
      ctx.setLineDash([]);
    }
  }

  setTargetLevels(levels) {
    this.targetLevels = levels;
    this.render();
  }

  drawPriceLevel(ctx, price, y, label, color, canvasWidth, paddingRight) {
    if (isNaN(y) || y < 0) return;
    ctx.strokeStyle = color;
    ctx.lineWidth = 1.5;
    ctx.setLineDash([6, 4]);
    ctx.beginPath();
    ctx.moveTo(15, y);
    ctx.lineTo(canvasWidth - paddingRight, y);
    ctx.stroke();
    ctx.setLineDash([]);

    // Draw Left-Side Label Pill (Action & Target Text)
    ctx.font = 'bold 10px JetBrains Mono, monospace';
    const textMetrics = ctx.measureText(label);
    const pillW = textMetrics.width + 14;
    const pillH = 18;
    const pillX = 20;
    const pillY = y - 9;

    ctx.fillStyle = 'rgba(10, 15, 29, 0.85)';
    ctx.beginPath();
    ctx.roundRect ? ctx.roundRect(pillX, pillY, pillW, pillH, 4) : ctx.rect(pillX, pillY, pillW, pillH);
    ctx.fill();
    ctx.strokeStyle = color;
    ctx.lineWidth = 1;
    ctx.stroke();

    ctx.fillStyle = color;
    ctx.fillText(label, pillX + 7, y + 4);

    // Draw Price Tag Badge on right axis
    ctx.fillStyle = color;
    ctx.fillRect(canvasWidth - paddingRight + 2, y - 9, 65, 18);
    ctx.fillStyle = '#0a0f1d';
    ctx.font = 'bold 10px JetBrains Mono, monospace';
    ctx.fillText(`$${price.toFixed(2)}`, canvasWidth - paddingRight + 7, y + 4);
  }

  drawLine(ctx, bars, valAccessor, getY, color, strokeWidth, padLeft, barW) {
    ctx.strokeStyle = color;
    ctx.lineWidth = strokeWidth;
    ctx.beginPath();
    let started = false;

    for (let i = 0; i < bars.length; i++) {
      const val = valAccessor(bars[i]);
      if (val !== null && val !== undefined) {
        const x = padLeft + i * barW + barW / 2;
        const y = getY(val);
        if (!started) {
          ctx.moveTo(x, y);
          started = true;
        } else {
          ctx.lineTo(x, y);
        }
      }
    }
    if (started) ctx.stroke();
  }

  resize() {
    if (!this.canvas) return;
    this.canvas.width = 0;
    this.canvas.height = 0;
    this.render();
  }
}


window.TechnicalChart = TechnicalChart;
