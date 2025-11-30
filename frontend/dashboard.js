class OptionChainDashboard {
    constructor() {
        this.currentSymbol = 'NIFTY';
        this.data = null;
        this.autoRefresh = true;
        this.refreshInterval = 30000; // 30 seconds
        
        this.init();
    }

    init() {
        this.setupEventListeners();
        this.loadData();
        this.startAutoRefresh();
    }

    setupEventListeners() {
        // Symbol tabs
        document.querySelectorAll('[data-symbol]').forEach(tab => {
            tab.addEventListener('click', (e) => {
                e.preventDefault();
                this.switchSymbol(e.target.getAttribute('data-symbol'));
            });
        });

        // Search functionality
        document.getElementById('search-strike').addEventListener('input', (e) => {
            this.filterStrikes(e.target.value);
        });
    }

    switchSymbol(symbol) {
        this.currentSymbol = symbol;
        document.querySelectorAll('.nav-link').forEach(tab => tab.classList.remove('active'));
        document.querySelector(`[data-symbol="${symbol}"]`).classList.add('active');
        this.loadData();
    }

    async loadData() {
        try {
            const response = await fetch(`/api/data/${this.currentSymbol}`);
            if (!response.ok) throw new Error('Network response was not ok');
            
            this.data = await response.json();
            this.updateDashboard();
        } catch (error) {
            console.error('Error fetching data:', error);
        }
    }

    updateDashboard() {
        this.updateKeyMetrics();
        this.updateCharts();
        this.updateOptionChainTable();
        this.updateTimestamp();
    }

    updateKeyMetrics() {
        const metricsDiv = document.getElementById('key-metrics');
        const { pcr, max_pain, spot_price, skew_patterns } = this.data;

        const pcrSignal = pcr.pcr_oi > 1.2 ? 'danger' : (pcr.pcr_oi < 0.8 ? 'success' : 'warning');
        const skewSignal = skew_patterns.bullish_skew ? 'success' : 
                          (skew_patterns.bearish_skew ? 'danger' : 'warning');

        metricsDiv.innerHTML = `
            <div class="col-md-2">
                <div class="card text-white bg-primary">
                    <div class="card-body text-center">
                        <h6>Spot Price</h6>
                        <h3>${spot_price.toFixed(2)}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-${pcrSignal}">
                    <div class="card-body text-center">
                        <h6>PCR OI</h6>
                        <h3>${pcr.pcr_oi.toFixed(2)}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-info">
                    <div class="card-body text-center">
                        <h6>Max Pain</h6>
                        <h3>${max_pain}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-${skewSignal}">
                    <div class="card-body text-center">
                        <h6>OI Skew</h6>
                        <h3>${skew_patterns.bullish_skew ? 'Bullish' : (skew_patterns.bearish_skew ? 'Bearish' : 'Neutral')}</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-secondary">
                    <div class="card-body text-center">
                        <h6>Total CE OI</h6>
                        <h3>${(pcr.total_ce_oi / 100000).toFixed(1)}L</h3>
                    </div>
                </div>
            </div>
            <div class="col-md-2">
                <div class="card text-white bg-secondary">
                    <div class="card-body text-center">
                        <h6>Total PE OI</h6>
                        <h3>${(pcr.total_pe_oi / 100000).toFixed(1)}L</h3>
                    </div>
                </div>
            </div>
        `;
    }

    updateCharts() {
        this.createOISkewChart();
        this.createVolumeOIChart();
    }

    createOISkewChart() {
        const strikes = this.data.strike_data.map(s => s.strike);
        const oiSkew = this.data.strike_data.map(s => s.oi_skew);

        const trace = {
            x: strikes,
            y: oiSkew,
            type: 'scatter',
            mode: 'lines+markers',
            name: 'OI Skew',
            line: { color: '#007bff' },
            marker: { size: 4 }
        };

        const layout = {
            title: 'OI Skew Across Strikes',
            xaxis: { title: 'Strike Price' },
            yaxis: { title: 'OI Skew Ratio' },
            height: 300,
            showlegend: false
        };

        Plotly.newPlot('oi-skew-chart', [trace], layout);
    }

    createVolumeOIChart() {
        const strikes = this.data.strike_data.map(s => s.strike);
        const ceVolumeOI = this.data.strike_data.map(s => s.ce_volume_oi_ratio || 0);
        const peVolumeOI = this.data.strike_data.map(s => s.pe_volume_oi_ratio || 0);

        const trace1 = {
            x: strikes,
            y: ceVolumeOI,
            type: 'bar',
            name: 'CE Volume/OI',
            marker: { color: 'red' }
        };

        const trace2 = {
            x: strikes,
            y: peVolumeOI,
            type: 'bar',
            name: 'PE Volume/OI',
            marker: { color: 'green' }
        };

        const layout = {
            title: 'Volume-OI Efficiency Ratio',
            xaxis: { title: 'Strike Price' },
            yaxis: { title: 'Volume/OI Ratio' },
            barmode: 'group',
            height: 300
        };

        Plotly.newPlot('volume-oi-chart', [trace1, trace2], layout);
    }

    updateOptionChainTable() {
        const tbody = document.getElementById('chain-table-body');
        tbody.innerHTML = '';

        this.data.strike_data.forEach(strike => {
            const row = document.createElement('tr');
            
            // Color coding based on values
            const ceBuildupClass = strike.ce_buildup === 'LONG' ? 'table-success' : 
                                  (strike.ce_buildup === 'SHORT' ? 'table-danger' : '');
            const peBuildupClass = strike.pe_buildup === 'LONG' ? 'table-success' : 
                                  (strike.pe_buildup === 'SHORT' ? 'table-danger' : '');
            const oiSkewClass = strike.oi_skew > 0.3 ? 'table-warning' : 
                               (strike.oi_skew < -0.3 ? 'table-info' : '');

            row.innerHTML = `
                <td><strong>${strike.strike}</strong></td>
                <td>${this.formatNumber(strike.ce_oi)}</td>
                <td class="${strike.ce_change_oi > 0 ? 'text-success' : 'text-danger'}">
                    ${strike.ce_change_oi > 0 ? '+' : ''}${this.formatNumber(strike.ce_change_oi)}
                </td>
                <td>${this.formatNumber(strike.ce_volume)}</td>
                <td>${(strike.ce_volume_oi_ratio || 0).toFixed(2)}</td>
                <td class="${ceBuildupClass}">${strike.ce_buildup || '-'}</td>
                <td class="${oiSkewClass}">${(strike.oi_skew * 100).toFixed(1)}%</td>
                <td class="${peBuildupClass}">${strike.pe_buildup || '-'}</td>
                <td>${(strike.pe_volume_oi_ratio || 0).toFixed(2)}</td>
                <td>${this.formatNumber(strike.pe_volume)}</td>
                <td class="${strike.pe_change_oi > 0 ? 'text-success' : 'text-danger'}">
                    ${strike.pe_change_oi > 0 ? '+' : ''}${this.formatNumber(strike.pe_change_oi)}
                </td>
                <td>${this.formatNumber(strike.pe_oi)}</td>
            `;
            tbody.appendChild(row);
        });
    }

    filterStrikes(searchTerm) {
        const rows = document.querySelectorAll('#chain-table-body tr');
        rows.forEach(row => {
            const strike = row.cells[0].textContent;
            if (strike.includes(searchTerm)) {
                row.style.display = '';
            } else {
                row.style.display = 'none';
            }
        });
    }

    formatNumber(num) {
        if (num >= 100000) {
            return (num / 100000).toFixed(1) + 'L';
        } else if (num >= 1000) {
            return (num / 1000).toFixed(1) + 'K';
        }
        return num.toString();
    }

    updateTimestamp() {
        document.getElementById('last-update').textContent = 
            new Date().toLocaleTimeString();
    }

    startAutoRefresh() {
        setInterval(() => {
            if (this.autoRefresh) {
                this.loadData();
            }
        }, this.refreshInterval);
    }
}

// Initialize dashboard when page loads
document.addEventListener('DOMContentLoaded', () => {
    new OptionChainDashboard();
});
