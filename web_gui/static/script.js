// Global variables
let devices = [];
let activeTab = 'dashboard';
let operationInProgress = false;
let statusCheckInterval = null;

// API base URL
const API_BASE = '/api';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    initializeApp();
    setupEventListeners();
    loadInitialData();
    startAutoRefresh();
    
    // Add tooltips to buttons
    addTooltips();
    
    showNotification('Web interface loaded successfully', 'success', 3000);
});

// Setup event listeners
function setupEventListeners() {
    // Tab navigation
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.addEventListener('click', function() {
            switchTab(this.dataset.tab);
        });
    });

    // Modal close
    document.addEventListener('click', function(e) {
        if (e.target.classList.contains('modal')) {
            closeModal();
        }
    });
}

// Initialize the application
function initializeApp() {
    updateSystemStatus('ready', 'System Ready');
    addActivityLog('Web interface initialized successfully', 'info');
    loadDevices();
}

// Tab switching functionality
function switchTab(tabName) {
    // Update active tab
    document.querySelectorAll('.nav-tab').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelector(`[data-tab="${tabName}"]`).classList.add('active');

    // Update content
    document.querySelectorAll('.tab-content').forEach(content => {
        content.classList.remove('active');
    });
    document.getElementById(tabName).classList.add('active');

    activeTab = tabName;

    // Load tab-specific data
    switch(tabName) {
        case 'devices':
            loadDevices();
            break;
        case 'backup':
            loadBackupHistory();
            break;
        case 'config':
            loadTemplates();
            break;
        case 'logs':
            loadLogs();
            break;
    }
}

// System status management
function updateSystemStatus(status, message) {
    const indicator = document.getElementById('statusIndicator');
    const statusText = indicator.querySelector('.status-text');
    const statusDot = indicator.querySelector('.status-dot');

    statusText.textContent = message;
    statusDot.className = `status-dot ${status}`;
}

// Activity log management
function addActivityLog(message, level = 'info') {
    const activityLog = document.getElementById('activityLog');
    const timestamp = new Date().toLocaleString();
    
    const logEntry = document.createElement('div');
    logEntry.className = 'log-entry';
    logEntry.innerHTML = `
        <span class="timestamp">[${timestamp}]</span>
        <span class="level ${level}">${level.toUpperCase()}</span>
        <span class="message">${message}</span>
    `;
    
    activityLog.insertBefore(logEntry, activityLog.firstChild);
    
    // Keep only last 50 entries
    while (activityLog.children.length > 50) {
        activityLog.removeChild(activityLog.lastChild);
    }
}

// Load initial data
async function loadInitialData() {
    try {
        await loadDevices();
    } catch (error) {
        console.error('Error loading initial data:', error);
    }
}

// Device management functions
async function discoverDevices() {
    if (operationInProgress) {
        showNotification('Another operation is already in progress', 'warning');
        return;
    }
    
    const button = event.target;
    setButtonLoading(button, true);
    
    try {
        operationInProgress = true;
        updateSystemStatus('processing', 'Discovering devices...');
        showNotification('Starting device discovery...', 'info');
        
        showModal('Device Discovery', `
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%" id="discoveryProgress"></div>
                </div>
                <p id="discoveryStatus">Initializing discovery...</p>
            </div>
            <div id="discoveryLogs" class="log-container" style="max-height: 200px; overflow-y: auto; margin-top: 15px;"></div>
        `);
        
        const result = await apiCall('/devices/discover', { method: 'POST' });
        
        // Start monitoring progress
        startProgressMonitoring('discovery');
        
        addActivityLog('Device discovery started successfully', 'info');
        showNotification('Device discovery started successfully', 'success');
        
    } catch (error) {
        operationInProgress = false;
        updateSystemStatus('error', 'Discovery Failed');
        closeModal();
        addActivityLog(`Device discovery failed: ${error.message}`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

async function loadDevices() {
    try {
        const response = await fetch(`${API_BASE}/devices`);
        const result = await response.json();
        
        if (result.success) {
            devices = result.devices;
            document.getElementById('deviceCount').textContent = devices.length;
            
            if (activeTab === 'devices') {
                renderDevices();
            }
        }
    } catch (error) {
        console.error('Error loading devices:', error);
    }
}

function renderDevices() {
    const devicesGrid = document.getElementById('devicesGrid');
    
    if (devices.length === 0) {
        devicesGrid.innerHTML = `
            <div class="text-center">
                <p>No devices discovered yet.</p>
                <button class="btn primary" onclick="discoverDevices()">
                    <i class="fas fa-search"></i>
                    Discover Devices
                </button>
            </div>
        `;
        return;
    }
    
    devicesGrid.innerHTML = devices.map(device => `
        <div class="device-card">
            <div class="device-header">
                <div class="device-name">
                    <i class="fas fa-${getDeviceIcon(device.type)}"></i>
                    ${device.name}
                </div>
                <div class="device-status ${device.status}">
                    ${device.status.toUpperCase()}
                </div>
            </div>
            <div class="device-info">
                <p><strong>IP:</strong> ${device.ip}</p>
                <p><strong>Type:</strong> ${device.type}</p>
                <p><strong>Last Seen:</strong> ${device.lastSeen}</p>
            </div>
            <div class="device-actions">
                <button class="btn primary" onclick="testDevice('${device.name}')" ${device.status === 'offline' ? 'disabled' : ''}>
                    <i class="fas fa-wifi"></i>
                    Test
                </button>
                <button class="btn secondary" onclick="configureDevice('${device.name}')" ${device.status === 'offline' ? 'disabled' : ''}>
                    <i class="fas fa-cog"></i>
                    Configure
                </button>
                <button class="btn info" onclick="backupDevice('${device.name}')" ${device.status === 'offline' ? 'disabled' : ''}>
                    <i class="fas fa-download"></i>
                    Backup
                </button>
            </div>
        </div>
    `).join('');
}

function getDeviceIcon(type) {
    switch(type) {
        case 'router': return 'router';
        case 'switch': return 'network-wired';
        case 'computer': return 'desktop';
        default: return 'server';
    }
}

// Backup functions
async function performBackup() {
    if (operationInProgress) return;
    
    const onlineDevices = devices.filter(d => d.status === 'online');
    if (onlineDevices.length === 0) {
        alert('No online devices available for backup');
        return;
    }
    
    showModal('Backup Operation', 'Backing up device configurations...');
    operationInProgress = true;
    updateSystemStatus('warning', 'Backup in progress...');
    
    try {
        const response = await fetch(`${API_BASE}/backup/all`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            }
        });
        
        const result = await response.json();
        
        if (result.success) {
            startStatusMonitoring();
            addActivityLog('Backup operation started', 'info');
        } else {
            throw new Error(result.error || 'Backup failed');
        }
        
    } catch (error) {
        addOperationLog(`✗ Backup failed: ${error.message}`, 'error');
        addActivityLog('Backup operation failed', 'error');
        updateSystemStatus('error', 'Backup Failed');
        closeModal();
        operationInProgress = false;
    }
}

async function loadBackupHistory() {
    try {
        const response = await fetch(`${API_BASE}/backups`);
        const result = await response.json();
        
        if (result.success) {
            renderBackupHistory(result.backups);
        }
    } catch (error) {
        console.error('Error loading backup history:', error);
    }
}

function renderBackupHistory(backups) {
    const backupList = document.getElementById('backupList');
    
    if (backups.length === 0) {
        backupList.innerHTML = '<p class="text-center">No backups available</p>';
        return;
    }
    
    backupList.innerHTML = backups.map(backup => `
        <div class="backup-item">
            <div class="backup-info">
                <h4>${backup.name}</h4>
                <p>Device: ${backup.device} | Date: ${backup.date} | Size: ${backup.size}</p>
            </div>
            <div class="backup-actions">
                <button class="btn secondary" onclick="downloadBackup('${backup.name}')">
                    <i class="fas fa-download"></i>
                    Download
                </button>
                <button class="btn warning" onclick="restoreBackup('${backup.name}')">
                    <i class="fas fa-upload"></i>
                    Restore
                </button>
                <button class="btn danger" onclick="deleteBackup('${backup.name}')">
                    <i class="fas fa-trash"></i>
                    Delete
                </button>
            </div>
        </div>
    `).join('');
}

// Configuration functions
async function applyConfiguration() {
    const commands = document.getElementById('configCommands').value.trim();
    if (!commands) {
        alert('Please enter configuration commands');
        return;
    }
    
    if (operationInProgress) return;
    
    const onlineDevices = devices.filter(d => d.status === 'online');
    if (onlineDevices.length === 0) {
        alert('No online devices available for configuration');
        return;
    }
    
    showModal('Configuration Application', 'Applying configuration to devices...');
    operationInProgress = true;
    updateSystemStatus('warning', 'Applying configuration...');
    
    try {
        const response = await fetch(`${API_BASE}/config/apply`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({ commands })
        });
        
        const result = await response.json();
        
        if (result.success) {
            startStatusMonitoring();
            addActivityLog('Configuration application started', 'info');
        } else {
            throw new Error(result.error || 'Configuration failed');
        }
        
    } catch (error) {
        addOperationLog(`✗ Configuration failed: ${error.message}`, 'error');
        addActivityLog('Configuration application failed', 'error');
        updateSystemStatus('error', 'Configuration Failed');
        closeModal();
        operationInProgress = false;
    }
}

async function loadTemplates() {
    try {
        const response = await fetch(`${API_BASE}/templates`);
        const result = await response.json();
        
        if (result.success) {
            renderTemplates(result.templates);
        }
    } catch (error) {
        console.error('Error loading templates:', error);
    }
}

function renderTemplates(templates) {
    const templateList = document.getElementById('templateList');
    
    templateList.innerHTML = templates.map(template => `
        <div class="template-item">
            <div>
                <div class="template-name">${template.name}</div>
                <small>${template.description}</small>
            </div>
            <div class="template-actions">
                <button class="btn secondary" onclick="viewTemplate('${template.name}')">
                    <i class="fas fa-eye"></i>
                    View
                </button>
                <button class="btn primary" onclick="useTemplate('${template.name}')">
                    <i class="fas fa-play"></i>
                    Use
                </button>
            </div>
        </div>
    `).join('');
}

// Security functions
async function enablePasswordAuth() {
    const username = document.getElementById('newUsername').value || 'admin';
    const password = document.getElementById('newPassword').value;
    const enableSecret = document.getElementById('enableSecret').value;
    
    if (!password) {
        alert('Please enter a password');
        return;
    }
    
    if (operationInProgress) return;
    
    showModal('Password Authentication', 'Enabling password authentication...');
    operationInProgress = true;
    updateSystemStatus('warning', 'Updating security...');
    
    try {
        const response = await fetch(`${API_BASE}/security/password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'enable',
                username,
                password,
                enable_secret: enableSecret
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            startStatusMonitoring();
            addActivityLog('Password authentication setup started', 'info');
        } else {
            throw new Error(result.error || 'Password setup failed');
        }
        
    } catch (error) {
        addOperationLog(`✗ Password setup failed: ${error.message}`, 'error');
        addActivityLog('Password setup failed', 'error');
        updateSystemStatus('error', 'Security Update Failed');
        closeModal();
        operationInProgress = false;
    }
}

async function rotatePasswords() {
    const username = document.getElementById('newUsername').value || 'admin';
    const password = document.getElementById('newPassword').value;
    const enableSecret = document.getElementById('enableSecret').value;
    
    if (!password) {
        alert('Please enter a password');
        return;
    }
    
    if (operationInProgress) return;
    
    showModal('Password Rotation', 'Rotating passwords...');
    operationInProgress = true;
    updateSystemStatus('warning', 'Updating passwords...');
    
    try {
        const response = await fetch(`${API_BASE}/security/password`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
            },
            body: JSON.stringify({
                action: 'rotate',
                username,
                password,
                enable_secret: enableSecret
            })
        });
        
        const result = await response.json();
        
        if (result.success) {
            startStatusMonitoring();
            addActivityLog('Password rotation started', 'info');
        } else {
            throw new Error(result.error || 'Password rotation failed');
        }
        
    } catch (error) {
        addOperationLog(`✗ Password rotation failed: ${error.message}`, 'error');
        addActivityLog('Password rotation failed', 'error');
        updateSystemStatus('error', 'Password Rotation Failed');
        closeModal();
        operationInProgress = false;
    }
}

// Status monitoring
function startStatusMonitoring() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        try {
            const response = await fetch(`${API_BASE}/operation/status`);
            const status = await response.json();
            
            if (status.current_operation) {
                // Update modal with latest logs
                const operationLog = document.getElementById('operationLog');
                operationLog.innerHTML = status.logs.map(log => 
                    `<div>[${log.timestamp}] ${log.message}</div>`
                ).join('');
                operationLog.scrollTop = operationLog.scrollHeight;
            } else {
                // Operation completed
                stopStatusMonitoring();
                addActivityLog('Operation completed', 'info');
                updateSystemStatus('ready', 'Operation Complete');
                closeModal();
                operationInProgress = false;
                
                // Refresh data
                await loadDevices();
                if (activeTab === 'backup') {
                    await loadBackupHistory();
                }
            }
        } catch (error) {
            console.error('Error checking status:', error);
        }
    }, 1000);
}

function stopStatusMonitoring() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
        statusCheckInterval = null;
    }
}

// Log management
async function loadLogs() {
    try {
        const response = await fetch(`${API_BASE}/logs`);
        const result = await response.json();
        
        if (result.success) {
            renderLogs(result.logs);
        }
    } catch (error) {
        console.error('Error loading logs:', error);
    }
}

function renderLogs(logs) {
    const logViewer = document.getElementById('logViewer');
    
    logViewer.innerHTML = logs.map(log => {
        const level = detectLogLevel(log.content);
        return `<div class="log-line ${level}">[${log.source}] ${log.content}</div>`;
    }).join('');
    
    logViewer.scrollTop = logViewer.scrollHeight;
}

function detectLogLevel(content) {
    if (content.includes('ERROR') || content.includes('Failed')) return 'error';
    if (content.includes('WARNING') || content.includes('Warning')) return 'warning';
    return 'info';
}

// Utility functions
function testConnectivity() {
    if (devices.length === 0) {
        alert('Please discover devices first');
        return;
    }
    
    discoverDevices(); // Reuse the discovery function to test connectivity
}

function refreshDevices() {
    if (devices.length === 0) {
        discoverDevices();
    } else {
        renderDevices();
        addActivityLog('Device list refreshed', 'info');
    }
}

function loadDevices() {
    renderDevices();
}

function viewLogs() {
    switchTab('logs');
}

function backupAll() {
    performBackup();
}

function loadLogs() {
    const logViewer = document.getElementById('logViewer');
    
    // Simulate log entries
    const logs = [
        { timestamp: '2025-07-04 14:11:09', level: 'info', message: 'System initialized successfully' },
        { timestamp: '2025-07-04 14:11:15', level: 'info', message: 'Connected to GNS3 server' },
        { timestamp: '2025-07-04 14:11:16', level: 'info', message: 'Found project: Solange' },
        { timestamp: '2025-07-04 14:11:17', level: 'warning', message: 'SSH connection timeout for R1' },
        { timestamp: '2025-07-04 14:11:18', level: 'error', message: 'Switch1 SSH not configured' },
        { timestamp: '2025-07-04 14:11:19', level: 'info', message: 'Baraton router accessible via SSH' }
    ];
    
    logViewer.innerHTML = logs.map(log => `
        <div class="log-line ${log.level}">
            [${log.timestamp}] ${log.level.toUpperCase()}: ${log.message}
        </div>
    `).join('');
}

// Modal functions
function showModal(title, content) {
    const modal = document.getElementById('operationModal');
    const modalTitle = document.getElementById('modalTitle');
    const modalBody = document.querySelector('.modal-body');
    
    if (modal && modalTitle && modalBody) {
        modalTitle.textContent = title;
        modalBody.innerHTML = content;
        modal.style.display = 'block';
        
        // Add escape key listener
        document.addEventListener('keydown', handleModalEscape);
    }
}

function handleModalEscape(e) {
    if (e.key === 'Escape') {
        closeModal();
    }
}

function closeModal() {
    const modal = document.getElementById('operationModal');
    if (modal) {
        modal.style.display = 'none';
    }
    document.removeEventListener('keydown', handleModalEscape);
}

function addOperationLog(message, level = 'info') {
    const operationLog = document.getElementById('operationLog');
    const timestamp = new Date().toLocaleString();
    
    const logEntry = document.createElement('div');
    logEntry.innerHTML = `[${timestamp}] ${message}`;
    if (level === 'error') {
        logEntry.style.color = '#e74c3c';
    }
    
    operationLog.appendChild(logEntry);
    operationLog.scrollTop = operationLog.scrollHeight;
}

// Enhanced notification system
function showNotification(message, type = 'info', duration = 5000) {
    // Remove existing notifications
    const existingNotifications = document.querySelectorAll('.notification');
    existingNotifications.forEach(notification => notification.remove());
    
    const notification = document.createElement('div');
    notification.className = `notification ${type}`;
    notification.innerHTML = `
        <div style="display: flex; align-items: center; justify-content: space-between;">
            <span>${message}</span>
            <button onclick="this.parentElement.parentElement.remove()" style="background: none; border: none; color: white; font-size: 18px; cursor: pointer; padding: 0; margin-left: 10px;">&times;</button>
        </div>
    `;
    
    document.body.appendChild(notification);
    
    // Trigger animation
    setTimeout(() => notification.classList.add('show'), 100);
    
    // Auto remove
    setTimeout(() => {
        notification.classList.remove('show');
        setTimeout(() => notification.remove(), 300);
    }, duration);
}

// Enhanced loading state management
function setButtonLoading(buttonElement, loading = true) {
    if (loading) {
        buttonElement.disabled = true;
        buttonElement.classList.add('loading');
        buttonElement.dataset.originalText = buttonElement.textContent;
    } else {
        buttonElement.disabled = false;
        buttonElement.classList.remove('loading');
        if (buttonElement.dataset.originalText) {
            buttonElement.textContent = buttonElement.dataset.originalText;
        }
    }
}

// Enhanced API call wrapper with better error handling
async function apiCall(endpoint, options = {}) {
    try {
        const response = await fetch(`${API_BASE}${endpoint}`, {
            headers: {
                'Content-Type': 'application/json',
                ...options.headers
            },
            ...options
        });
        
        if (!response.ok) {
            throw new Error(`HTTP ${response.status}: ${response.statusText}`);
        }
        
        const result = await response.json();
        
        if (!result.success) {
            throw new Error(result.error || 'Operation failed');
        }
        
        return result;
    } catch (error) {
        console.error('API call failed:', error);
        showNotification(`Error: ${error.message}`, 'error');
        throw error;
    }
}

// Enhanced progress monitoring
function startProgressMonitoring(operationType) {
    const progressElement = document.getElementById(`${operationType}Progress`);
    const statusElement = document.getElementById(`${operationType}Status`);
    let progress = 0;
    
    const interval = setInterval(async () => {
        try {
            const status = await apiCall('/operation/status');
            
            if (status.operation_complete) {
                progress = 100;
                if (progressElement) progressElement.style.width = '100%';
                if (statusElement) statusElement.textContent = 'Operation completed successfully!';
                
                setTimeout(() => {
                    closeModal();
                    operationInProgress = false;
                    updateSystemStatus('ready', 'System Ready');
                    loadDevices(); // Refresh device list
                    showNotification('Operation completed successfully!', 'success');
                }, 2000);
                
                clearInterval(interval);
            } else {
                progress = Math.min(progress + Math.random() * 10, 95);
                if (progressElement) progressElement.style.width = `${progress}%`;
                if (statusElement) statusElement.textContent = status.current_message || 'Processing...';
                
                // Add logs if available
                if (status.logs && status.logs.length > 0) {
                    const logsContainer = document.getElementById(`${operationType}Logs`);
                    if (logsContainer) {
                        status.logs.forEach(log => {
                            const logEntry = document.createElement('div');
                            logEntry.className = `log-entry ${log.level}`;
                            logEntry.innerHTML = `<span class="timestamp">[${log.timestamp}]</span> ${log.message}`;
                            logsContainer.appendChild(logEntry);
                            logsContainer.scrollTop = logsContainer.scrollHeight;
                        });
                    }
                }
            }
        } catch (error) {
            console.error('Error checking progress:', error);
            clearInterval(interval);
            operationInProgress = false;
            updateSystemStatus('error', 'Operation Failed');
            closeModal();
        }
    }, 2000);
}

// Enhanced backup operation with progress tracking
async function startBackup() {
    if (operationInProgress) {
        showNotification('Another operation is already in progress', 'warning');
        return;
    }
    
    if (devices.length === 0) {
        showNotification('No devices available for backup. Please discover devices first.', 'warning');
        return;
    }
    
    const button = event.target;
    setButtonLoading(button, true);
    
    try {
        operationInProgress = true;
        updateSystemStatus('processing', 'Creating backups...');
        
        showModal('Device Backup', `
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%" id="backupProgress"></div>
                </div>
                <p id="backupStatus">Preparing backup...</p>
            </div>
            <div id="backupLogs" class="log-container" style="max-height: 200px; overflow-y: auto; margin-top: 15px;"></div>
        `);
        
        const result = await apiCall('/backup/start', { method: 'POST' });
        
        startProgressMonitoring('backup');
        addActivityLog('Backup operation started', 'info');
        showNotification('Backup operation started', 'info');
        
    } catch (error) {
        operationInProgress = false;
        updateSystemStatus('error', 'Backup Failed');
        closeModal();
        addActivityLog(`Backup failed: ${error.message}`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Enhanced configuration deployment
async function deployConfiguration() {
    if (operationInProgress) {
        showNotification('Another operation is already in progress', 'warning');
        return;
    }
    
    const selectedDevices = getSelectedDevices();
    if (selectedDevices.length === 0) {
        showNotification('Please select at least one device', 'warning');
        return;
    }
    
    const configText = document.getElementById('configText').value.trim();
    if (!configText) {
        showNotification('Please enter configuration commands', 'warning');
        return;
    }
    
    const button = event.target;
    setButtonLoading(button, true);
    
    try {
        operationInProgress = true;
        updateSystemStatus('processing', 'Deploying configuration...');
        
        showModal('Configuration Deployment', `
            <div class="progress-container">
                <div class="progress-bar">
                    <div class="progress-fill" style="width: 0%" id="configProgress"></div>
                </div>
                <p id="configStatus">Preparing deployment...</p>
            </div>
            <div id="configLogs" class="log-container" style="max-height: 200px; overflow-y: auto; margin-top: 15px;"></div>
        `);
        
        const result = await apiCall('/config/deploy', {
            method: 'POST',
            body: JSON.stringify({
                devices: selectedDevices,
                config: configText
            })
        });
        
        startProgressMonitoring('config');
        addActivityLog(`Configuration deployment started for ${selectedDevices.length} devices`, 'info');
        showNotification('Configuration deployment started', 'info');
        
    } catch (error) {
        operationInProgress = false;
        updateSystemStatus('error', 'Deployment Failed');
        closeModal();
        addActivityLog(`Configuration deployment failed: ${error.message}`, 'error');
    } finally {
        setButtonLoading(button, false);
    }
}

// Enhanced device testing with individual feedback
async function testDevice(deviceName) {
    const deviceCard = event.target.closest('.device-card');
    const originalButton = event.target;
    
    setButtonLoading(originalButton, true);
    
    try {
        const result = await apiCall(`/devices/${deviceName}/test`, { method: 'POST' });
        
        // Update device card with test result
        const statusElement = deviceCard.querySelector('.device-status');
        if (result.reachable) {
            statusElement.textContent = 'ONLINE';
            statusElement.className = 'device-status online';
            showNotification(`Device ${deviceName} is reachable`, 'success');
        } else {
            statusElement.textContent = 'OFFLINE';
            statusElement.className = 'device-status offline';
            showNotification(`Device ${deviceName} is not reachable`, 'error');
        }
        
        addActivityLog(`Device test completed for ${deviceName}: ${result.reachable ? 'Reachable' : 'Not reachable'}`, result.reachable ? 'info' : 'warning');
        
    } catch (error) {
        showNotification(`Failed to test device ${deviceName}`, 'error');
        addActivityLog(`Device test failed for ${deviceName}: ${error.message}`, 'error');
    } finally {
        setButtonLoading(originalButton, false);
    }
}

// Enhanced error display in modals
function showErrorModal(title, error) {
    showModal(title, `
        <div class="error-container" style="text-align: center; padding: 20px;">
            <i class="fas fa-exclamation-triangle" style="font-size: 48px; color: #e74c3c; margin-bottom: 15px;"></i>
            <h3 style="color: #e74c3c; margin-bottom: 15px;">Operation Failed</h3>
            <p style="margin-bottom: 20px;">${error}</p>
            <button class="btn primary" onclick="closeModal()">Close</button>
        </div>
    `);
}

// Enhanced device selection helpers
function getSelectedDevices() {
    const checkboxes = document.querySelectorAll('.device-checkbox:checked');
    return Array.from(checkboxes).map(cb => cb.value);
}

function selectAllDevices() {
    const checkboxes = document.querySelectorAll('.device-checkbox');
    const selectAllBtn = event.target;
    const isSelectAll = selectAllBtn.textContent.includes('Select All');
    
    checkboxes.forEach(cb => cb.checked = isSelectAll);
    selectAllBtn.textContent = isSelectAll ? 'Deselect All' : 'Select All';
    
    showNotification(`${isSelectAll ? 'Selected' : 'Deselected'} all devices`, 'info');
}

// Enhanced auto-refresh functionality
function startAutoRefresh() {
    if (statusCheckInterval) {
        clearInterval(statusCheckInterval);
    }
    
    statusCheckInterval = setInterval(async () => {
        if (!operationInProgress && activeTab === 'devices') {
            try {
                await loadDevices();
            } catch (error) {
                console.error('Auto-refresh failed:', error);
            }
        }
    }, 30000); // Refresh every 30 seconds
}

// Add tooltips to interactive elements
function addTooltips() {
    const tooltipElements = [
        { selector: '[onclick*="discoverDevices"]', text: 'Scan network for devices using GNS3' },
        { selector: '[onclick*="startBackup"]', text: 'Create configuration backups for all devices' },
        { selector: '[onclick*="deployConfiguration"]', text: 'Deploy configuration to selected devices' },
        { selector: '[onclick*="testDevice"]', text: 'Test connectivity to this device' }
    ];
    
    tooltipElements.forEach(({ selector, text }) => {
        const elements = document.querySelectorAll(selector);
        elements.forEach(el => {
            if (!el.classList.contains('tooltip')) {
                el.classList.add('tooltip');
                const tooltip = document.createElement('span');
                tooltip.className = 'tooltiptext';
                tooltip.textContent = text;
                el.appendChild(tooltip);
            }
        });
    });
}

// Simulate API calls
function simulateApiCall(endpoint, data = {}, delay = 1000) {
    return new Promise((resolve, reject) => {
        setTimeout(() => {
            // Simulate random success/failure
            if (Math.random() > 0.1) { // 90% success rate
                resolve({ success: true, data: data });
            } else {
                reject(new Error('Network error'));
            }
        }, delay);
    });
}

function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// Individual device functions (placeholders)
function testDevice(deviceName) {
    addActivityLog(`Testing connectivity to ${deviceName}`, 'info');
}

function configureDevice(deviceName) {
    addActivityLog(`Opening configuration for ${deviceName}`, 'info');
}

function backupDevice(deviceName) {
    addActivityLog(`Backing up ${deviceName}`, 'info');
}

function downloadBackup(filename) {
    addActivityLog(`Downloading backup: ${filename}`, 'info');
}

function restoreBackup(filename) {
    if (confirm(`Are you sure you want to restore from ${filename}?`)) {
        addActivityLog(`Restoring from backup: ${filename}`, 'warning');
    }
}

function deleteBackup(filename) {
    if (confirm(`Are you sure you want to delete ${filename}?`)) {
        addActivityLog(`Deleted backup: ${filename}`, 'warning');
        loadBackupHistory();
    }
}

function scheduleBackup() {
    alert('Backup scheduling feature coming soon!');
}

function rotatePasswords() {
    enablePasswordAuth(); // Reuse the password function
}

function createSchedule() {
    alert('Password rotation scheduling feature coming soon!');
}

function createTemplate() {
    const name = prompt('Enter template name:');
    if (name) {
        addActivityLog(`Created new template: ${name}`, 'info');
        loadTemplates();
    }
}

function loadTemplate(name) {
    alert(`Loading template: ${name}`);
}

function useTemplate(name) {
    // Simulate loading template content
    const templates = {
        'Basic OSPF Configuration': `router ospf 1
network 192.168.1.0 0.0.0.255 area 0
exit`,
        'DHCP Server Setup': `ip dhcp pool LAN
network 192.168.1.0 255.255.255.0
default-router 192.168.1.1
dns-server 8.8.8.8
exit`,
        'Security Hardening': `line vty 0 4
login local
transport input ssh
exec-timeout 5 0
exit
ip ssh time-out 60
ip ssh authentication-retries 3`
    };
    
    document.getElementById('configCommands').value = templates[name] || '';
    addActivityLog(`Loaded template: ${name}`, 'info');
}

function refreshLogs() {
    loadLogs();
    addActivityLog('Logs refreshed', 'info');
}

function downloadLogs() {
    addActivityLog('Downloading system logs', 'info');
}
