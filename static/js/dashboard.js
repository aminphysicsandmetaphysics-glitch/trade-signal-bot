class SignalDashboard {
    constructor() {
        this.autoUpdate = true;
        this.updateInterval = null;
        this.lastSignalCount = 0;
        this.knownSignals = new Set();
        
        this.init();
    }
    
    init() {
        this.startAutoUpdate();
        this.loadSignals();
    }
    
    startAutoUpdate() {
        if (this.updateInterval) {
            clearInterval(this.updateInterval);
        }
        
        if (this.autoUpdate) {
            this.updateInterval = setInterval(() => {
                this.loadSignals();
            }, 3000); // Update every 3 seconds
        }
    }
    
    async loadSignals() {
        try {
            const response = await fetch('/api/signals');
            if (!response.ok) throw new Error('Failed to fetch signals');
            
            const data = await response.json();
            this.updateStatistics(data);
            this.updateSignalFeed(data.signals);
            this.updateLastUpdateTime();
            
        } catch (error) {
            console.error('Error loading signals:', error);
            this.showError('Failed to load signals');
        }
    }
    
    updateStatistics(data) {
        const totalSignals = data.total_signals || 0;
        const buySignals = data.signals.filter(s => s.position === 'BUY').length;
        const sellSignals = data.signals.filter(s => s.position === 'SELL').length;
        const botStatus = data.bot_status || 'stopped';
        
        document.getElementById('totalSignals').textContent = totalSignals;
        document.getElementById('buySignals').textContent = buySignals;
        document.getElementById('sellSignals').textContent = sellSignals;
        
        this.updateBotStatus(botStatus);
    }
    
    updateBotStatus(status) {
        const statusElement = document.getElementById('botStatus');
        const statusText = document.getElementById('statusText');
        const indicator = statusElement.querySelector('.status-indicator');
        
        indicator.className = 'status-indicator';
        
        switch (status) {
            case 'running':
                indicator.classList.add('status-running');
                statusText.textContent = 'Running';
                break;
            case 'ready':
                indicator.classList.add('status-ready');
                statusText.textContent = 'Ready';
                break;
            default:
                indicator.classList.add('status-stopped');
                statusText.textContent = 'Stopped';
        }
    }
    
    updateSignalFeed(signals) {
        const feedElement = document.getElementById('signalFeed');
        const emptyState = document.getElementById('emptyState');
        
        if (signals.length === 0) {
            emptyState.style.display = 'block';
            return;
        }
        
        emptyState.style.display = 'none';
        
        // Check for new signals
        const newSignals = signals.filter(signal => !this.knownSignals.has(signal.id));
        
        // Add new signals to known set
        newSignals.forEach(signal => this.knownSignals.add(signal.id));
        
        // If there are new signals, rebuild the feed to show them at the top
        if (newSignals.length > 0) {
            this.buildSignalFeed(signals, newSignals.map(s => s.id));
        }
    }
    
    buildSignalFeed(signals, newSignalIds = []) {
        const feedElement = document.getElementById('signalFeed');
        
        const signalHTML = signals.map(signal => {
            const isNew = newSignalIds.includes(signal.id);
            const takeProfit = JSON.parse(signal.take_profits || '[]');
            
            return `
                <div class="signal-item p-3 border-bottom ${isNew ? 'new-signal' : ''}" 
                     onclick="showSignalDetails(${signal.id})" style="cursor: pointer;">
                    <div class="d-flex justify-content-between align-items-start">
                        <div>
                            <h6 class="mb-1">
                                <i class="fas fa-coins me-2"></i>${signal.symbol}
                                <span class="badge ms-2 ${signal.position === 'BUY' ? 'bg-success' : 'bg-danger'}">
                                    ${signal.position}
                                </span>
                                ${isNew ? '<span class="badge bg-warning ms-1">NEW</span>' : ''}
                            </h6>
                            <div class="row small text-muted">
                                <div class="col-md-6">
                                    <strong>Entry:</strong> ${signal.entry}<br>
                                    <strong>Stop Loss:</strong> ${signal.stop_loss}
                                </div>
                                <div class="col-md-6">
                                    <strong>Take Profits:</strong> ${takeProfit.join(', ')}<br>
                                    ${signal.risk_reward ? `<strong>R/R:</strong> ${signal.risk_reward}` : ''}
                                </div>
                            </div>
                        </div>
                        <div class="text-end">
                            <small class="text-muted">
                                ${signal.timestamp}<br>
                                <i class="fas fa-broadcast-tower me-1"></i>${signal.source_channel}
                            </small>
                        </div>
                    </div>
                </div>
            `;
        }).join('');
        
        feedElement.innerHTML = signalHTML;
        
        // Remove new-signal class after animation
        setTimeout(() => {
            document.querySelectorAll('.new-signal').forEach(el => {
                el.classList.remove('new-signal');
            });
        }, 2000);
    }
    
    updateLastUpdateTime() {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        document.getElementById('lastUpdate').textContent = `Last update: ${timeString}`;
    }
    
    showError(message) {
        // You could implement a toast notification here
        console.error(message);
    }
}

// Global functions
let dashboard;

document.addEventListener('DOMContentLoaded', function() {
    dashboard = new SignalDashboard();
});

function toggleAutoUpdate() {
    dashboard.autoUpdate = !dashboard.autoUpdate;
    const updateText = document.getElementById('updateText');
    const updateIcon = document.getElementById('updateIcon');
    
    if (dashboard.autoUpdate) {
        updateText.textContent = 'Auto Update: ON';
        updateIcon.classList.remove('fa-play');
        updateIcon.classList.add('fa-sync-alt');
        dashboard.startAutoUpdate();
    } else {
        updateText.textContent = 'Auto Update: OFF';
        updateIcon.classList.remove('fa-sync-alt');
        updateIcon.classList.add('fa-play');
        clearInterval(dashboard.updateInterval);
    }
}

function clearSignalFeed() {
    const feedElement = document.getElementById('signalFeed');
    const emptyState = document.getElementById('emptyState');
    
    feedElement.innerHTML = '';
    emptyState.style.display = 'block';
    dashboard.knownSignals.clear();
}

function showSignalDetails(signalId) {
    // Find the signal data
    fetch('/api/signals')
        .then(response => response.json())
        .then(data => {
            const signal = data.signals.find(s => s.id === signalId);
            if (signal) {
                displaySignalModal(signal);
            }
        })
        .catch(error => {
            console.error('Error fetching signal details:', error);
        });
}

function displaySignalModal(signal) {
    const takeProfit = JSON.parse(signal.take_profits || '[]');
    
    const modalContent = `
        <div class="row">
            <div class="col-md-6">
                <h5 class="text-primary">${signal.symbol}</h5>
                <div class="mb-3">
                    <span class="badge ${signal.position === 'BUY' ? 'bg-success' : 'bg-danger'} fs-6">
                        ${signal.position}
                    </span>
                </div>
                
                <table class="table table-sm">
                    <tr>
                        <td><strong>Entry Price:</strong></td>
                        <td>${signal.entry}</td>
                    </tr>
                    <tr>
                        <td><strong>Stop Loss:</strong></td>
                        <td>${signal.stop_loss}</td>
                    </tr>
                    <tr>
                        <td><strong>Take Profits:</strong></td>
                        <td>${takeProfit.map((tp, i) => `TP${i+1}: ${tp}`).join('<br>')}</td>
                    </tr>
                    ${signal.risk_reward ? `
                    <tr>
                        <td><strong>Risk/Reward:</strong></td>
                        <td>${signal.risk_reward}</td>
                    </tr>
                    ` : ''}
                    <tr>
                        <td><strong>Source Channel:</strong></td>
                        <td>${signal.source_channel}</td>
                    </tr>
                    <tr>
                        <td><strong>Timestamp:</strong></td>
                        <td>${signal.timestamp}</td>
                    </tr>
                </table>
            </div>
            <div class="col-md-6">
                <h6>Formatted Signal:</h6>
                <div class="bg-dark p-3 rounded small">
                    <pre style="white-space: pre-wrap; margin: 0;">${signal.formatted_signal}</pre>
                </div>
            </div>
        </div>
    `;
    
    document.getElementById('signalDetails').innerHTML = modalContent;
    
    const modal = new bootstrap.Modal(document.getElementById('signalModal'));
    modal.show();
}

// Auto-refresh page if it becomes visible again (handles browser tab switching)
document.addEventListener('visibilitychange', function() {
    if (!document.hidden && dashboard) {
        dashboard.loadSignals();
    }
});
