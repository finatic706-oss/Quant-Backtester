document.addEventListener('DOMContentLoaded', () => {
    const scanBtn = document.getElementById('scanBtn');
    const tickerInput = document.getElementById('tickerInput');
    const capitalInput = document.getElementById('capitalInput');
    const btnSpinner = document.getElementById('btn-spinner');
    const btnText = document.querySelector('.btn-text');
    const results = document.getElementById('results');
    const errorMessage = document.getElementById('error-message');
    const displayTicker = document.getElementById('displayTicker');

    let currentResults = {};
    let charts = {};

    // Trigger scan on Enter key
    tickerInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') scanBtn.click();
    });
    capitalInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') scanBtn.click();
    });

    scanBtn.addEventListener('click', async () => {
        const ticker = tickerInput.value.trim();
        const capital = parseFloat(capitalInput.value) || 100000;
        
        if (!ticker) {
            showError("Please enter a stock ticker.");
            return;
        }

        // UI Reset
        hideError();
        results.classList.add('hidden');
        btnSpinner.classList.remove('hidden');
        btnText.textContent = "Simulating...";
        scanBtn.disabled = true;

        try {
            const response = await fetch('/api/backtest', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ ticker: ticker })
            });

            const data = await response.json();

            if (!response.ok) {
                throw new Error(data.error || "An error occurred while backtesting.");
            }

            currentResults = data.results;
            displayResults(data.ticker, data.results, capital);

        } catch (error) {
            showError(error.message);
        } finally {
            btnSpinner.classList.add('hidden');
            btnText.textContent = "Run Simulation";
            scanBtn.disabled = false;
        }
    });

    function showError(msg) {
        errorMessage.textContent = msg;
        errorMessage.classList.remove('hidden');
    }
    function hideError() {
        errorMessage.classList.add('hidden');
    }

    function formatPct(val) {
        const sign = val > 0 ? '+' : '';
        return `<span class="${val >= 0 ? 'positive' : 'negative'}">${sign}${val.toFixed(2)}%</span>`;
    }

    // Format numbers as Indian Rupees
    function formatCurrency(val) {
        return new Intl.NumberFormat('en-IN', {
            style: 'currency',
            currency: 'INR',
            maximumFractionDigits: 0
        }).format(val);
    }

    // Animate the final value counting up
    function animateValue(obj, start, end, duration) {
        let startTimestamp = null;
        const step = (timestamp) => {
            if (!startTimestamp) startTimestamp = timestamp;
            const progress = Math.min((timestamp - startTimestamp) / duration, 1);
            const currentVal = Math.floor(progress * (end - start) + start);
            obj.innerHTML = formatCurrency(currentVal);
            if (progress < 1) {
                window.requestAnimationFrame(step);
            } else {
                obj.innerHTML = formatCurrency(end);
                // Style based on profit/loss
                obj.style.color = end >= start ? 'var(--success)' : 'var(--danger)';
                obj.style.textShadow = end >= start ? '0 0 10px rgba(16, 185, 129, 0.3)' : '0 0 10px rgba(239, 68, 68, 0.3)';
            }
        };
        window.requestAnimationFrame(step);
    }

    function renderMetricsHtml(data) {
        return `
            <div class="metric-row">
                <span class="metric-label">CAGR (Annualized)</span>
                <span class="metric-value">${formatPct(data.cagr)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total Return</span>
                <span class="metric-value">${formatPct(data.total_return)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Win Rate</span>
                <span class="metric-value">${data.win_rate.toFixed(1)}%</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Max Drawdown</span>
                <span class="metric-value"><span class="negative">${data.max_drawdown.toFixed(2)}%</span></span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Avg Profit / Trade</span>
                <span class="metric-value">${formatPct(data.avg_profit_per_trade)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total Trades</span>
                <span class="metric-value">${data.total_trades}</span>
            </div>
        `;
    }

    function renderHeroMetricsHtml(data, capital) {
        const finalVal = capital * (1 + (data.total_return / 100));
        return `
            <div class="metric-row">
                <span class="metric-label">CAGR</span>
                <span class="metric-value">${formatPct(data.cagr)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Total Return</span>
                <span class="metric-value">${formatPct(data.total_return)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Final Value</span>
                <span class="metric-value ${finalVal >= capital ? 'positive' : 'negative'}">${formatCurrency(finalVal)}</span>
            </div>
            <div class="metric-row">
                <span class="metric-label">Max Drawdown</span>
                <span class="metric-value"><span class="negative">${data.max_drawdown.toFixed(2)}%</span></span>
            </div>
        `;
    }

    function drawChart(canvasId, chartData, color) {
        const ctx = document.getElementById(canvasId).getContext('2d');
        if (charts[canvasId]) { charts[canvasId].destroy(); }

        charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                datasets: [{
                    data: chartData,
                    borderColor: color,
                    borderWidth: 2,
                    pointRadius: 0,
                    pointHitRadius: 10,
                    fill: true,
                    backgroundColor: (context) => {
                        const gradient = ctx.createLinearGradient(0, 0, 0, 180);
                        gradient.addColorStop(0, color.replace('1)', '0.3)'));
                        gradient.addColorStop(1, 'rgba(0, 0, 0, 0)');
                        return gradient;
                    },
                    tension: 0.3
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: { display: false },
                    tooltip: {
                        mode: 'index', intersect: false,
                        callbacks: {
                            label: function(context) { return context.parsed.y + '%'; }
                        }
                    }
                },
                scales: {
                    x: { display: false },
                    y: {
                        display: true,
                        grid: { color: 'rgba(255,255,255,0.05)' },
                        ticks: { color: '#94a3b8', font: { size: 10 } }
                    }
                },
                interaction: { mode: 'nearest', axis: 'x', intersect: false }
            }
        });
    }

    function displayResults(ticker, resultsData, capital) {
        displayTicker.textContent = ticker;
        
        // Benchmark (Buy & Hold)
        const bhData = resultsData["Buy & Hold"];
        if (bhData) {
            document.getElementById('metrics-buyandhold').innerHTML = renderHeroMetricsHtml(bhData, capital);
            drawChart('chart-buyandhold', bhData.chart_data, 'rgba(255, 171, 0, 1)'); // Gold
        }

        // Strategy Cards
        document.getElementById('metrics-momentum').innerHTML = renderMetricsHtml(resultsData["Momentum Breakout"]);
        document.getElementById('metrics-meanrev').innerHTML = renderMetricsHtml(resultsData["Mean Reversion (RSI)"]);
        document.getElementById('metrics-crossover').innerHTML = renderMetricsHtml(resultsData["MA Crossover"]);

        // Animate Final Values
        const fvMom = capital * (1 + (resultsData["Momentum Breakout"].total_return / 100));
        const fvMean = capital * (1 + (resultsData["Mean Reversion (RSI)"].total_return / 100));
        const fvCross = capital * (1 + (resultsData["MA Crossover"].total_return / 100));

        animateValue(document.getElementById('fv-momentum'), capital, fvMom, 1500);
        animateValue(document.getElementById('fv-meanrev'), capital, fvMean, 1500);
        animateValue(document.getElementById('fv-crossover'), capital, fvCross, 1500);

        // Draw Strategy Charts
        drawChart('chart-momentum', resultsData["Momentum Breakout"].chart_data, 'rgba(6, 182, 212, 1)'); // Cyan
        drawChart('chart-meanrev', resultsData["Mean Reversion (RSI)"].chart_data, 'rgba(168, 85, 247, 1)'); // Purple
        drawChart('chart-crossover', resultsData["MA Crossover"].chart_data, 'rgba(16, 185, 129, 1)'); // Green

        results.classList.remove('hidden');
        document.querySelectorAll('.view-trades-btn').forEach(btn => btn.classList.remove('hidden'));
    }

    // Modal Logic
    const modal = document.getElementById('tradesModal');
    const closeBtn = document.querySelector('.close-btn');
    const tradesBody = document.getElementById('tradesBody');
    const modalTitle = document.getElementById('modalTitle');

    document.querySelectorAll('.view-trades-btn').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const strategy = e.target.getAttribute('data-strategy');
            const trades = currentResults[strategy].trade_log;
            
            modalTitle.textContent = `${strategy} - Trade Log`;
            tradesBody.innerHTML = ''; 

            if (trades.length === 0) {
                tradesBody.innerHTML = '<tr><td colspan="5" style="text-align:center;">No trades taken.</td></tr>';
            } else {
                trades.forEach(trade => {
                    const tr = document.createElement('tr');
                    tr.innerHTML = `
                        <td>${trade.entry_date}</td>
                        <td>${trade.entry_price}</td>
                        <td>${trade.exit_date}</td>
                        <td>${trade.exit_price}</td>
                        <td>${formatPct(trade.pnl_pct * 100)}</td>
                    `;
                    tradesBody.appendChild(tr);
                });
            }
            modal.classList.remove('hidden');
        });
    });

    closeBtn.addEventListener('click', () => modal.classList.add('hidden'));
    window.addEventListener('click', (e) => { if (e.target === modal) modal.classList.add('hidden'); });
});
