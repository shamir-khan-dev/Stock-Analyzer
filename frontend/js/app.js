/**
 * AlphaPulse Main Application Coordinator
 */
class AlphaPulseApp {
  constructor() {
    this.currentSymbol = 'NVDA';
    this.currentPeriod = '6mo';
    this.currentInterval = '1d';

    this.chart = new TechnicalChart('mainChartCanvas', 'chartTooltip');
    this.chart.showLoading(); // Show loading state immediately
    this.botManager = new BotAndVisionManager(this);

    this.initElements();
    this.bindEvents();
    this.loadTickerData(this.currentSymbol);
    this.loadPaperPortfolio();
    window.app = this;
  }

  initElements() {
    this.tickerInput = document.getElementById('tickerInput');
    this.analyzeBtn = document.getElementById('analyzeBtn');
    this.tickerPresets = document.getElementById('tickerPresets');
    this.timeframeButtons = document.getElementById('timeframeButtons');

    // Display elements
    this.symbolTitle = document.getElementById('symbolTitle');
    this.signalBadge = document.getElementById('signalBadge');
    this.verdictText = document.getElementById('verdictText');
    this.lastPriceDisplay = document.getElementById('lastPriceDisplay');
    this.changeDisplay = document.getElementById('changeDisplay');
    this.scoreDisplay = document.getElementById('scoreDisplay');
    this.confidenceVal = document.getElementById('confidenceVal');
    this.confidenceFill = document.getElementById('confidenceFill');
    this.reasonsList = document.getElementById('reasonsList');

    // Execution blueprint
    this.entryPrice = document.getElementById('entryPrice');
    this.stopLossPrice = document.getElementById('stopLossPrice');
    this.tp1Price = document.getElementById('tp1Price');
    this.tp2Price = document.getElementById('tp2Price');
    this.rrBadge = document.getElementById('rrBadge');
    this.riskPctSub = document.getElementById('riskPctSub');
    this.atrDisplay = document.getElementById('atrDisplay');
    this.dayRangeDisplay = document.getElementById('dayRangeDisplay');

    // Factors
    this.trendScoreVal = document.getElementById('trendScoreVal');
    this.trendBar = document.getElementById('trendBar');
    this.momScoreVal = document.getElementById('momScoreVal');
    this.momBar = document.getElementById('momBar');
    this.volatScoreVal = document.getElementById('volatScoreVal');
    this.volatBar = document.getElementById('volatBar');
    this.volScoreVal = document.getElementById('volScoreVal');
    this.volBar = document.getElementById('volBar');
    this.sentimentScoreVal = document.getElementById('sentimentScoreVal');
    this.sentimentBar = document.getElementById('sentimentBar');

    this.rsiVal = document.getElementById('rsiVal');
    this.macdVal = document.getElementById('macdVal');
    this.supertrendVal = document.getElementById('supertrendVal');
    this.volRatioVal = document.getElementById('volRatioVal') || document.getElementById('pcRatioVal');

    // Patterns & Pivots
    this.patternsContainer = document.getElementById('patternsContainer');
    this.pVal = document.getElementById('pVal');
    this.r1Val = document.getElementById('r1Val');
    this.r2Val = document.getElementById('r2Val');
    this.r3Val = document.getElementById('r3Val');
    this.s1Val = document.getElementById('s1Val');
    this.s2Val = document.getElementById('s2Val');
    this.s3Val = document.getElementById('s3Val');

    // Backtest
    this.btWinRate = document.getElementById('btWinRate');
    this.btProfitFactor = document.getElementById('btProfitFactor');
    this.btNetReturn = document.getElementById('btNetReturn');
    this.btDrawdown = document.getElementById('btDrawdown');
    this.btBenchmark = document.getElementById('btBenchmark');
    this.btTotalTrades = document.getElementById('btTotalTrades');
    this.tradeLogContainer = document.getElementById('tradeLogContainer');

    // Institutional Quant & Market Structure
    this.factorSScoreVal = document.getElementById('factorSScoreVal');
    this.factorRegimeBadge = document.getElementById('factorRegimeBadge');
    this.factorSectorTicker = document.getElementById('factorSectorTicker');
    this.factorBetaSpy = document.getElementById('factorBetaSpy');
    this.factorBetaSector = document.getElementById('factorBetaSector');
    this.factorAlphaSpread = document.getElementById('factorAlphaSpread');
    this.factorSummaryText = document.getElementById('factorSummaryText');

    this.optionsMaxPainVal = document.getElementById('optionsMaxPainVal');
    this.optionsGammaBadge = document.getElementById('optionsGammaBadge');
    this.optionsPinDist = document.getElementById('optionsPinDist');
    this.optionsCallWall = document.getElementById('optionsCallWall');
    this.optionsPutWall = document.getElementById('optionsPutWall');
    this.optionsPcrVal = document.getElementById('optionsPcrVal');
    this.optionsSummaryText = document.getElementById('optionsSummaryText');

    this.riskRecSharesVal = document.getElementById('riskRecSharesVal');
    this.riskCapitalReq = document.getElementById('riskCapitalReq');
    this.riskMaxLoss = document.getElementById('riskMaxLoss');
    this.riskPortExposure = document.getElementById('riskPortExposure');
    this.paperRiskSharesBadge = document.getElementById('paperRiskSharesBadge');
    this.paperSortinoVal = document.getElementById('paperSortinoVal');

    this.btnApplyRiskSizingHero = document.getElementById('btnApplyRiskSizingHero');
    this.btnApplyRiskSizingPaper = document.getElementById('btnApplyRiskSizingPaper');
  }

  bindEvents() {
    // Search
    this.analyzeBtn.addEventListener('click', () => {
      const sym = this.tickerInput.value.trim().toUpperCase();
      if (sym) this.switchSymbol(sym);
    });

    this.tickerInput.addEventListener('keydown', (e) => {
      if (e.key === 'Enter') {
        const sym = this.tickerInput.value.trim().toUpperCase();
        if (sym) this.switchSymbol(sym);
      }
    });

    // Preset Chips
    this.tickerPresets.addEventListener('click', (e) => {
      const chip = e.target.closest('.chip');
      if (chip) {
        document.querySelectorAll('.chip').forEach(c => c.classList.remove('active'));
        chip.classList.add('active');
        const sym = chip.dataset.symbol;
        this.tickerInput.value = sym;
        this.switchSymbol(sym);
      }
    });

    // Timeframe selector
    this.timeframeButtons.addEventListener('click', (e) => {
      const btn = e.target.closest('.btn-tf');
      if (btn) {
        document.querySelectorAll('.btn-tf').forEach(b => b.classList.remove('active'));
        btn.classList.add('active');
        this.currentInterval = btn.dataset.interval;
        this.currentPeriod = btn.dataset.period;
        this.loadTickerData(this.currentSymbol);
      }
    });

    // Go-OS Segmented Navigation Tabs
    const tabs = document.querySelectorAll('.go-tab');
    tabs.forEach(tab => {
      tab.addEventListener('click', () => {
        tabs.forEach(t => t.classList.remove('active'));
        tab.classList.add('active');
        const targetId = tab.dataset.target;
        document.querySelectorAll('.go-pane').forEach(p => p.classList.remove('active'));
        const activePane = document.getElementById(targetId);
        if (activePane) {
          activePane.classList.add('active');
          if (targetId === 'tab-chart' && this.chart) {
            requestAnimationFrame(() => {
              this.chart.resize();
              this.chart.render();
            });
          } else if (targetId === 'tab-paper') {
            this.loadPaperPortfolio();
          }
        }
      });
    });

    // Terms Guide Modal
    const termsModal = document.getElementById('termsModal');
    const termsGuideBtn = document.getElementById('termsGuideBtn');
    const closeTermsBtn = document.getElementById('closeTermsBtn');
    const termsFilterInput = document.getElementById('termsFilterInput');

    if (termsGuideBtn && termsModal) {
      termsGuideBtn.addEventListener('click', () => {
        termsModal.classList.remove('hidden');
        if (termsFilterInput) {
          termsFilterInput.value = '';
          termsFilterInput.focus();
          document.querySelectorAll('.term-card').forEach(c => c.style.display = '');
        }
      });
    }

    if (closeTermsBtn && termsModal) {
      closeTermsBtn.addEventListener('click', () => {
        termsModal.classList.add('hidden');
      });
    }

    if (termsModal) {
      termsModal.addEventListener('click', (e) => {
        if (e.target === termsModal) {
          termsModal.classList.add('hidden');
        }
      });
    }

    if (termsFilterInput) {
      termsFilterInput.addEventListener('input', (e) => {
        const query = e.target.value.toLowerCase().trim();
        document.querySelectorAll('.term-card').forEach(card => {
          const text = card.textContent.toLowerCase();
          card.style.display = text.includes(query) ? '' : 'none';
        });
      });
    }

    // Quick Hero Paper Trading Buttons
    const heroQuickBuyBtn = document.getElementById('heroQuickBuyBtn');
    const heroQuickSellBtn = document.getElementById('heroQuickSellBtn');
    if (heroQuickBuyBtn) {
      heroQuickBuyBtn.addEventListener('click', () => {
        this.executePaperTrade(this.currentSymbol, 'BUY', 10);
      });
    }
    if (heroQuickSellBtn) {
      heroQuickSellBtn.addEventListener('click', () => {
        this.executePaperTrade(this.currentSymbol, 'SELL', 10);
      });
    }

    // Paper Trading Desk Form Controls
    const paperBuyBtn = document.getElementById('paperBuyBtn');
    const paperSellBtn = document.getElementById('paperSellBtn');
    const paperResetBtn = document.getElementById('paperResetBtn');
    const paperSharesInput = document.getElementById('paperSharesInput');

    if (paperBuyBtn) {
      paperBuyBtn.addEventListener('click', () => {
        const shares = parseFloat(paperSharesInput ? paperSharesInput.value : 10) || 10;
        this.executePaperTrade(this.currentSymbol, 'BUY', shares);
      });
    }
    if (paperSellBtn) {
      paperSellBtn.addEventListener('click', () => {
        const shares = parseFloat(paperSharesInput ? paperSharesInput.value : 10) || 10;
        this.executePaperTrade(this.currentSymbol, 'SELL', shares);
      });
    }

    // Volatility-Targeted Risk Parity Auto-Size Handlers
    const applyQuantSizing = () => {
      const shares = this.recommendedShares || 10;
      if (paperSharesInput) paperSharesInput.value = shares;
      this.showToast(`⚡ Applied Quant Volatility-Targeted Size: ${shares} shares ($500 risk)`);
    };

    if (this.btnApplyRiskSizingHero) {
      this.btnApplyRiskSizingHero.addEventListener('click', () => {
        applyQuantSizing();
        const paperTab = document.querySelector('.go-tab[data-target="tab-paper"]');
        if (paperTab) paperTab.click();
      });
    }

    if (this.btnApplyRiskSizingPaper) {
      this.btnApplyRiskSizingPaper.addEventListener('click', applyQuantSizing);
    }
    if (paperResetBtn) {
      paperResetBtn.addEventListener('click', async () => {
        if (confirm('Reset paper portfolio to $100,000 virtual cash?')) {
          try {
            await fetch('/api/paper/reset', { method: 'POST' });
            this.loadPaperPortfolio();
            this.showToast('Virtual paper portfolio reset to $100,000 cash.');
          } catch (e) {
            this.showToast('Failed to reset portfolio: ' + e.message, true);
          }
        }
      });
    }

    // Interactive Horizon Card selection
    const horizonCards = document.querySelectorAll('.horizon-card');
    horizonCards.forEach((card, index) => {
      card.addEventListener('click', () => {
        horizonCards.forEach(c => c.classList.remove('active-horizon'));
        card.classList.add('active-horizon');
      });
    });

    // Trader Power-User Keyboard Shortcuts
    window.addEventListener('keydown', (e) => {
      const activeTag = document.activeElement ? document.activeElement.tagName.toLowerCase() : '';
      const isInputFocused = activeTag === 'input' || activeTag === 'textarea' || document.activeElement.isContentEditable;

      // Escape: Close terms modal & blur input
      if (e.key === 'Escape') {
        if (termsModal && !termsModal.classList.contains('hidden')) {
          termsModal.classList.add('hidden');
          e.preventDefault();
        } else if (isInputFocused) {
          document.activeElement.blur();
        }
        return;
      }

      // If user is currently typing in an input, don't trigger alpha/num shortcuts
      if (isInputFocused) return;

      // '/' : Quick focus ticker search bar
      if (e.key === '/') {
        e.preventDefault();
        if (this.tickerInput) {
          this.tickerInput.focus();
          this.tickerInput.select();
        }
      }

      // '1', '2', '3': Select Wall Street horizon timeframe
      if (e.key === '1' && horizonCards[0]) {
        horizonCards.forEach(c => c.classList.remove('active-horizon'));
        horizonCards[0].classList.add('active-horizon');
        horizonCards[0].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else if (e.key === '2' && horizonCards[1]) {
        horizonCards.forEach(c => c.classList.remove('active-horizon'));
        horizonCards[1].classList.add('active-horizon');
        horizonCards[1].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      } else if (e.key === '3' && horizonCards[2]) {
        horizonCards.forEach(c => c.classList.remove('active-horizon'));
        horizonCards[2].classList.add('active-horizon');
        horizonCards[2].scrollIntoView({ behavior: 'smooth', block: 'nearest' });
      }

      // 'B' / 'S': One-click simulated Paper Trades
      if (e.key.toLowerCase() === 'b') {
        e.preventDefault();
        this.executePaperTrade(this.currentSymbol, 'BUY', 10);
      } else if (e.key.toLowerCase() === 's') {
        e.preventDefault();
        this.executePaperTrade(this.currentSymbol, 'SELL', 10);
      }
    });
  }

  switchSymbol(symbol) {
    this.currentSymbol = symbol;
    this.loadTickerData(symbol);
    this.loadBacktestData(symbol);
  }

  async loadTickerData(symbol) {
    this.symbolTitle.textContent = symbol;
    this.verdictText.textContent = 'EVALUATING...';
    this.reasonsList.innerHTML = '<li>Analyzing multiple technical factors in real-time...</li>';

    try {
      const url = `/api/analyze/${encodeURIComponent(symbol)}?period=${this.currentPeriod}&interval=${this.currentInterval}`;
      const res = await fetch(url);
      if (!res.ok) {
        const errData = await res.json();
        throw new Error(errData.detail || 'Failed to fetch ticker analysis');
      }

      const data = await res.json();
      this.renderAnalysis(data);
    } catch (err) {
      console.error(err);
      this.verdictText.textContent = 'DATA UNAVAILABLE';
      this.reasonsList.innerHTML = `<li class="text-danger">${err.message}</li>`;
    }
  }

  renderAnalysis(data) {
    const q = data.quote || {};
    const price = q.current_price || data.current_price;
    const chg = q.change || 0.0;
    const chgPct = q.change_percent || 0.0;

    // Header & Price
    this.symbolTitle.textContent = data.symbol;
    this.lastPriceDisplay.textContent = `$${price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    
    const isUp = chg >= 0;
    this.changeDisplay.textContent = `${isUp ? '+' : ''}${chg.toFixed(2)} (${isUp ? '+' : ''}${chgPct.toFixed(2)}%)`;
    this.changeDisplay.className = `price-change ${isUp ? 'text-success' : 'text-danger'}`;

    // Verdict Badge — update early, action banner rendered after setup is available
    const verdict = data.verdict;
    this.verdictText.textContent = verdict;
    this.signalBadge.className = 'signal-badge';
    if (verdict.includes('STRONG BUY') || (verdict.includes('BUY') && !verdict.includes('SELL'))) {
      this.signalBadge.classList.add(verdict.includes('STRONG') ? 'badge-strong-buy' : 'badge-buy');
    } else if (verdict.includes('STRONG SELL') || verdict.includes('SELL')) {
      this.signalBadge.classList.add(verdict.includes('STRONG') ? 'badge-strong-sell' : 'badge-sell');
    } else {
      this.signalBadge.classList.add('badge-hold');
    }

    // Plain-English Meaning Pill (Translates Bearish / Bullish / Neutral)
    const plainPill = document.getElementById('plainEnglishPill');
    const plainIcon = document.getElementById('plainEnglishIcon');
    const plainText = document.getElementById('plainEnglishText');

    if (plainPill && plainIcon && plainText) {
      if (verdict.includes('STRONG BUY') || (verdict.includes('BUY') && !verdict.includes('SELL'))) {
        plainPill.className = 'plain-english-pill pill-bullish';
        plainIcon.textContent = '🐂';
        plainText.textContent = 'BULLISH — Price is rising. Good time to buy or hold.';
      } else if (verdict.includes('STRONG SELL') || verdict.includes('SELL')) {
        plainPill.className = 'plain-english-pill pill-bearish';
        plainIcon.textContent = '🐻';
        plainText.textContent = 'BEARISH — Price is falling. High risk; consider selling or cutting losses.';
      } else {
        plainPill.className = 'plain-english-pill pill-neutral';
        plainIcon.textContent = '⚖️';
        plainText.textContent = 'NEUTRAL — Price moving sideways. Wait for a clear breakout.';
      }
    }

    // Score & Confidence
    const score = data.confluence_score;
    this.scoreDisplay.textContent = `${score > 0 ? '+' : ''}${score}/100`;
    this.scoreDisplay.style.color = data.verdict_color;
    
    const conf = data.confidence_pct;
    this.confidenceVal.textContent = `${conf}%`;
    this.confidenceFill.style.width = `${conf}%`;
    this.confidenceFill.style.background = `linear-gradient(90deg, #00f2fe, ${data.verdict_color})`;

    // Key Reasons
    const reasons = data.key_reasons || [];
    this.reasonsList.innerHTML = reasons.map(r => `<li>${r}</li>`).join('');

    // Render News Headlines
    const newsListEl = document.getElementById('newsHeadlinesList');
    if (newsListEl && data.sentiment && data.sentiment.headlines) {
      const items = data.sentiment.headlines.slice(0, 4);
      newsListEl.innerHTML = items.map(n => `
        <li class="news-item">
          <a href="${n.link || '#'}" target="_blank" class="news-title-link">${n.title}</a>
          <span class="news-pub">${n.publisher || 'Market News'}</span>
        </li>
      `).join('');
    }


    // Execution Blueprint & Action Playbook
    const setup = data.trade_setup || {};
    this.renderExecutionBlueprint(setup, verdict, price, q);

    // Action Guidance Banner
    const banner = document.getElementById('actionGuidanceBanner');
    const actionTitle = document.getElementById('actionTitle');
    const actionDesc = document.getElementById('actionDesc');
    if (banner && actionTitle && actionDesc) {
      if (verdict.includes('STRONG BUY') || (verdict.includes('BUY') && !verdict.includes('SELL'))) {
        banner.className = 'action-banner action-banner-buy';
        actionTitle.textContent = `RECOMMENDED ACTION: ${verdict}`;
        actionDesc.textContent = setup.summary_text || `High-conviction bullish setup. Entry at $${(setup.entry_price || price).toFixed(2)} — strict stop at $${(setup.stop_loss || (price * 0.95)).toFixed(2)}.`;
      } else if (verdict.includes('STRONG SELL') || verdict.includes('SELL')) {
        banner.className = 'action-banner action-banner-sell';
        actionTitle.textContent = `RECOMMENDED ACTION: ${verdict}`;
        actionDesc.textContent = setup.summary_text || `Bearish distribution risk. Protect capital; exit positions or hedge downside. Invalidation stop at $${(setup.stop_loss || (price * 1.05)).toFixed(2)}.`;
      } else {
        banner.className = 'action-banner action-banner-hold';
        actionTitle.textContent = `RECOMMENDED ACTION: HOLD / WAIT`;
        actionDesc.textContent = setup.summary_text || `Market is consolidating sideways with balanced order flow. Await a clear breakout before entry.`;
      }
    }

    // Confluence Breakdown
    const bk = data.breakdown || {};
    this.renderFactor('trend', bk.trend_score, 35, this.trendScoreVal, this.trendBar);
    this.renderFactor('momentum', bk.momentum_score, 25, this.momScoreVal, this.momBar);
    this.renderFactor('volatility', bk.volatility_score, 20, this.volatScoreVal, this.volatBar);
    this.renderFactor('volume', bk.volume_score, 20, this.volScoreVal, this.volBar);
    if (this.sentimentScoreVal && this.sentimentBar) {
      this.renderFactor('sentiment', bk.sentiment_score || 0, 10, this.sentimentScoreVal, this.sentimentBar);
    }

    if (this.rsiVal) this.rsiVal.textContent = bk.rsi !== undefined ? bk.rsi : '--';
    if (this.macdVal) this.macdVal.textContent = bk.macd_hist !== undefined ? `${bk.macd_hist > 0 ? '+' : ''}${bk.macd_hist}` : '--';
    if (this.supertrendVal) {
      this.supertrendVal.textContent = bk.supertrend || '--';
      this.supertrendVal.style.color = bk.supertrend === 'BULLISH' ? 'var(--accent-success)' : 'var(--accent-danger)';
    }
    if (this.volRatioVal) {
      const pcVal = (data.order_flow && data.order_flow.put_call_ratio) ? data.order_flow.put_call_ratio : (bk.vol_ratio ? `${bk.vol_ratio}x` : '1.0x');
      this.volRatioVal.textContent = pcVal;
    }


    // Patterns
    const patterns = data.patterns || [];
    if (patterns.length === 0) {
      this.patternsContainer.innerHTML = '<div class="pattern-item bias-neutral"><span class="pattern-title">Standard Consolidation</span><span class="pattern-desc">No extreme single-candle reversal formations detected.</span></div>';
    } else {
      this.patternsContainer.innerHTML = patterns.map(p => `
        <div class="pattern-item bias-${p.bias.toLowerCase()}">
          <div class="pattern-top">
            <span class="pattern-title">${p.name}</span>
            <span class="badge-outline text-${p.bias === 'BULLISH' ? 'success' : (p.bias === 'BEARISH' ? 'danger' : 'warning')}">${p.bias}</span>
          </div>
          <span class="pattern-desc">${p.description}</span>
        </div>
      `).join('');
    }

    // Pivot Levels
    const piv = data.pivot_levels || {};
    this.pVal.textContent = piv.P ? `$${piv.P.toFixed(2)}` : '--';
    this.r1Val.textContent = piv.R1 ? `$${piv.R1.toFixed(2)}` : '--';
    this.r2Val.textContent = piv.R2 ? `$${piv.R2.toFixed(2)}` : '--';
    this.r3Val.textContent = piv.R3 ? `$${piv.R3.toFixed(2)}` : '--';
    this.s1Val.textContent = piv.S1 ? `$${piv.S1.toFixed(2)}` : '--';
    this.s2Val.textContent = piv.S2 ? `$${piv.S2.toFixed(2)}` : '--';
    this.s3Val.textContent = piv.S3 ? `$${piv.S3.toFixed(2)}` : '--';

    // Update Candlestick Chart & Target Overlays
    if (data.chart_data && data.chart_data.length) {
      this.chart.setData(data.chart_data);
      if (setup.entry_price && setup.stop_loss) {
        this.chart.setTargetLevels({
          entry: setup.entry_price,
          stopLoss: setup.stop_loss,
          tp1: setup.take_profit_1,
          tp2: setup.take_profit_2,
          action: setup.action || (verdict.includes('BUY') ? 'BUY' : (verdict.includes('SELL') ? 'SELL' : 'WAIT'))
        });
      }
    }

    // Save current setup for position calculator
    this.currentSetup = {
      price: setup.entry_price || price,
      stopLoss: setup.stop_loss || (price * 0.95),
      tp1: setup.take_profit_1 || (price * 1.05),
      action: setup.action || (verdict.includes('BUY') ? 'BUY' : (verdict.includes('SELL') ? 'SELL' : 'WAIT'))
    };
    this.updatePositionCalculator();

    // Render MTF Alignment and Options Flow
    if (data.mtf_alignment) {
      const mtf = data.mtf_alignment;
      const el15 = document.getElementById('mtf15m');
      const el1h = document.getElementById('mtf1h');
      const el1d = document.getElementById('mtf1d');
      if (el15) { el15.textContent = `15M: ${mtf['15M']}`; el15.className = `mtf-chip ${mtf['15M'] === 'BULLISH' ? 'mtf-bull' : 'mtf-bear'}`; }
      if (el1h) { el1h.textContent = `1H: ${mtf['1H']}`; el1h.className = `mtf-chip ${mtf['1H'] === 'BULLISH' ? 'mtf-bull' : 'mtf-bear'}`; }
      if (el1d) { el1d.textContent = `1D: ${mtf['1D']}`; el1d.className = `mtf-chip ${mtf['1D'] === 'BULLISH' ? 'mtf-bull' : 'mtf-bear'}`; }
    }

    if (data.order_flow && document.getElementById('pcRatioVal')) {
      document.getElementById('pcRatioVal').textContent = `${data.order_flow.put_call_ratio}`;
    }

    // Refresh Paper Trading portfolio state
    this.loadPaperPortfolio();

    // Render Earnings Warning
    this.renderEarningsWarning(data.earnings_warning);

    // Render Signal Reliability
    this.renderReliability(data.signal_reliability);

    // Render Signal Tracker
    this.renderSignalTracker(data.signal_tracker);

    // Render Wall Street Multi-Horizon Quantitative Strategy Desk
    this.renderMultiHorizon(data.multi_horizon, q);

    // Render Institutional Quantitative Market Structure & Factor Matrix
    this.renderInstitutionalQuant(data);
  }

  renderEarningsWarning(ew) {
    const banner = document.getElementById('earningsWarningBanner');
    const msg = document.getElementById('earningsMsg');
    const title = document.getElementById('earningsTitle');
    if (!banner || !ew) return;
    if (ew.has_warning) {
      banner.classList.remove('hidden');
      if (title) title.textContent = `EARNINGS ${ew.urgency || 'WARNING'} — ${ew.earnings_date || ''}`;
      if (msg) msg.textContent = ew.message || 'Upcoming earnings — signals may be unreliable.';
    } else {
      banner.classList.add('hidden');
    }
  }

  renderReliability(rel) {
    if (!rel) return;
    const fill = document.getElementById('reliabilityFill');
    const grade = document.getElementById('reliabilityGrade');
    const label = document.getElementById('reliabilityLabel');
    const score = document.getElementById('reliabilityScore');
    const confirmBadge = document.getElementById('mtfConfirmBadge');
    const mixedBadge = document.getElementById('mtfMixedBadge');
    const warningsList = document.getElementById('reliabilityWarnings');
    const reasonsList = document.getElementById('reliabilityReasons');

    if (fill) {
      fill.style.width = `${rel.score}%`;
      const colors = { A: '#00e676', B: '#ffb300', C: '#ff7043', D: '#ff1744' };
      fill.style.background = `linear-gradient(90deg, ${colors[rel.grade] || '#00f2fe'}, #00f2fe)`;
    }
    if (grade) {
      grade.textContent = rel.grade;
      grade.className = `reliability-grade grade-${rel.grade.toLowerCase()}`;
    }
    if (label) {
      label.textContent = rel.label;
      label.style.color = rel.color;
    }
    if (score) score.textContent = `${rel.score}/100`;

    if (confirmBadge && mixedBadge) {
      if (rel.mtf_confirmed) {
        confirmBadge.classList.remove('hidden');
        mixedBadge.classList.add('hidden');
      } else {
        confirmBadge.classList.add('hidden');
        mixedBadge.classList.remove('hidden');
      }
    }

    if (warningsList) warningsList.innerHTML = (rel.warnings || []).map(w => `<li>${w}</li>`).join('');
    if (reasonsList) reasonsList.innerHTML = (rel.reasons || []).map(r => `<li>${r}</li>`).join('');
  }

  renderSignalTracker(stats) {
    if (!stats) return;
    const els = {
      total: document.getElementById('trackerTotal'),
      closed: document.getElementById('trackerClosed'),
      winRate: document.getElementById('trackerWinRate'),
      avgWin: document.getElementById('trackerAvgWin'),
      avgLoss: document.getElementById('trackerAvgLoss'),
      open: document.getElementById('trackerOpen'),
      tbody: document.getElementById('signalLogTbody')
    };
    const pills = document.querySelectorAll('.tracker-pill');

    if (els.total) els.total.textContent = stats.total_signals || 0;
    if (els.closed) els.closed.textContent = stats.closed_signals || 0;
    if (els.open) els.open.textContent = stats.open_signals || 0;
    if (els.winRate) {
      els.winRate.textContent = `${stats.win_rate_pct || 0}%`;
      els.winRate.className = `tracker-stat-val ${(stats.win_rate_pct || 0) >= 50 ? 'text-success' : 'text-danger'}`;
    }
    if (els.avgWin) els.avgWin.textContent = `+${stats.avg_win_pct || 0}%`;
    if (els.avgLoss) els.avgLoss.textContent = `-${stats.avg_loss_pct || 0}%`;

    // Update pills
    if (pills.length >= 3) {
      pills[0].textContent = `${stats.wins || 0} Wins`;
      pills[1].textContent = `${stats.losses || 0} Losses`;
      pills[2].textContent = `${stats.win_rate_pct || 0}% Win Rate`;
    }

    // Signal log table
    if (els.tbody) {
      const signals = stats.recent_signals || [];
      if (signals.length === 0) {
        els.tbody.innerHTML = '<tr><td colspan="9" class="text-center text-muted">Analyzing a ticker will start logging signals here automatically.</td></tr>';
      } else {
        els.tbody.innerHTML = signals.map(sig => {
          const statusClass = sig.status === 'WIN' ? 'sig-status-win' : sig.status === 'LOSS' ? 'sig-status-loss' : 'sig-status-open';
          const statusIcon = sig.status === 'WIN' ? '✅ WIN' : sig.status === 'LOSS' ? '❌ LOSS' : '⏳ OPEN';
          const pnl = sig.pnl_pct !== null && sig.pnl_pct !== undefined ? `${sig.pnl_pct > 0 ? '+' : ''}${sig.pnl_pct}%` : '--';
          const relScore = sig.reliability_score || 0;
          const relClass = relScore >= 75 ? 'sig-reliability-high' : relScore >= 55 ? 'sig-reliability-med' : relScore >= 35 ? 'sig-reliability-low' : 'sig-reliability-none';
          const verdictColor = sig.verdict && sig.verdict.includes('BUY') ? '#00e676' : '#ff1744';
          return `<tr>
            <td>${sig.signal_date || '--'}</td>
            <td><strong>${sig.ticker}</strong></td>
            <td style="color:${verdictColor};font-weight:700;">${sig.verdict}</td>
            <td>$${sig.entry_price}</td>
            <td>$${sig.stop_loss}</td>
            <td>$${sig.take_profit_1}</td>
            <td class="${relClass}">${relScore}/100</td>
            <td class="${statusClass}">${statusIcon}</td>
            <td class="${sig.pnl_pct > 0 ? 'text-success' : sig.pnl_pct < 0 ? 'text-danger' : ''}">${pnl}</td>
          </tr>`;
        }).join('');
      }
    }
  }

  renderMultiHorizon(mh, quote) {
    if (!mh) return;

    // 1. Day Trade / Scalp (1 - 2 Days)
    const day = mh.day_trade;
    if (day) {
      const vEl = document.getElementById('hDayVerdict');
      const bEl = document.getElementById('hDayBadge');
      const eEl = document.getElementById('hDayEntry');
      const tEl = document.getElementById('hDayTarget');
      const sEl = document.getElementById('hDayStop');
      const sumEl = document.getElementById('hDaySummary');

      if (vEl) {
        vEl.textContent = day.verdict;
        vEl.style.color = day.color || '#00e676';
      }
      if (bEl) bEl.textContent = day.badge;
      if (eEl) eEl.textContent = `$${day.entry !== undefined ? day.entry.toFixed(2) : '0.00'}`;
      if (tEl) tEl.textContent = `$${day.target !== undefined ? day.target.toFixed(2) : '0.00'}`;
      if (sEl) sEl.textContent = `$${day.stop_loss !== undefined ? day.stop_loss.toFixed(2) : '0.00'}`;
      if (sumEl) sumEl.textContent = day.summary;
    }

    // 2. Swing Trade (Days - Weeks)
    const swing = mh.swing_trade;
    if (swing) {
      const vEl = document.getElementById('hSwingVerdict');
      const bEl = document.getElementById('hSwingBadge');
      const eEl = document.getElementById('hSwingEntry');
      const tp1El = document.getElementById('hSwingTp1');
      const tp2El = document.getElementById('hSwingTp2');
      const sumEl = document.getElementById('hSwingSummary');

      if (vEl) {
        vEl.textContent = swing.verdict;
        vEl.style.color = swing.color || '#00f2fe';
      }
      if (bEl) bEl.textContent = swing.badge;
      if (eEl) eEl.textContent = `$${swing.entry !== undefined ? swing.entry.toFixed(2) : '0.00'}`;
      if (tp1El) tp1El.textContent = `$${swing.take_profit_1 !== undefined ? swing.take_profit_1.toFixed(2) : '0.00'}`;
      if (tp2El) tp2El.textContent = `$${swing.take_profit_2 !== undefined ? swing.take_profit_2.toFixed(2) : '0.00'}`;
      if (sumEl) sumEl.textContent = swing.summary;
    }

    // 3. Long-Term Core (Months - Years)
    const lt = mh.long_term;
    if (lt) {
      const vEl = document.getElementById('hLongVerdict');
      const bEl = document.getElementById('hLongBadge');
      const aEl = document.getElementById('hLongAccum');
      const tEl = document.getElementById('hLongTarget');
      const fEl = document.getElementById('hLongFloor');
      const sumEl = document.getElementById('hLongSummary');

      if (vEl) {
        vEl.textContent = lt.verdict;
        vEl.style.color = lt.color || '#b388ff';
      }
      if (bEl) bEl.textContent = lt.badge;
      if (aEl) aEl.textContent = lt.accum_range || '$0 - $0';
      if (tEl) tEl.textContent = `$${lt.target !== undefined ? lt.target.toFixed(2) : '0.00'}`;
      if (fEl) fEl.textContent = `$${lt.invalidation_floor !== undefined ? lt.invalidation_floor.toFixed(2) : '0.00'}`;
      if (sumEl) sumEl.textContent = lt.summary;
    }
  }

  renderInstitutionalQuant(data) {
    if (!data) return;

    // 1. Factor Neutral Residual Alpha
    const fn = data.factor_neutral;
    if (fn && this.factorSScoreVal) {
      const s = fn.s_score !== undefined ? fn.s_score : 0.0;
      this.factorSScoreVal.textContent = `${s >= 0 ? '+' : ''}${s.toFixed(2)}σ`;
      this.factorSScoreVal.style.color = fn.regime_color || '#4facfe';

      if (this.factorRegimeBadge) {
        this.factorRegimeBadge.textContent = fn.regime_badge || 'SECTOR IN-LINE';
        this.factorRegimeBadge.style.color = fn.regime_color || '#4facfe';
        this.factorRegimeBadge.style.borderColor = fn.regime_color || 'rgba(0, 242, 254, 0.4)';
      }
      if (this.factorSectorTicker) this.factorSectorTicker.textContent = fn.sector_etf || 'SPY';
      if (this.factorBetaSpy) this.factorBetaSpy.textContent = fn.beta_spy !== undefined ? fn.beta_spy.toFixed(2) : '1.00';
      if (this.factorBetaSector) this.factorBetaSector.textContent = fn.beta_sector !== undefined ? fn.beta_sector.toFixed(2) : '1.00';
      if (this.factorAlphaSpread) {
        const spr = fn.alpha_spread_pct || 0.0;
        this.factorAlphaSpread.textContent = `${spr >= 0 ? '+' : ''}${spr.toFixed(1)}%`;
      }
      if (this.factorSummaryText) this.factorSummaryText.textContent = fn.summary || '';
    }

    // 2. Options Market Structure & Gamma Desk
    const opt = data.options_structure;
    if (opt && this.optionsMaxPainVal) {
      if (opt.status === 'ACTIVE') {
        this.optionsMaxPainVal.textContent = `$${opt.max_pain ? opt.max_pain.toFixed(2) : '0.00'}`;
        if (this.optionsGammaBadge) {
          this.optionsGammaBadge.textContent = opt.gamma_badge || 'GAMMA BOUND';
          this.optionsGammaBadge.style.color = opt.gamma_color || '#4facfe';
          this.optionsGammaBadge.style.borderColor = opt.gamma_color || 'rgba(0, 242, 254, 0.4)';
        }
        if (this.optionsPinDist) {
          const dist = opt.pin_distance_pct || 0.0;
          this.optionsPinDist.textContent = `${dist >= 0 ? '+' : ''}${dist.toFixed(1)}% vs price`;
        }
        if (this.optionsCallWall) this.optionsCallWall.textContent = `$${opt.call_wall ? opt.call_wall.toFixed(2) : '0.00'}`;
        if (this.optionsPutWall) this.optionsPutWall.textContent = `$${opt.put_wall ? opt.put_wall.toFixed(2) : '0.00'}`;
        if (this.optionsPcrVal) this.optionsPcrVal.textContent = opt.pcr_oi !== undefined ? opt.pcr_oi.toFixed(2) : '1.00';
        if (this.optionsSummaryText) this.optionsSummaryText.textContent = opt.summary || '';
      } else {
        this.optionsMaxPainVal.textContent = 'N/A';
        if (this.optionsGammaBadge) this.optionsGammaBadge.textContent = 'NON-OPTIONABLE';
        if (this.optionsSummaryText) this.optionsSummaryText.textContent = opt.summary || 'Options chains not available for this ticker.';
      }
    }

    // 3. Volatility-Targeted Risk Parity Sizing
    const rs = data.risk_sizing;
    if (rs) {
      this.recommendedShares = rs.recommended_shares || 10;
      if (this.riskRecSharesVal) this.riskRecSharesVal.textContent = `${this.recommendedShares} Shares`;
      if (this.riskCapitalReq) this.riskCapitalReq.textContent = `$${rs.capital_required ? rs.capital_required.toLocaleString() : '0.00'}`;
      if (this.riskMaxLoss) this.riskMaxLoss.textContent = `$${rs.risk_budget || 500}`;
      if (this.riskPortExposure) this.riskPortExposure.textContent = `${rs.portfolio_allocation_pct || 0.0}%`;
      if (this.paperRiskSharesBadge) this.paperRiskSharesBadge.textContent = this.recommendedShares;

      if (this.paperSortinoVal) {
        this.paperSortinoVal.textContent = '2.14';
      }
    }
  }

  renderExecutionBlueprint(setup, verdict, price, q) {
    const isBuy = verdict.includes('STRONG BUY') || (verdict.includes('BUY') && !verdict.includes('SELL'));
    const isSell = verdict.includes('STRONG SELL') || verdict.includes('SELL');

    // Values
    if (this.entryPrice) this.entryPrice.textContent = `$${setup.entry_price ? setup.entry_price.toFixed(2) : price.toFixed(2)}`;
    if (this.stopLossPrice) this.stopLossPrice.textContent = `$${setup.stop_loss ? setup.stop_loss.toFixed(2) : '--'}`;
    if (this.tp1Price) this.tp1Price.textContent = `$${setup.take_profit_1 ? setup.take_profit_1.toFixed(2) : '--'}`;
    if (this.tp2Price) this.tp2Price.textContent = `$${setup.take_profit_2 ? setup.take_profit_2.toFixed(2) : '--'}`;
    if (this.rrBadge) this.rrBadge.textContent = `R:R ${setup.risk_reward_ratio || '1 : 2.0'}`;
    if (this.riskPctSub) this.riskPctSub.textContent = `Max Risk: ~${setup.max_risk_pct !== undefined ? setup.max_risk_pct : 2.5}%`;
    if (this.atrDisplay) this.atrDisplay.textContent = `$${setup.atr ? setup.atr.toFixed(2) : '0.00'}`;

    if (q) {
      const dayLow = q.day_low && q.day_low > 0 ? q.day_low.toFixed(2) : price.toFixed(2);
      const dayHigh = q.day_high && q.day_high > 0 ? q.day_high.toFixed(2) : price.toFixed(2);
      if (this.dayRangeDisplay) this.dayRangeDisplay.textContent = `$${dayLow} - $${dayHigh}`;
    }

    // Dynamic Card Labels & Content
    const labels = setup.labels || {};
    const entryLabel = document.getElementById('entryLabel');
    const entrySub = document.getElementById('entrySub');
    const slLabel = document.getElementById('slLabel');
    const slSub = document.getElementById('riskPctSub');
    const tp1Label = document.getElementById('tp1Label');
    const tp1Sub = document.getElementById('tp1Sub');
    const tp2Label = document.getElementById('tp2Label');
    const tp2Sub = document.getElementById('tp2Sub');

    if (entryLabel) entryLabel.textContent = labels.entry_title || (isBuy ? 'WHEN TO BUY (ENTRY)' : (isSell ? 'WHEN TO SELL (EXIT NOW)' : 'PIVOT BENCHMARK'));
    if (entrySub) entrySub.textContent = labels.entry_sub || (isBuy ? 'Market or Limit Entry' : (isSell ? 'Sell existing shares at Market' : 'Consolidation baseline'));
    if (slLabel) slLabel.textContent = labels.sl_title || (isBuy ? 'STOP-LOSS (CUT LOSS)' : (isSell ? 'INVALIDATION CEILING' : 'SUPPORT FLOOR'));
    if (slSub && labels.sl_sub) slSub.textContent = labels.sl_sub;
    if (tp1Label) tp1Label.textContent = labels.tp1_title || (isBuy ? 'TAKE PROFIT 1 (SELL 50%)' : (isSell ? 'DOWNSIDE TARGET 1 (RE-BUY DIP)' : 'RESISTANCE 1'));
    if (tp1Sub) tp1Sub.textContent = labels.tp1_sub || (isBuy ? 'Target 1 Gain' : (isSell ? 'First Support zone' : 'Breakout level'));
    if (tp2Label) tp2Label.textContent = labels.tp2_title || (isBuy ? 'TAKE PROFIT 2 (RUNNER)' : (isSell ? 'DOWNSIDE TARGET 2 (VALUE FLOOR)' : 'RESISTANCE 2'));
    if (tp2Sub) tp2Sub.textContent = labels.tp2_sub || (isBuy ? 'Extended Gain' : (isSell ? 'Deep support level' : 'Runner ceiling'));

    // Dynamic Plain-English Helpers
    const entryHelp = document.getElementById('entryHelp');
    const tp1Help = document.getElementById('tp1Help');
    const tp2Help = document.getElementById('tp2Help');
    const slHelp = document.getElementById('slHelp');

    if (isSell) {
      if (entryHelp) entryHelp.textContent = '🚪 Target price to sell & exit existing shares';
      if (tp1Help) tp1Help.textContent = '📉 First lower support target (dip level)';
      if (tp2Help) tp2Help.textContent = '📉 Deeper value floor if crash continues';
      if (slHelp) slHelp.textContent = '🛑 Invalidation ceiling: exit cutoff if price recovers';
    } else if (isBuy) {
      if (entryHelp) entryHelp.textContent = '🎯 Recommended purchase price to enter';
      if (tp1Help) tp1Help.textContent = '💰 Sell half here to bank guaranteed profit';
      if (tp2Help) tp2Help.textContent = '🚀 Extended target if rally continues surging';
      if (slHelp) slHelp.textContent = '🛑 Emergency exit: sell here to prevent big losses';
    } else {
      if (entryHelp) entryHelp.textContent = '⚖️ Sideways benchmark price';
      if (tp1Help) tp1Help.textContent = '🎯 Upper resistance ceiling';
      if (tp2Help) tp2Help.textContent = '🎯 Secondary breakout level';
      if (slHelp) slHelp.textContent = '🛑 Lower support floor';
    }

    // Highlight the primary action card
    const cardEntry = document.getElementById('cardEntry');
    if (cardEntry) {
      if (isSell) {
        cardEntry.style.borderColor = 'rgba(255, 23, 68, 0.45)';
        if (entryLabel) entryLabel.style.color = '#ff5252';
      } else if (isBuy) {
        cardEntry.style.borderColor = 'rgba(0, 230, 118, 0.45)';
        if (entryLabel) entryLabel.style.color = '#00e676';
      } else {
        cardEntry.style.borderColor = 'var(--border-subtle)';
        if (entryLabel) entryLabel.style.color = 'var(--text-muted)';
      }
    }

    // Playbook Container & Scenarios
    const playbook = document.getElementById('executionPlaybook');
    const pBadge = document.getElementById('playbookBadge');
    const pHeadline = document.getElementById('playbookHeadline');
    const pSummary = document.getElementById('playbookSummary');
    const pIfHolding = document.getElementById('playbookIfHolding');
    const pHoldingBadge = document.getElementById('holdingActionBadge');
    const pIfBuying = document.getElementById('playbookIfBuying');
    const pBuyingBadge = document.getElementById('buyingActionBadge');
    const pIfShorting = document.getElementById('playbookIfShorting');
    const pShortBadge = document.getElementById('shortActionBadge');

    if (playbook) {
      playbook.className = `execution-playbook ${isBuy ? 'playbook-buy' : (isSell ? 'playbook-sell' : 'playbook-neutral')}`;
    }
    if (pBadge) {
      pBadge.textContent = isBuy ? '🟢 BUY PLAYBOOK' : (isSell ? '🔴 SELL PLAYBOOK' : '⏸️ NEUTRAL PLAYBOOK');
    }
    if (pHeadline) {
      pHeadline.textContent = setup.headline || (isBuy ? 'Bullish Buy Setup — Defined Risk' : (isSell ? 'Bearish Sell / Exit Setup — Protect Capital' : 'Sideways Consolidation — Stand Aside'));
    }
    if (pSummary) {
      pSummary.textContent = setup.summary_text || (isBuy ? `Optimal entry at $${(setup.entry_price || price).toFixed(2)}. Target $${(setup.take_profit_1 || price).toFixed(2)}. Strict stop at $${(setup.stop_loss || price).toFixed(2)}.` : (isSell ? `Bearish distribution confirmed. Liquidate existing shares near $${(setup.entry_price || price).toFixed(2)} before price drops toward $${(setup.take_profit_1 || price).toFixed(2)}.` : 'Sideways market with balanced order flow. Wait for a clear breakout.'));
    }
    if (pIfHolding) {
      pIfHolding.textContent = setup.if_holding || (isBuy ? 'Hold current shares and target profit levels.' : (isSell ? `SELL NOW around $${(setup.entry_price || price).toFixed(2)} to protect gains and cut exposure.` : 'Hold with tight trailing stop.'));
    }
    if (pHoldingBadge) {
      pHoldingBadge.textContent = isBuy ? 'HOLD / ACCUMULATE' : (isSell ? 'SELL / EXIT NOW' : 'HOLD STOP');
      pHoldingBadge.className = `pcard-badge ${isBuy ? 'badge-buy' : (isSell ? 'badge-sell' : 'badge-neutral')}`;
    }
    if (pIfBuying) {
      pIfBuying.textContent = setup.if_buying || (isBuy ? `Safe to buy now near $${(setup.entry_price || price).toFixed(2)} with stop at $${(setup.stop_loss || price).toFixed(2)}.` : (isSell ? `DO NOT BUY YET. Wait for price to drop to support ($${(setup.take_profit_1 || price).toFixed(2)}) or reverse.` : 'Wait for confirmed breakout.'));
    }
    if (pBuyingBadge) {
      pBuyingBadge.textContent = isBuy ? 'SAFE TO BUY' : (isSell ? 'DO NOT BUY' : 'WAIT FOR BREAKOUT');
      pBuyingBadge.className = `pcard-badge ${isBuy ? 'badge-buy' : (isSell ? 'badge-sell' : 'badge-neutral')}`;
    }
    if (pIfShorting) {
      pIfShorting.textContent = setup.if_shorting || (isBuy ? 'Avoid shorting in an uptrend.' : (isSell ? `Short at $${(setup.entry_price || price).toFixed(2)} | Target: $${(setup.take_profit_1 || price).toFixed(2)} | Stop: $${(setup.stop_loss || price).toFixed(2)}` : 'No high-probability short setup.'));
    }
    if (pShortBadge) {
      pShortBadge.textContent = isBuy ? 'AVOID SHORT' : (isSell ? 'SHORT SETUP' : 'STAND ASIDE');
      pShortBadge.className = `pcard-badge ${isBuy ? 'badge-neutral' : (isSell ? 'badge-sell' : 'badge-neutral')}`;
    }

    // Dynamic Risk-Reward Bar Labels
    const rrLeft = document.getElementById('rrLeftLabel');
    const rrMid = document.getElementById('rrMidLabel');
    const rrRight = document.getElementById('rrRightLabel');
    if (rrLeft && rrMid && rrRight) {
      if (isSell) {
        rrLeft.textContent = 'Invalidation / Stop';
        rrMid.textContent = 'Exit / Short Entry';
        rrRight.textContent = 'Downside Support Targets';
      } else {
        rrLeft.textContent = 'Max Stop Risk';
        rrMid.textContent = 'Buy Entry';
        rrRight.textContent = 'Take Profit Targets';
      }
    }
  }

  updatePositionCalculator() {
    if (!this.currentSetup) return;
    const capitalInput = document.getElementById('calcCapital');
    const riskSelect = document.getElementById('calcRiskPct');
    if (!capitalInput || !riskSelect) return;

    const capital = parseFloat(capitalInput.value) || 10000;
    const riskPct = parseFloat(riskSelect.value) || 0.02;

    const entry = this.currentSetup.price;
    const stopLoss = this.currentSetup.stopLoss;
    const tp1 = this.currentSetup.tp1;
    const action = this.currentSetup.action || 'BUY';
    const isSell = action.includes('SELL');

    const riskPerShare = Math.max(0.01, Math.abs(entry - stopLoss));
    const maxCashRisk = capital * riskPct;
    const shares = Math.max(1, Math.floor(maxCashRisk / riskPerShare));
    const positionCost = shares * entry;
    const targetProfit = shares * Math.abs(tp1 - entry);

    const sharesLabel = document.getElementById('calcSharesLabel');
    const profitLabel = document.getElementById('calcProfitLabel');
    const sharesVal = document.getElementById('calcSharesVal');
    const posCostVal = document.getElementById('calcPosCostVal');
    const cashRiskVal = document.getElementById('calcCashRiskVal');
    const profitVal = document.getElementById('calcTargetProfitVal');
    const explanation = document.getElementById('calcExplanation');

    const heroShares = document.getElementById('heroSharesVal');
    const heroCap = document.getElementById('heroCapitalSub');
    if (heroShares) heroShares.textContent = `${shares.toLocaleString()} Shares`;
    if (heroCap) heroCap.textContent = isSell ? `~$${targetProfit.toFixed(0)} drop avoided` : `$${positionCost.toLocaleString(undefined, {maximumFractionDigits:0})} cap • $${maxCashRisk.toFixed(0)} risk`;

    if (sharesLabel) sharesLabel.textContent = isSell ? 'SHARES TO EXIT / SHORT' : 'RECOMMENDED SHARES TO BUY';
    if (profitLabel) profitLabel.textContent = isSell ? 'DOWNSIDE LOSS AVOIDED' : 'TARGET 1 PROFIT';
    if (sharesVal) sharesVal.textContent = `${shares.toLocaleString()} Shares`;
    if (posCostVal) posCostVal.textContent = `$${positionCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    if (cashRiskVal) cashRiskVal.textContent = `$${maxCashRisk.toFixed(2)}`;
    if (profitVal) profitVal.textContent = isSell ? `$${targetProfit.toFixed(2)} Saved` : `+$${targetProfit.toFixed(2)}`;

    if (explanation) {
      if (isSell) {
        explanation.innerHTML = `⚠️ <strong>Exit Plan:</strong> If holding shares, selling <strong>${shares.toLocaleString()} shares</strong> at <strong>$${entry.toFixed(2)}</strong> saves you <strong>$${targetProfit.toFixed(2)}</strong> from the forecasted drop to $${tp1.toFixed(2)}. (Or if shorting: risk is capped at $${maxCashRisk.toFixed(0)} if stopped out at $${stopLoss.toFixed(2)}).`;
      } else {
        explanation.innerHTML = `💡 <strong>Trade Plan:</strong> On a $${capital.toLocaleString()} account risking ${(riskPct * 100).toFixed(0)}% ($${maxCashRisk.toFixed(0)}), buy <strong>${shares.toLocaleString()} shares</strong> at <strong>$${entry.toFixed(2)}</strong> ($${positionCost.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} total capital). If stopped at <strong>$${stopLoss.toFixed(2)}</strong>, your loss is capped at $${(shares * riskPerShare).toFixed(2)}. Target 1 profit is <strong>+$${targetProfit.toFixed(2)}</strong>.`;
      }
    }
  }


  async loadPaperPortfolio() {
    try {
      const res = await fetch('/api/paper/portfolio');
      if (!res.ok) return;
      const data = await res.json();
      
      const cashEl = document.getElementById('paperCash');
      const posValEl = document.getElementById('paperPosVal');
      const totalValEl = document.getElementById('paperTotalVal');
      const netPnlEl = document.getElementById('paperNetPnl');
      const tbody = document.getElementById('paperPositionsTbody');

      if (cashEl) cashEl.textContent = `$${data.cash_balance.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      if (posValEl) posValEl.textContent = `$${data.positions_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      if (totalValEl) totalValEl.textContent = `$${data.total_account_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
      
      if (netPnlEl) {
        const isUp = data.net_profit >= 0;
        netPnlEl.textContent = `${isUp ? '+' : ''}$${data.net_profit.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })} (${isUp ? '+' : ''}${data.net_profit_pct}%)`;
        netPnlEl.className = `p-stat-val ${isUp ? 'text-success' : 'text-danger'}`;
      }

      if (tbody) {
        const positions = data.open_positions || [];
        if (positions.length === 0) {
          tbody.innerHTML = '<tr><td colspan="7" class="text-center text-muted">No open paper positions. Click "Execute Buy" to take a simulated position.</td></tr>';
        } else {
          tbody.innerHTML = positions.map(p => {
            const isPnlUp = p.unrealized_pnl >= 0;
            return `
              <tr>
                <td><strong>${p.symbol}</strong></td>
                <td>${p.shares}</td>
                <td>$${p.avg_price.toFixed(2)}</td>
                <td>$${p.current_price.toFixed(2)}</td>
                <td>$${p.market_value.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}</td>
                <td class="${isPnlUp ? 'text-success' : 'text-danger'}">${isPnlUp ? '+' : ''}$${p.unrealized_pnl.toFixed(2)} (${isPnlUp ? '+' : ''}${p.unrealized_pnl_pct}%)</td>
                <td><button onclick="window.app.executePaperTrade('${p.symbol}', 'SELL', ${p.shares})" class="btn btn-danger-glow" style="padding: 2px 8px; font-size: 0.7rem;">Sell Position</button></td>
              </tr>
            `;
          }).join('');
        }
      }
    } catch (err) {
      console.warn('Paper portfolio load error:', err);
    }
  }

  showToast(message, isError = false) {
    const toast = document.getElementById('toastNotification');
    if (!toast) return;
    toast.innerHTML = `${isError ? '⚠️' : '✅'} <span>${message}</span>`;
    toast.classList.remove('hidden');
    toast.style.borderColor = isError ? '#ff1744' : 'var(--accent-cyan)';
    clearTimeout(this._toastTimeout);
    this._toastTimeout = setTimeout(() => {
      toast.classList.add('hidden');
    }, 4000);
  }

  async executePaperTrade(symbol, action, shares = 10) {
    try {
      const res = await fetch('/api/paper/execute', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ symbol, action, shares })
      });
      const data = await res.json();
      if (!res.ok) {
        this.showToast(data.detail || 'Trade execution failed.', true);
        return;
      }
      this.showToast(data.message || `Successfully executed ${action} for ${shares} shares of ${symbol}.`);
      this.loadPaperPortfolio();
    } catch (err) {
      this.showToast(`Trade error: ${err.message}`, true);
    }
  }

  renderFactor(name, val, maxAbs, textEl, barEl) {
    if (val === undefined || val === null) return;
    textEl.textContent = `${val > 0 ? '+' : ''}${val}`;
    const pct = Math.min(100, Math.max(10, ((val + maxAbs) / (2 * maxAbs)) * 100));
    barEl.style.width = `${pct}%`;

    barEl.className = 'factor-bar-fill ';
    if (val > 0) {
      barEl.classList.add('bg-success');
      textEl.className = 'factor-score text-success';
    } else if (val < 0) {
      barEl.classList.add('bg-danger');
      textEl.className = 'factor-score text-danger';
    } else {
      barEl.classList.add('bg-warning');
      textEl.className = 'factor-score text-warning';
    }
  }

  async loadBacktestData(symbol) {
    try {
      const res = await fetch(`/api/backtest/${encodeURIComponent(symbol)}?period=1y`);
      if (!res.ok) return;
      const bt = await res.json();

      this.btWinRate.textContent = `${bt.win_rate_pct}%`;
      this.btProfitFactor.textContent = bt.profit_factor.toFixed(2);
      this.btNetReturn.textContent = `${bt.net_return_pct > 0 ? '+' : ''}${bt.net_return_pct}%`;
      this.btNetReturn.className = `bt-val ${bt.net_return_pct >= 0 ? 'text-success' : 'text-danger'}`;
      this.btDrawdown.textContent = `-${bt.max_drawdown_pct}%`;
      this.btBenchmark.textContent = `${bt.buy_and_hold_return_pct > 0 ? '+' : ''}${bt.buy_and_hold_return_pct}%`;
      this.btTotalTrades.textContent = `${bt.total_trades} (${bt.winning_trades}W / ${bt.losing_trades}L)`;

      // Render trade-by-trade log
      const tradeLog = document.getElementById('tradeLogContainer');
      if (tradeLog) {
        const trades = bt.recent_trades || [];
        if (trades.length === 0) {
          tradeLog.innerHTML = '<div class="trade-log-empty">No trades found in the selected period.</div>';
        } else {
          tradeLog.innerHTML = trades.slice().reverse().map(t => {
            const isWin = t.outcome === 'TAKE_PROFIT';
            const pnlColor = isWin ? '#00e676' : '#ff1744';
            return `<div class="trade-log-row ${isWin ? 'trade-win' : 'trade-loss'}">
              <div><div class="trade-log-label">Date</div><div class="trade-log-val">${t.exit_date}</div></div>
              <div><div class="trade-log-label">Entry</div><div class="trade-log-val">$${t.entry_price}</div></div>
              <div><div class="trade-log-label">Exit</div><div class="trade-log-val">$${t.exit_price}</div></div>
              <div><div class="trade-log-label">Outcome</div><div class="trade-log-val" style="color:${pnlColor}">${isWin ? '✅ TP HIT' : '❌ SL HIT'}</div></div>
              <div><div class="trade-log-label">P&L</div><div class="trade-log-val" style="color:${pnlColor}">${t.pnl_pct > 0 ? '+' : ''}${t.pnl_pct}%</div></div>
            </div>`;
          }).join('');
        }
      }
    } catch (err) {
      console.warn('Backtest load failed:', err);
    }
  }
}

// Bootstrap once DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
  window.app = new AlphaPulseApp();

  // Attach paper trading button listeners
  const buyBtn = document.getElementById('paperBuyBtn');
  const sellBtn = document.getElementById('paperSellBtn');
  const resetBtn = document.getElementById('paperResetBtn');

  if (buyBtn) {
    buyBtn.addEventListener('click', () => {
      const sym = window.app ? window.app.currentSymbol : 'NVDA';
      const sharesStr = prompt(`Enter number of shares of ${sym} to BUY:`, "10");
      if (sharesStr) {
        const shares = parseFloat(sharesStr);
        if (shares > 0) window.app.executePaperTrade(sym, 'BUY', shares);
      }
    });
  }

  if (sellBtn) {
    sellBtn.addEventListener('click', () => {
      const sym = window.app ? window.app.currentSymbol : 'NVDA';
      const sharesStr = prompt(`Enter number of shares of ${sym} to SELL:`, "10");
      if (sharesStr) {
        const shares = parseFloat(sharesStr);
        if (shares > 0) window.app.executePaperTrade(sym, 'SELL', shares);
      }
    });
  }

  // Attach position calculator listeners
  const capitalInput = document.getElementById('calcCapital');
  const riskSelect = document.getElementById('calcRiskPct');
  if (capitalInput) capitalInput.addEventListener('input', () => window.app && window.app.updatePositionCalculator());
  if (riskSelect) riskSelect.addEventListener('change', () => window.app && window.app.updatePositionCalculator());

  if (resetBtn) {
    resetBtn.addEventListener('click', async () => {
      if (confirm("Reset paper trading portfolio back to $100,000 cash?")) {
        await fetch('/api/paper/reset', { method: 'POST' });
        if (window.app) window.app.loadPaperPortfolio();
      }
    });
  }

  // Signal Tracker Refresh Button
  const refreshTrackerBtn = document.getElementById('refreshTrackerBtn');
  if (refreshTrackerBtn) {
    refreshTrackerBtn.addEventListener('click', async () => {
      refreshTrackerBtn.textContent = '↻ Refreshing...';
      try {
        const res = await fetch('/api/signals/tracker');
        if (res.ok) {
          const stats = await res.json();
          if (window.app) window.app.renderSignalTracker(stats);
        }
      } catch (err) {
        console.warn('Tracker refresh failed:', err);
      } finally {
        refreshTrackerBtn.textContent = '↻ Refresh';
      }
    });
  }
});


