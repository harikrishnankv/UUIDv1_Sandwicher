// UUID v1 Generator Tool - JavaScript

class UUIDGeneratorApp {
    constructor() {
        this.initializeEventListeners();
        this.loadingModal = null;
        this.warningModal = null;
        this.loadingTimeout = null;
        this.currentTimeDifference = 0;
        this.currentEstimatedCount = 0;
        this.pendingGenerationCallback = null;
        this.currentTaskId = null;
        this.initializeModal();
        this.initializeWarningModal();
    }

    initializeModal() {
        const modalElement = document.getElementById('loadingModal');
        if (modalElement && typeof bootstrap !== 'undefined') {
            try {
                this.loadingModal = new bootstrap.Modal(modalElement, {
                    backdrop: 'static',
                    keyboard: false
                });
                console.log('Bootstrap modal initialized successfully');
            } catch (error) {
                console.error('Error initializing Bootstrap modal:', error);
                this.loadingModal = null;
            }
        } else {
            console.log('Modal element not found or Bootstrap not available');
            this.loadingModal = null;
        }
    }

    initializeWarningModal() {
        const warningModalElement = document.getElementById('warningModal');
        if (warningModalElement && typeof bootstrap !== 'undefined') {
            try {
                this.warningModal = new bootstrap.Modal(warningModalElement, {
                    backdrop: 'static',
                    keyboard: false
                });
                console.log('Bootstrap warning modal initialized successfully');
            } catch (error) {
                console.error('Error initializing Bootstrap warning modal:', error);
                this.warningModal = null;
            }
        } else {
            console.log('Warning modal element not found or Bootstrap not available');
            this.warningModal = null;
        }
    }

    showWarningModal(timeDifference, estimatedCount, callback) {
        if (this.warningModal) {
            // Update modal content
            document.getElementById('warningTimeDelay').textContent = timeDifference.toFixed(6);
            document.getElementById('warningUuidCount').textContent = estimatedCount.toLocaleString();
            
            // Store callback for when user accepts risk
            this.pendingGenerationCallback = callback;
            
            // Show modal
            this.warningModal.show();
        } else {
            // If modal not available, just execute callback directly
            callback();
        }
    }

    acceptRiskAndContinue() {
        if (this.pendingGenerationCallback) {
            // Hide warning modal
            if (this.warningModal) {
                this.warningModal.hide();
            }
            
            // Execute the pending generation
            const callback = this.pendingGenerationCallback;
            this.pendingGenerationCallback = null;
            callback();
        }
    }

    checkTimeDelayAndProceed(callback) {
        if (this.currentTimeDifference > 3) {
            // Show warning modal for high time delays
            this.showWarningModal(this.currentTimeDifference, this.currentEstimatedCount, callback);
        } else {
            // Safe time delay, proceed directly
            callback();
        }
    }

    async cancelGeneration() {
        if (!this.currentTaskId) {
            this.showError('No active generation to cancel');
            return;
        }

        try {
            const response = await fetch(`/api/cancel-generation/${this.currentTaskId}`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                }
            });

            const data = await response.json();
            
            if (response.ok) {
                this.showSuccess('Generation cancelled successfully');
                // Hide progress container
                document.getElementById('progressContainer').style.display = 'none';
                // Reset current task
                this.currentTaskId = null;
            } else {
                this.showError(data.error || 'Failed to cancel generation');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        }
    }

    initializeEventListeners() {
        // Single UUID generation
        document.getElementById('generateSingleBtn').addEventListener('click', () => {
            this.generateSingleUUID();
        });

        // UUID version selector
        document.getElementById('uuidVersionSelect').addEventListener('change', () => {
            this.handleVersionChange();
        });

        // Range estimation
        document.getElementById('estimateBtn').addEventListener('click', () => {
            this.estimateRange();
        });

        // Range generation (legacy - kept for compatibility)
        const rangeForm = document.getElementById('rangeForm');
        if (rangeForm) {
            rangeForm.addEventListener('submit', (e) => {
                e.preventDefault();
                this.generateRange();
            });
        }

        // Fast range generation
        document.getElementById('generateRangeFastBtn').addEventListener('click', () => {
            this.generateRangeFast();
        });

        // UUID analysis
        document.getElementById('analyzeBtn').addEventListener('click', () => {
            this.analyzeUUID();
        });

        // Enter key for analysis
        document.getElementById('analyzeUuid').addEventListener('keypress', (e) => {
            if (e.key === 'Enter') {
                this.analyzeUUID();
            }
        });

        // Accept risk button for warning modal
        const acceptRiskBtn = document.getElementById('acceptRiskBtn');
        if (acceptRiskBtn) {
            acceptRiskBtn.addEventListener('click', () => {
                this.acceptRiskAndContinue();
            });
        }

        // Add page unload listener to clean up tasks
        window.addEventListener('beforeunload', () => {
            this.cleanupCurrentTask();
        });
    }

    handleVersionChange() {
        const version = document.getElementById('uuidVersionSelect').value;
        const nameContainer = document.getElementById('nameInputContainer');
        
        if (version === '3') {
            nameContainer.style.display = 'block';
        } else {
            nameContainer.style.display = 'none';
        }
    }

    // UUID validation regex
    validateUUID(uuidStr) {
        if (!uuidStr || typeof uuidStr !== 'string') return false;
        const uuidPattern = /^[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$/i;
        return uuidPattern.test(uuidStr.trim());
    }

    // Text validation for UUID v3 name
    validateTextInput(text, maxLength = 1000) {
        if (!text || typeof text !== 'string') return false;
        const trimmed = text.trim();
        if (trimmed.length === 0 || trimmed.length > maxLength) return false;
        // Block potentially dangerous characters
        if (/[<>"']/.test(trimmed)) return false;
        // Allow printable characters
        return /^[\x20-\x7E]+$/.test(trimmed);
    }

    async generateSingleUUID() {
        try {
            const version = document.getElementById('uuidVersionSelect').value;
            const name = document.getElementById('nameInput').value.trim();
            
            // Validate version
            if (!['1', '2', '3', '4'].includes(version)) {
                this.showError('Invalid UUID version');
                return;
            }
            
            console.log('Starting UUID generation for version:', version);
            
            let loadingMessage = '';
            switch(version) {
                case '1':
                    loadingMessage = 'Generating UUID v1 - Time-based (MAC address + timestamp)...';
                    break;
                case '2':
                    loadingMessage = 'Generating UUID v2 - DCE Security (time-based + POSIX UID/GID)...';
                    break;
                case '3':
                    if (!name) {
                        this.showError('Please enter a name for UUID v3 generation');
                        return;
                    }
                    // Validate text input
                    if (!this.validateTextInput(name, 1000)) {
                        this.showError('Invalid name format. Name must be text only, 1-1000 characters, and cannot contain special characters like < > " \'');
                        return;
                    }
                    loadingMessage = 'Generating UUID v3 - Name-based using MD5 hash...';
                    break;
                case '4':
                    loadingMessage = 'Generating UUID v4 - Random (cryptographically secure)...';
                    break;
            }
            
            this.showLoading(`Generating UUID v${version}...`, loadingMessage);
            
            const requestBody = {
                version: version
            };
            
            if (version === '3' && name) {
                requestBody.name = name;
                const namespace = document.getElementById('namespaceSelect').value;
                // Validate namespace
                if (!['DNS', 'URL', 'OID', 'X500'].includes(namespace)) {
                    this.showError('Invalid namespace');
                    return;
                }
                requestBody.namespace = namespace;
            }
            
            const response = await fetch('/api/generate-single', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            console.log('Response:', response.status, data);
            
            if (response.ok) {
                this.displaySingleResult(data);
            } else {
                this.showError(data.error || 'Failed to generate UUID');
            }
        } catch (error) {
            console.error('Error generating UUID:', error);
            this.showError('Network error: ' + error.message);
        } finally {
            console.log('Finally block - hiding loading...');
            this.hideLoading();
        }
    }

    async estimateRange() {
        console.log('estimateRange function called');
        const startUuid = document.getElementById('startUuid').value.trim();
        const endUuid = document.getElementById('endUuid').value.trim();

        if (!startUuid || !endUuid) {
            this.showError('Please enter both start and end UUIDs');
            return;
        }

        // Validate UUID formats
        if (!this.validateUUID(startUuid)) {
            this.showError('Invalid start UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
            return;
        }
        if (!this.validateUUID(endUuid)) {
            this.showError('Invalid end UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
            return;
        }
        
        console.log('Start UUID:', startUuid);
        console.log('End UUID:', endUuid);

        try {
            this.showLoading('Estimating Range', 'Analyzing UUID range parameters...', false);
            
            const response = await fetch('/api/estimate', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    start_uuid: startUuid,
                    end_uuid: endUuid,
                    step_seconds: 0.0000001
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.displayEstimationResults(data);
            } else {
                this.showError(data.error || 'Failed to estimate range');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async generateRange() {
        const startUuid = document.getElementById('startUuid').value.trim();
        const endUuid = document.getElementById('endUuid').value.trim();

        if (!startUuid || !endUuid) {
            this.showError('Please enter both start and end UUIDs');
            return;
        }

        try {
            // Ensure we have estimation data
            await this.ensureEstimation(startUuid, endUuid);
        } catch {
            return; // estimation failed and was surfaced to user
        }

        // Check time delay and proceed with generation
        this.checkTimeDelayAndProceed(async () => {
            try {
                this.showLoading('Generating UUID Range', 'Initializing UUID generation process...', false, true);
                
                const response = await fetch('/api/generate-range', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        start_uuid: startUuid,
                        end_uuid: endUuid,
                        step_seconds: 0.0000001,
                        max_count: 1000
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    this.displayRangeResults(data);
                } else {
                    this.showError(data.error || 'Failed to generate UUID range');
                }
            } catch (error) {
                this.showError('Network error: ' + error.message);
            } finally {
                this.hideLoading();
            }
        });
    }

    async generateRangeFast() {
        const startUuid = document.getElementById('startUuid').value.trim();
        const endUuid = document.getElementById('endUuid').value.trim();

        if (!startUuid || !endUuid) {
            this.showError('Please enter both start and end UUIDs');
            return;
        }

        // Validate UUID formats
        if (!this.validateUUID(startUuid)) {
            this.showError('Invalid start UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
            return;
        }
        if (!this.validateUUID(endUuid)) {
            this.showError('Invalid end UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
            return;
        }

        try {
            // Ensure we have estimation data
            await this.ensureEstimation(startUuid, endUuid);
        } catch {
            return; // estimation failed and was surfaced to user
        }

        // Check time delay and proceed with generation
        this.checkTimeDelayAndProceed(async () => {
            try {
                // Start background generation without loading popup
                const response = await fetch('/api/generate-range-fast', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify({
                        start_uuid: startUuid,
                        end_uuid: endUuid
                    })
                });

                const data = await response.json();
                
                if (response.ok) {
                    // Start monitoring the background task
                    this.startFastGenerationMonitoring(data.task_id);
                } else {
                    this.showError(data.error || 'Failed to start fast generation');
                }
            } catch (error) {
                this.showError('Network error: ' + error.message);
            }
        });
    }

    async ensureEstimation(startUuid, endUuid) {
        if (this.currentTimeDifference && this.currentEstimatedCount) {
            return; // already have estimation
        }
        try {
            const response = await fetch('/api/estimate', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({ start_uuid: startUuid, end_uuid: endUuid, step_seconds: 0.0000001 })
            });
            const data = await response.json();
            if (response.ok) {
                // Set values so downstream checks work
                if (typeof data.start_timestamp_hex === 'number' && typeof data.end_timestamp_hex === 'number') {
                    const diffIntervals = Math.abs(data.end_timestamp_hex - data.start_timestamp_hex);
                    const diffSeconds = diffIntervals / 10000000;
                    this.currentTimeDifference = diffSeconds;
                }
                this.currentEstimatedCount = data.total_possible || 0;
            } else {
                throw new Error(data.error || 'Failed to estimate range');
            }
        } catch (e) {
            this.showError('Range estimation failed: ' + e.message);
            throw e;
        }
    }

    startFastGenerationMonitoring(taskId) {
        // Show progress container
        const progressContainer = document.getElementById('progressContainer');
        const rangeResults = document.getElementById('rangeResults');
        
        progressContainer.style.display = 'block';
        rangeResults.style.display = 'none';
        
        // Store current task ID for cancellation
        this.currentTaskId = taskId;
        
        // Update progress text
        this.updateProgress(0, 'Starting fast UUID generation...');
        
        // Start progress monitoring
        this.monitorFastGenerationProgress(taskId);
    }

    async monitorFastGenerationProgress(taskId) {
        const progressContainer = document.getElementById('progressContainer');
        const rangeResults = document.getElementById('rangeResults');
        
        // Enhanced XHR-based progress monitoring with real-time updates
        let retryCount = 0;
        const maxRetries = 5;
        const baseInterval = 100; // Start with 100ms for very responsive updates
        
        try {
            while (true) {
                try {
                    // Use XHR for better control and error handling
                    const response = await this.makeXHRRequest(`/api/generation-status/${taskId}`);
                    const task = response.data;
                    
                    if (response.success) {
                        const { status, progress, count, error, message } = task;
                        
                        if (status === 'completed') {
                            // Generation complete
                            this.updateProgress(100, `Fast generation complete! Generated ${count.toLocaleString()} UUIDs.`);
                            
                            setTimeout(() => {
                                progressContainer.style.display = 'none';
                                this.showFastGenerationDownload(taskId, count, message);
                                // Reset current task
                                this.currentTaskId = null;
                            }, 1000);
                            break;
                            
                        } else if (status === 'error') {
                            // Generation failed
                            this.showError(`Fast generation failed: ${error}`);
                            progressContainer.style.display = 'none';
                            // Reset current task
                            this.currentTaskId = null;
                            break;
                            
                        } else if (status === 'cancelled') {
                            // Generation cancelled
                            this.showSuccess('Generation cancelled successfully');
                            progressContainer.style.display = 'none';
                            // Reset current task
                            this.currentTaskId = null;
                            break;
                            
                        } else if (status === 'generating') {
                            // Update progress with live percentage and enhanced display
                            const progressPercent = progress || 0;
                            const countDisplay = count ? count.toLocaleString() : '0';
                            
                            // Enhanced progress message with more details
                            const progressMessage = `Generating UUIDs... ${countDisplay} generated (${progressPercent.toFixed(1)}%)`;
                            this.updateProgress(progressPercent, progressMessage);
                            
                            // Update progress bar with smooth animation
                            this.updateProgressBar(progressPercent);
                            
                            // Add live timestamp for real-time feel
                            this.updateProgressTimestamp();
                            
                            // Reset retry count on successful update
                            retryCount = 0;
                        }
                        
                        // Dynamic interval based on progress - faster updates when progress is changing
                        const interval = this.calculateProgressInterval(progress || 0, baseInterval);
                        await new Promise(resolve => setTimeout(resolve, interval));
                        
                    } else {
                        throw new Error(response.error || 'Failed to get generation status');
                    }
                    
                } catch (xhrError) {
                    retryCount++;
                    console.warn(`Progress check attempt ${retryCount} failed:`, xhrError);
                    
                    if (retryCount >= maxRetries) {
                        this.showError(`Failed to monitor progress after ${maxRetries} attempts: ${xhrError.message}`);
                        progressContainer.style.display = 'none';
                        break;
                    }
                    
                    // Exponential backoff for retries
                    const retryDelay = Math.min(1000 * Math.pow(2, retryCount - 1), 5000);
                    await new Promise(resolve => setTimeout(resolve, retryDelay));
                }
            }
        } catch (error) {
            this.showError('Error monitoring progress: ' + error.message);
            progressContainer.style.display = 'none';
        }
    }

    // Enhanced XHR request method with better error handling
    makeXHRRequest(url, options = {}) {
        return new Promise((resolve, reject) => {
            const xhr = new XMLHttpRequest();
            
            xhr.open('GET', url, true);
            xhr.timeout = 10000; // 10 second timeout
            
            // Set headers
            xhr.setRequestHeader('Content-Type', 'application/json');
            xhr.setRequestHeader('X-Requested-With', 'XMLHttpRequest');
            
            xhr.onload = function() {
                if (xhr.status >= 200 && xhr.status < 300) {
                    try {
                        const data = JSON.parse(xhr.responseText);
                        resolve({
                            success: true,
                            data: data,
                            status: xhr.status,
                            headers: xhr.getAllResponseHeaders()
                        });
                    } catch (parseError) {
                        resolve({
                            success: false,
                            error: 'Failed to parse response: ' + parseError.message,
                            status: xhr.status
                        });
                    }
                } else {
                    resolve({
                        success: false,
                        error: `HTTP ${xhr.status}: ${xhr.statusText}`,
                        status: xhr.status
                    });
                }
            };
            
            xhr.onerror = function() {
                resolve({
                    success: false,
                    error: 'Network error occurred',
                    status: 0
                });
            };
            
            xhr.ontimeout = function() {
                resolve({
                    success: false,
                    error: 'Request timeout',
                    status: 0
                });
            };
            
            xhr.send();
        });
    }

    // Calculate dynamic interval based on progress for optimal responsiveness
    calculateProgressInterval(progress, baseInterval) {
        if (progress < 10) {
            return baseInterval; // Very fast updates at the beginning
        } else if (progress < 50) {
            return baseInterval * 2; // Fast updates during early progress
        } else if (progress < 90) {
            return baseInterval * 3; // Moderate updates during middle progress
        } else if (progress < 99) {
            return baseInterval * 4; // Slower updates near completion
        } else {
            return baseInterval * 5; // Slowest updates when almost done
        }
    }

    // Add live timestamp to progress display
    updateProgressTimestamp() {
        const progressText = document.getElementById('progressText');
        if (progressText) {
            const now = new Date();
            const timeString = now.toLocaleTimeString();
            const existingText = progressText.textContent;
            
            // Only update if it doesn't already have a timestamp
            if (!existingText.includes('Last updated:')) {
                progressText.innerHTML = `${existingText} <small class="text-muted">(Last updated: ${timeString})</small>`;
            }
        }
    }

    showFastGenerationDownload(taskId, count, message) {
        const rangeResults = document.getElementById('rangeResults');
        const summaryDiv = document.getElementById('rangeSummary');
        
        summaryDiv.innerHTML = `
            <div class="row">
                <div class="col-md-12">
                    <div class="alert alert-success">
                        <h6><i class="fas fa-check-circle me-2"></i>Fast Generation Complete!</h6>
                        <p><strong>Generated:</strong> ${count.toLocaleString()} UUIDs</p>
                        <p><strong>Message:</strong> ${message}</p>
                        <p><strong>Task ID:</strong> <code>${taskId}</code></p>
                        <p class="mb-0"><small class="text-muted">All UUIDs generated using optimized fast method!</small></p>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="mb-3">
                        <div class="alert alert-info">
                            <h6><i class="fas fa-search me-2"></i>Search UUID in Generated List</h6>
                            <p class="mb-2">Search for a specific UUID in the generated file. Works even after download!</p>
                            <div class="input-group">
                                <input type="text" class="form-control" id="searchUuidInput" placeholder="Enter UUID to search for (e.g., 08df43ec-f8d5-11ef-8a38-aedb2c11800f)">
                                <button class="btn btn-primary" onclick="window.uuidApp.searchUuidInFile('${taskId || ''}')">
                                    <i class="fas fa-search me-1"></i>Search
                                </button>
                            </div>
                            <div id="searchResults" class="mt-2" style="display: none;"></div>
                        </div>
                    </div>
                </div>
            </div>
            <div class="row">
                <div class="col-md-12">
                    <div class="d-grid gap-2">
                        <button class="btn btn-success btn-lg" onclick="window.uuidApp.downloadFile('${taskId}')">
                            <i class="fas fa-download me-2"></i>Download All UUIDs
                        </button>
                        <button class="btn btn-outline-secondary" onclick="window.uuidApp.cleanupTask('${taskId}')">
                            <i class="fas fa-trash me-2"></i>Clean Up Task
                        </button>
                    </div>
                </div>
            </div>
        `;
        
        rangeResults.style.display = 'block';
        rangeResults.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    async searchUuidInFile(taskId = null) {
        const searchInput = document.getElementById('searchUuidInput');
        const searchResults = document.getElementById('searchResults');
        const searchUuid = searchInput.value.trim();
        
        if (!searchUuid) {
            this.showError('Please enter a UUID to search for');
            return;
        }
        
        try {
            this.showLoading('Searching...', 'Searching for UUID in generated file...');
            
            // Build request body - task_id is optional, will search in latest file if not provided
            const requestBody = {
                search_uuid: searchUuid
            };
            if (taskId) {
                requestBody.task_id = taskId;
            }
            
            const response = await fetch('/api/search-uuid', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(requestBody)
            });

            const data = await response.json();
            
            if (response.ok) {
                if (data.found) {
                    searchResults.innerHTML = `
                        <div class="alert alert-success">
                            <i class="fas fa-check-circle me-2"></i>
                            <strong>UUID Found!</strong> ${data.message}
                        </div>
                    `;
                } else {
                    searchResults.innerHTML = `
                        <div class="alert alert-warning">
                            <i class="fas fa-exclamation-triangle me-2"></i>
                            <strong>UUID Not Found:</strong> ${data.message}
                        </div>
                    `;
                }
                searchResults.style.display = 'block';
            } else {
                this.showError(data.error || 'Search failed');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    async analyzeUUID() {
        const uuidStr = document.getElementById('analyzeUuid').value.trim();

        if (!uuidStr) {
            this.showError('Please enter a UUID to analyze');
            return;
        }

        // Validate UUID format
        if (!this.validateUUID(uuidStr)) {
            this.showError('Invalid UUID format. UUID must be in format: xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx');
            return;
        }

        try {
            this.showLoading('Analyzing UUID...', 'Extracting timestamp and metadata...');
            
            const response = await fetch('/api/analyze', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({
                    uuid: uuidStr
                })
            });

            const data = await response.json();
            
            if (response.ok) {
                this.displayAnalysisResults(data);
            } else {
                this.showError(data.error || 'Failed to analyze UUID');
            }
        } catch (error) {
            this.showError('Network error: ' + error.message);
        } finally {
            this.hideLoading();
        }
    }

    displaySingleResult(data) {
        console.log('Displaying single result:', data);
        const resultDiv = document.getElementById('singleResult');
        const uuidElement = document.getElementById('singleUuid');
        
        if (!resultDiv || !uuidElement) {
            console.error('Required elements not found');
            return;
        }
        
        uuidElement.textContent = data.uuid;
        
        // Update the result display to show version information
        const resultContent = resultDiv.querySelector('.alert');
        if (resultContent) {
            let versionInfo = `Generated UUID v${data.version || '1'}:`;
            if (data.version === '3' && data.name) {
                versionInfo += ` (based on name: "${data.name}")`;
            }
            
            resultContent.querySelector('h6').innerHTML = versionInfo;
        }
        
        resultDiv.style.display = 'block';
        
        // Scroll to result
        resultDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    displayEstimationResults(data) {
        const resultsDiv = document.getElementById('estimationResults');
        const detailsDiv = document.getElementById('estimationDetails');
        
        if (data.error) {
            detailsDiv.innerHTML = `<div class="text-danger">${data.error}</div>`;
        } else {
            // Calculate time difference in seconds
            let timeDiffSeconds = 0;
            let timeClass = '';
            let warningIcon = '';
            
            if (typeof data.start_timestamp_hex === 'number' && typeof data.end_timestamp_hex === 'number') {
                const diffIntervals = Math.abs(data.end_timestamp_hex - data.start_timestamp_hex);
                timeDiffSeconds = diffIntervals / 10000000; // convert to seconds
                
                // Color coding based on time difference
                if (timeDiffSeconds <= 3) {
                    timeClass = 'time-green';
                    warningIcon = '<i class="fas fa-check-circle text-success warning-icon"></i>';
                } else if (timeDiffSeconds <= 5) {
                    timeClass = 'time-yellow';
                    warningIcon = '<i class="fas fa-exclamation-triangle text-warning warning-icon"></i>';
                } else {
                    timeClass = 'time-red';
                    warningIcon = '<i class="fas fa-skull text-danger warning-icon"></i>';
                }
            }
            
            detailsDiv.innerHTML = `
                <div class="estimation-detail">
                    <span class="estimation-label">Estimated UUID Count:</span>
                    <span class="estimation-value">${(data.total_possible || 0).toLocaleString()}</span>
                </div>
                <div class="estimation-detail">
                    <span class="estimation-label">Time Difference (Seconds):</span>
                    <span class="estimation-value ${timeClass}">${timeDiffSeconds.toFixed(6)}${warningIcon}</span>
                </div>
                <div class="estimation-detail">
                    <span class="estimation-label">Estimated Generation Time:</span>
                    <span class="estimation-value">${data.estimated_time_human || 'N/A'}</span>
                </div>
            `;
            
            // Store time difference for later use in generation
            this.currentTimeDifference = timeDiffSeconds;
            this.currentEstimatedCount = data.total_possible;
        }
        
        resultsDiv.style.display = 'block';
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    displayRangeResults(data) {
        const resultsDiv = document.getElementById('rangeResults');
        const summaryDiv = document.getElementById('rangeSummary');
        const tableBody = document.getElementById('rangeTableBody');
        
        // Update summary
        summaryDiv.innerHTML = `
            <div class="row">
                <div class="col-md-3">
                    <strong>Total Generated:</strong> ${data.total_generated.toLocaleString()}
                </div>
                <div class="col-md-3">
                    <strong>Has More:</strong> ${data.has_more ? 'Yes' : 'No'}
                </div>
                <div class="col-md-3">
                    <strong>Start Time:</strong> ${new Date(data.start_time * 1000).toLocaleString()}
                </div>
                <div class="col-md-3">
                    <strong>End Time:</strong> ${new Date(data.end_time * 1000).toLocaleString()}
                </div>
            </div>
        `;
        
        // Clear and populate table
        tableBody.innerHTML = '';
        
        data.uuids.forEach(uuidData => {
            const row = document.createElement('tr');
            row.innerHTML = `
                <td>${uuidData.index}</td>
                <td><code>${uuidData.uuid}</code></td>
                <td>${uuidData.timestamp.toFixed(6)}</td>
                <td>${new Date(uuidData.datetime).toLocaleString()}</td>
                <td>
                    <button class="btn btn-sm btn-outline-secondary" onclick="copyToClipboard('${uuidData.uuid}')">
                        <i class="fas fa-copy"></i>
                    </button>
                </td>
            `;
            tableBody.appendChild(row);
        });
        
        resultsDiv.style.display = 'block';
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'start' });
    }

    displayAnalysisResults(data) {
        const resultsDiv = document.getElementById('analysisResults');
        const detailsDiv = document.getElementById('analysisDetails');
        
        if (data.error) {
            detailsDiv.innerHTML = `<div class="text-danger">${data.error}</div>`;
        } else {
            // Update the analysis header to show version
            const analysisHeader = resultsDiv.querySelector('h6');
            if (analysisHeader) {
                analysisHeader.innerHTML = `<i class="fas fa-info-circle me-2"></i>UUID Analysis - Version ${data.version || 'Unknown'}`;
            }
            detailsDiv.innerHTML = `
                <div class="analysis-grid">
                    <div class="analysis-item">
                        <div class="analysis-label">UUID</div>
                        <div class="analysis-value">
                            ${data.uuid}
                            <button class="btn btn-sm btn-outline-secondary ms-2" onclick="copyToClipboard('${data.uuid}')">
                                <i class="fas fa-copy"></i>
                            </button>
                        </div>
                        <div class="analysis-desc">The complete UUID string in standard format</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Version</div>
                        <div class="analysis-value">${data.version}</div>
                        <div class="analysis-desc">${data.version_desc}</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Variant</div>
                        <div class="analysis-value">${data.variant}</div>
                        <div class="analysis-desc">UUID variant specification (code: ${data.variant_code})</div>
                    </div>
                    
                    ${data.timestamp ? `
                    <div class="analysis-item">
                        <div class="analysis-label">Timestamp</div>
                        <div class="analysis-value">${data.timestamp.toFixed(6)}</div>
                        <div class="analysis-desc">Unix timestamp in seconds since epoch</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Date (UTC)</div>
                        <div class="analysis-value">${data.date_utc}</div>
                        <div class="analysis-desc">Date in Coordinated Universal Time</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Date (IST)</div>
                        <div class="analysis-value">${data.date_ist}</div>
                        <div class="analysis-desc">Date in Indian Standard Time (UTC+5:30)</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Time (UTC)</div>
                        <div class="analysis-value">${data.time_utc}</div>
                        <div class="analysis-desc">Time in Coordinated Universal Time</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Time (IST)</div>
                        <div class="analysis-value">${data.time_ist}</div>
                        <div class="analysis-desc">Time in Indian Standard Time (UTC+5:30)</div>
                    </div>
                    ` : `
                    <div class="analysis-item">
                        <div class="analysis-label">Timestamp</div>
                        <div class="analysis-value text-muted">Not Applicable</div>
                        <div class="analysis-desc">This UUID version does not contain timestamp information</div>
                    </div>
                    `}
                    
                    ${data.version !== '3' && data.version !== '4' ? `
                    <div class="analysis-item">
                        <div class="analysis-label">Node (MAC Address)</div>
                        <div class="analysis-value">${data.node}</div>
                        <div class="analysis-desc">${data.node_desc}</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Clock Sequence</div>
                        <div class="analysis-value">${data.clock_seq}</div>
                        <div class="analysis-desc">${data.clock_seq_desc}</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Clock Sequence (High)</div>
                        <div class="analysis-value">${data.clock_seq_hi}</div>
                        <div class="analysis-desc">High byte of clock sequence with variant bits</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Clock Sequence (Low)</div>
                        <div class="analysis-value">${data.clock_seq_low}</div>
                        <div class="analysis-desc">Low byte of clock sequence</div>
                    </div>
                    
                    ${data.timestamp ? `
                    <div class="analysis-item">
                        <div class="analysis-label">Time Low</div>
                        <div class="analysis-value">${data.time_low}</div>
                        <div class="analysis-desc">Lower 32 bits of timestamp</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Time Mid</div>
                        <div class="analysis-value">${data.time_mid}</div>
                        <div class="analysis-desc">Middle 16 bits of timestamp</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Time High</div>
                        <div class="analysis-value">${data.time_hi}</div>
                        <div class="analysis-desc">Upper 12 bits of timestamp (without version)</div>
                    </div>
                    
                    <div class="analysis-item">
                        <div class="analysis-label">Time High + Version</div>
                        <div class="analysis-value">${data.time_hi_version}</div>
                        <div class="analysis-desc">Upper 16 bits including version (4 bits)</div>
                    </div>
                    ` : ''}
                    ` : data.version === '4' ? `
                    <div class="analysis-item">
                        <div class="analysis-label">Note</div>
                        <div class="analysis-value text-info"><i class="fas fa-info-circle me-2"></i>UUID v4 is Random</div>
                        <div class="analysis-desc">UUID v4 uses random bits. Fields like "node", "clock sequence", and "time" are random data, not actual MAC addresses, clock sequences, or timestamps.</div>
                    </div>
                    ` : ''}
                </div>
            `;
        }
        
        resultsDiv.style.display = 'block';
        
        // Show version-specific analysis
        this.displayVersionSpecificAnalysis(data);
        
        resultsDiv.scrollIntoView({ behavior: 'smooth', block: 'center' });
    }

    displayVersionSpecificAnalysis(data) {
        const versionAnalysisDiv = document.getElementById('versionAnalysis');
        const versionDetailsDiv = document.getElementById('versionDetails');
        
        if (!versionAnalysisDiv || !versionDetailsDiv) {
            console.error('Version analysis elements not found');
            return;
        }
        
        const version = parseInt(data.version);
        let versionContent = '';
        
        switch(version) {
            case 1:
                versionContent = this.getVersion1Analysis(data);
                break;
            case 2:
                versionContent = this.getVersion2Analysis(data);
                break;
            case 3:
                versionContent = this.getVersion3Analysis(data);
                break;
            case 4:
                versionContent = this.getVersion4Analysis(data);
                break;
            default:
                versionContent = this.getGenericAnalysis(data);
        }
        
        versionDetailsDiv.innerHTML = versionContent;
        versionAnalysisDiv.style.display = 'block';
    }

    getVersion1Analysis(data) {
        return `
            <div class="version-analysis-grid">
                <div class="version-analysis-section">
                    <h6 class="text-primary"><i class="fas fa-clock me-2"></i>Time-based Features</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Timestamp Precision:</span>
                        <span class="version-value">100 nanoseconds</span>
                        <span class="version-desc">UUID v1 uses 100-nanosecond precision timestamps</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Epoch Base:</span>
                        <span class="version-value">October 15, 1582</span>
                        <span class="version-desc">Gregorian calendar reform date (RFC 4122)</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">MAC Address:</span>
                        <span class="version-value">${data.node}</span>
                        <span class="version-desc">Unique hardware identifier (may be randomized for privacy)</span>
                    </div>
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-success"><i class="fas fa-shield-alt me-2"></i>Security & Privacy</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Clock Sequence:</span>
                        <span class="version-value">${data.clock_seq}</span>
                        <span class="version-desc">Prevents duplicates when system clock goes backwards</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Collision Resistance:</span>
                        <span class="version-value">Very High</span>
                        <span class="version-desc">Extremely low probability of duplicate generation</span>
                    </div>
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-info"><i class="fas fa-cogs me-2"></i>Technical Details</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Total Bits:</span>
                        <span class="version-value">128 bits</span>
                        <span class="version-desc">Standard UUID length</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Version Bits:</span>
                        <span class="version-value">4 bits (position 48-51)</span>
                        <span class="version-desc">Always set to 0001 for v1</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Variant Bits:</span>
                        <span class="version-value">2 bits (position 64-65)</span>
                        <span class="version-desc">Always set to 10 for RFC 4122</span>
                    </div>
                </div>
                
                <div class="version-analysis-section sandwich-attack-section">
                    <h6 class="text-danger"><i class="fas fa-skull me-2"></i>Sandwich Attack Possibility</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Risk Level:</span>
                        <span class="version-value text-danger fw-bold">${data.sandwich_attack_possibility || 'HIGH - Time-based UUIDs are vulnerable to sandwich attacks'}</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Description:</span>
                        <span class="version-value">${data.sandwich_attack_description || 'UUID v1 timestamps are predictable and can be manipulated to create collisions or predict future UUIDs'}</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Risk:</span>
                        <span class="version-value">${data.sandwich_attack_risk || 'Attackers can generate UUIDs with timestamps before and after a target UUID, potentially causing database conflicts'}</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Exploitation:</span>
                        <span class="version-value">${data.sandwich_attack_exploitation || 'Use UUID SANDWICHER tool to generate payloads for testing and exploitation'}</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Learn More:</span>
                        <a href="${data.sandwich_attack_article_url || 'https://medium.com/@securityresearcher/uuid-sandwich-attacks-time-based-vulnerabilities-in-distributed-systems-1234567890ab'}" target="_blank" class="btn btn-outline-danger btn-sm mt-2">
                            <i class="fas fa-book-open me-1"></i>Read Article
                        </a>
                    </div>
                </div>
                
                <div class="version-analysis-section lab-section">
                    <h6 class="text-primary"><i class="fas fa-flask me-2"></i>Practice Lab</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Hands-on Practice:</span>
                        <span class="version-value">Test your UUID v1 exploitation skills with our dedicated vulnerable lab</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Lab Challenge:</span>
                        <span class="version-value">Find the admin's flag file by exploiting predictable UUID v1 patterns</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Access Lab:</span>
                        <a href="${data.sandwich_attack_lab_url || 'https://github.com/harikrishnankv/file-storage-lab'}" target="_blank" class="btn btn-outline-primary btn-sm mt-2">
                            <i class="fab fa-github me-1"></i>File Storage Lab
                        </a>
                    </div>
                </div>
            </div>
        `;
    }

    getVersion2Analysis(data) {
        return `
            <div class="version-analysis-grid">
                <div class="version-analysis-section">
                    <h6 class="text-warning"><i class="fas fa-user-shield me-2"></i>DCE Security Features</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Security Model:</span>
                        <span class="version-value">DCE Security</span>
                        <span class="version-desc">Distributed Computing Environment security model</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">POSIX Integration:</span>
                        <span class="version-value">UID/GID Support</span>
                        <span class="version-desc">Integrates with POSIX user and group identifiers</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Domain:</span>
                        <span class="version-value">${data.dce_domain || 'Security Domain'}</span>
                        <span class="version-desc">DCE Security domain classification</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Security Identifier:</span>
                        <span class="version-value">${data.security_identifier || 'N/A'}</span>
                        <span class="version-desc">DCE Security domain identifier</span>
                    </div>
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-success"><i class="fas fa-users me-2"></i>POSIX Information</h6>
                    <div class="version-detail-item">
                        <span class="version-label">User/Group Info:</span>
                        <span class="version-value">${data.posix_uid_gid || 'N/A'}</span>
                        <span class="version-desc">POSIX UID and GID information</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Clock Sequence Purpose:</span>
                        <span class="version-value">DCE Security</span>
                        <span class="version-desc">Used for DCE Security domain identification</span>
                    </div>
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-info"><i class="fas fa-info-circle me-2"></i>Technical Details</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Version Bits:</span>
                        <span class="version-value">4 bits (position 48-51)</span>
                        <span class="version-desc">Set to 0001 (same as v1, detected by patterns)</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Variant Bits:</span>
                        <span class="version-value">2 bits (position 64-65)</span>
                        <span class="version-desc">Set to 10 for DCE Security (RFC 4122)</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Use Cases:</span>
                        <span class="version-value">Secure Distributed Systems</span>
                        <span class="version-desc">Enterprise security, POSIX integration, DCE environments</span>
                    </div>
                </div>
                
                ${data.detection_note ? `
                <div class="version-analysis-section">
                    <h6 class="text-primary"><i class="fas fa-search me-2"></i>Detection Analysis</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Detection Note:</span>
                        <span class="version-value">${data.detection_note}</span>
                        <span class="version-desc">How this UUID was identified as v2</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Confidence Level:</span>
                        <span class="version-value">${data.confidence_level || 'N/A'}</span>
                        <span class="version-desc">Reliability of the v2 detection</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Analysis Method:</span>
                        <span class="version-value">${data.analysis_method || 'N/A'}</span>
                        <span class="version-desc">Technique used for pattern detection</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Recommendation:</span>
                        <span class="version-value">${data.recommendation || 'N/A'}</span>
                        <span class="version-desc">Suggested usage approach</span>
                    </div>
                </div>
                ` : ''}
            </div>
        `;
    }

    getVersion3Analysis(data) {
        // Only show certain/definitive information about UUID v3
        return `
            <div class="version-analysis-grid">
                <div class="version-analysis-section">
                    <h6 class="text-success"><i class="fas fa-hashtag me-2"></i>UUID v3 - Name-based Generation</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Hash Algorithm:</span>
                        <span class="version-value">MD5</span>
                        <span class="version-desc">Uses MD5 hash of namespace + name (128-bit output)</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Deterministic:</span>
                        <span class="version-value">Yes</span>
                        <span class="version-desc">Same input always produces same UUID</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Version Bits:</span>
                        <span class="version-value">0011 (v3)</span>
                        <span class="version-desc">4 bits at position 48-51 identify this as UUID v3</span>
                    </div>
                    ${data.used_namespace ? `
                    <div class="version-detail-item">
                        <span class="version-label">Namespace (User Specified):</span>
                        <span class="version-value">${data.used_namespace}</span>
                        <span class="version-desc">${data.used_namespace_description || `Using ${data.used_namespace} namespace`}</span>
                    </div>
                    ${data.used_namespace_uuid ? `
                    <div class="version-detail-item">
                        <span class="version-label">Namespace UUID:</span>
                        <span class="version-value"><code>${data.used_namespace_uuid}</code></span>
                        <span class="version-desc">The UUID of the namespace used for generation</span>
                    </div>
                    ` : ''}
                    ` : ''}
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-info"><i class="fas fa-cogs me-2"></i>Hash Components</h6>
                    ${data.hash_components ? `
                    <div class="version-detail-item">
                        <span class="version-label">Hash Low (32 bits):</span>
                        <span class="version-value"><code>${data.hash_components.hash_low_32bits}</code></span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Hash Mid (16 bits):</span>
                        <span class="version-value"><code>${data.hash_components.hash_mid_16bits}</code></span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Hash High (12 bits):</span>
                        <span class="version-value"><code>${data.hash_components.hash_hi_12bits}</code></span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Hash Clock (14 bits):</span>
                        <span class="version-value"><code>${data.hash_components.hash_clock_14bits}</code></span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Hash Node (48 bits):</span>
                        <span class="version-value"><code>${data.hash_components.hash_node_48bits}</code></span>
                    </div>
                    <div class="alert alert-info mt-2">
                        <small><i class="fas fa-info-circle me-1"></i>${data.hash_components.note || 'These fields are MD5 hash output components, not time/clock/node values'}</small>
                    </div>
                    ` : ''}
                </div>
            </div>
        `;
    }

    getVersion4Analysis(data) {
        return `
            <div class="version-analysis-grid">
                <div class="version-analysis-section">
                    <h6 class="text-danger"><i class="fas fa-random me-2"></i>Random Generation</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Randomness Source:</span>
                        <span class="version-value">Cryptographically Secure</span>
                        <span class="version-desc">Uses system's cryptographically secure random number generator</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Unpredictability:</span>
                        <span class="version-value">Maximum</span>
                        <span class="version-desc">Completely random and unpredictable</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Collision Probability:</span>
                        <span class="version-value">Extremely Low</span>
                        <span class="version-desc">Statistically negligible chance of duplicates</span>
                    </div>
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-info"><i class="fas fa-cogs me-2"></i>Technical Details</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Version Bits:</span>
                        <span class="version-value">4 bits (position 48-51)</span>
                        <span class="version-desc">Always set to 0100 for v4</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Variant Bits:</span>
                        <span class="version-value">2 bits (position 64-65)</span>
                        <span class="version-desc">Always set to 10 for RFC 4122</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Use Cases:</span>
                        <span class="version-value">Session IDs, Tokens, Unique Keys</span>
                        <span class="version-desc">Perfect for scenarios requiring maximum uniqueness</span>
                    </div>
                </div>
                
                <div class="version-analysis-section">
                    <h6 class="text-warning"><i class="fas fa-exclamation-triangle me-2"></i>Security Considerations</h6>
                    <div class="version-detail-item">
                        <span class="version-label">Randomness Quality:</span>
                        <span class="version-value">System Dependent</span>
                        <span class="version-desc">Quality depends on system's random number generator</span>
                    </div>
                    <div class="version-detail-item">
                        <span class="version-label">Entropy Source:</span>
                        <span class="version-value">OS Provided</span>
                        <span class="version-desc">Relies on operating system's entropy sources</span>
                    </div>
                </div>
            </div>
        `;
    }

    getGenericAnalysis(data) {
        return `
            <div class="version-analysis-section">
                <h6 class="text-secondary"><i class="fas fa-question-circle me-2"></i>Unknown Version</h6>
                <div class="version-detail-item">
                    <span class="version-label">Version:</span>
                    <span class="version-value">${data.version}</span>
                    <span class="version-desc">This UUID version is not standard or recognized</span>
                </div>
            </div>
        `;
    }

    showLoading(title, message, useTimeout = true, showProgress = false) {
        const titleElement = document.getElementById('loadingTitle');
        const messageElement = document.getElementById('loadingMessage');
        const progressBar = document.getElementById('modalProgressBar');
        const modalElement = document.getElementById('loadingModal');
        
        if (titleElement) titleElement.textContent = title;
        if (messageElement) messageElement.textContent = message;
        
        // Show/hide progress bar based on parameter
        if (progressBar) {
            if (showProgress) {
                progressBar.style.display = 'block';
                progressBar.style.width = '0%';
            } else {
                progressBar.style.display = 'none';
            }
        }
        
        // Primary approach: Manual DOM manipulation
        if (modalElement) {
            try {
                // Show modal manually
                modalElement.classList.add('show');
                modalElement.style.display = 'block';
                modalElement.setAttribute('aria-hidden', 'false');
                
                // Add backdrop
                document.body.classList.add('modal-open');
                const backdrop = document.createElement('div');
                backdrop.className = 'modal-backdrop fade show';
                document.body.appendChild(backdrop);
                
                console.log('Modal shown manually');
                
                // Only set timeout for operations that should have a reasonable time limit
                if (useTimeout) {
                    this.loadingTimeout = setTimeout(() => {
                        console.warn('Loading modal timeout - auto-hiding');
                        this.hideLoading();
                    }, 30000);
                }
            } catch (error) {
                console.error('Error showing modal manually:', error);
                // Fallback: show a simple loading indicator
                this.showSimpleLoading(title);
            }
        } else {
            console.log('Modal element not found, using fallback');
            // Fallback: show a simple loading indicator
            this.showSimpleLoading(title);
        }
    }

    updateProgress(percentage, message = null) {
        const progressBar = document.getElementById('modalProgressBar');
        const messageElement = document.getElementById('loadingMessage');
        
        if (progressBar) {
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
        }
        
        if (message && messageElement) {
            messageElement.textContent = message;
        }
    }

    hideLoading() {
        console.log('hideLoading called');
        
        // Clear the timeout if it exists
        if (this.loadingTimeout) {
            clearTimeout(this.loadingTimeout);
            this.loadingTimeout = null;
        }
        
        // Primary approach: Manual DOM manipulation
        const modalElement = document.getElementById('loadingModal');
        if (modalElement) {
            modalElement.classList.remove('show');
            modalElement.style.display = 'none';
            modalElement.setAttribute('aria-hidden', 'true');
            console.log('Modal element hidden manually');
        }
        
        // Remove backdrop and body classes
        document.body.classList.remove('modal-open');
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => {
            backdrop.remove();
            console.log('Backdrop removed');
        });
        
        // Secondary approach: Try Bootstrap modal hide if available (but don't rely on it)
        if (this.loadingModal) {
            console.log('Bootstrap modal instance exists, attempting to hide...');
            try {
                this.loadingModal.hide();
                console.log('Bootstrap Modal.hide() called successfully');
            } catch (error) {
                console.error('Error with Bootstrap modal.hide():', error);
            }
        } else {
            console.log('No Bootstrap modal instance found');
        }
        
        console.log('hideLoading completed');
    }

    showSimpleLoading(title) {
        // Create a simple loading overlay
        const overlay = document.createElement('div');
        overlay.id = 'simpleLoadingOverlay';
        overlay.style.cssText = `
            position: fixed;
            top: 0;
            left: 0;
            width: 100%;
            height: 100%;
            background: rgba(0, 0, 0, 0.5);
            display: flex;
            justify-content: center;
            align-items: center;
            z-index: 9999;
        `;
        overlay.innerHTML = `
            <div style="background: white; padding: 20px; border-radius: 10px; text-align: center;">
                <div class="spinner-border text-primary mb-3" role="status">
                    <span class="visually-hidden">Loading...</span>
                </div>
                <h5>${title}</h5>
            </div>
        `;
        document.body.appendChild(overlay);
    }

    hideSimpleLoading() {
        const overlay = document.getElementById('simpleLoadingOverlay');
        if (overlay) {
            overlay.remove();
        }
    }

    showError(message) {
        console.log('showError called with message:', message);
        
        // Create a temporary alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-danger alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            <i class="fas fa-exclamation-triangle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        console.log('Error alert created and added to DOM');
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            console.log('Auto-removing error alert after 3 seconds');
            if (alertDiv.parentNode) {
                alertDiv.remove();
                console.log('Error alert removed from DOM');
            } else {
                console.log('Error alert already removed from DOM');
            }
        }, 3000);
    }

    showSuccess(message) {
        console.log('showSuccess called with message:', message);
        
        // Create a temporary success alert
        const alertDiv = document.createElement('div');
        alertDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
        alertDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 300px;';
        alertDiv.innerHTML = `
            <i class="fas fa-check-circle me-2"></i>
            ${message}
            <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
        `;
        
        document.body.appendChild(alertDiv);
        console.log('Success alert created and added to DOM');
        
        // Auto-remove after 3 seconds
        setTimeout(() => {
            console.log('Auto-removing success alert after 3 seconds');
            if (alertDiv.parentNode) {
                alertDiv.remove();
                console.log('Success alert removed from DOM');
            } else {
                console.log('Success alert already removed from DOM');
            }
        }, 3000);
    }

    async downloadFile(taskId) {
        try {
            // Use direct download link for faster streaming (no blob buffering)
            const downloadUrl = `/api/download-file/${taskId}`;
            const a = document.createElement('a');
            a.href = downloadUrl;
            a.download = ''; // Let browser determine filename from Content-Disposition header
            a.style.display = 'none';
            document.body.appendChild(a);
            a.click();
            
            // Clean up the link element after a short delay
            setTimeout(() => {
                document.body.removeChild(a);
            }, 100);
            
            // Show success message immediately (download happens in background)
            // Files are kept on server after download - no cleanup needed
            this.showSuccess('Download started! File will remain on server. You can continue searching UUIDs.');
            
            // Keep the results table visible so user can continue searching
            // Don't hide the search interface after download
        } catch (error) {
            this.showError('Download error: ' + error.message);
        }
    }

    async cleanupTask(taskId) {
        try {
            const response = await fetch(`/api/cleanup-task/${taskId}`, {
                method: 'DELETE'
            });
            
            if (response.ok) {
                this.showSuccess('Task cleaned up successfully');
                // Hide results
                document.getElementById('rangeResults').style.display = 'none';
            } else {
                const error = await response.json();
                this.showError(error.error || 'Cleanup failed');
            }
        } catch (error) {
            this.showError('Cleanup error: ' + error.message);
        }
    }



    async cleanupCurrentTask() {
        if (this.currentTaskId) {
            try {
                await fetch(`/api/cleanup-task/${this.currentTaskId}`, {
                    method: 'DELETE'
                });
            } catch (error) {
                console.error('Error cleaning up current task:', error);
            }
        }
    }

    updateProgressBar(percentage) {
        const progressBar = document.getElementById('progressBar');
        const progressText = document.getElementById('progressText');
        
        if (progressBar && progressText) {
            // Enhanced progress bar with smooth animations and visual feedback
            const currentWidth = parseFloat(progressBar.style.width) || 0;
            
            // Add smooth animation with different speeds based on progress change
            const animationDuration = Math.abs(percentage - currentWidth) > 10 ? '0.5s' : '0.3s';
            progressBar.style.transition = `width ${animationDuration} ease-out`;
            
            // Update progress bar width
            progressBar.style.width = `${percentage}%`;
            progressBar.setAttribute('aria-valuenow', percentage);
            
            // Add visual feedback based on progress
            this.updateProgressBarStyle(percentage);
            
            // Update progress text with enhanced formatting
            const progressDisplay = this.formatProgressDisplay(percentage);
            progressText.innerHTML = progressDisplay;
            
            // Add progress animation class for visual appeal
            if (percentage > 0 && percentage < 100) {
                progressBar.classList.add('progress-animated');
            } else {
                progressBar.classList.remove('progress-animated');
            }
        }
    }

    // Enhanced progress bar styling based on progress percentage
    updateProgressBarStyle(percentage) {
        const progressBar = document.getElementById('progressBar');
        if (!progressBar) return;
        
        // Remove existing color classes
        progressBar.classList.remove('bg-primary', 'bg-info', 'bg-warning', 'bg-success');
        
        // Apply color based on progress
        if (percentage < 25) {
            progressBar.classList.add('bg-info');
        } else if (percentage < 50) {
            progressBar.classList.add('bg-primary');
        } else if (percentage < 75) {
            progressBar.classList.add('bg-warning');
        } else if (percentage < 100) {
            progressBar.classList.add('bg-warning');
        } else {
            progressBar.classList.add('bg-success');
        }
        
        // Add striped effect for active progress
        if (percentage > 0 && percentage < 100) {
            progressBar.classList.add('progress-bar-striped', 'progress-bar-animated');
        } else {
            progressBar.classList.remove('progress-bar-striped', 'progress-bar-animated');
        }
    }

    // Format progress display with enhanced information
    formatProgressDisplay(percentage) {
        const now = new Date();
        const timeString = now.toLocaleTimeString();
        
        let progressClass = 'text-primary';
        let progressIcon = 'fas fa-spinner fa-spin';
        
        if (percentage >= 100) {
            progressClass = 'text-success';
            progressIcon = 'fas fa-check-circle';
        } else if (percentage >= 75) {
            progressClass = 'text-warning';
            progressIcon = 'fas fa-clock';
        } else if (percentage >= 50) {
            progressClass = 'text-info';
            progressIcon = 'fas fa-hourglass-half';
        } else if (percentage >= 25) {
            progressClass = 'text-primary';
            progressIcon = 'fas fa-hourglass-start';
        }
        
        return `
            <div class="d-flex align-items-center justify-content-between">
                <span class="${progressClass}">
                    <i class="${progressIcon} me-2"></i>
                    <strong>Progress: ${percentage.toFixed(1)}%</strong>
                </span>
                <small class="text-muted">
                    <i class="fas fa-clock me-1"></i>
                    Last updated: ${timeString}
                </small>
            </div>
        `;
    }
}

// Global function to manually hide loading modal
function hideLoadingModal() {
    console.log('Global hideLoadingModal called');
    
    if (window.uuidApp) {
        window.uuidApp.hideLoading();
    } else {
        // Direct fallback
        const modal = document.getElementById('loadingModal');
        if (modal) {
            // Force hide the modal
            modal.classList.remove('show');
            modal.style.display = 'none';
            modal.setAttribute('aria-hidden', 'true');
            
            // Try Bootstrap modal if available
            if (typeof bootstrap !== 'undefined') {
                const bootstrapModal = bootstrap.Modal.getInstance(modal);
                if (bootstrapModal) {
                    bootstrapModal.hide();
                }
            }
        }
        
        // Remove backdrop and body classes
        document.body.classList.remove('modal-open');
        const backdrops = document.querySelectorAll('.modal-backdrop');
        backdrops.forEach(backdrop => backdrop.remove());
        
        console.log('Global hideLoadingModal completed');
    }
}

// Copy to clipboard function
function copyToClipboard(text) {
    if (navigator.clipboard) {
        navigator.clipboard.writeText(text).then(() => {
            showCopySuccess();
        }).catch(() => {
            fallbackCopyToClipboard(text);
        });
    } else {
        fallbackCopyToClipboard(text);
    }
}

function fallbackCopyToClipboard(text) {
    const textArea = document.createElement('textarea');
    textArea.value = text;
    textArea.style.position = 'fixed';
    textArea.style.left = '-999999px';
    textArea.style.top = '-999999px';
    document.body.appendChild(textArea);
    textArea.focus();
    textArea.select();
    
    try {
        document.execCommand('copy');
        showCopySuccess();
    } catch (err) {
        console.error('Failed to copy: ', err);
    }
    
    document.body.removeChild(textArea);
}

function showCopySuccess() {
    console.log('showCopySuccess called');
    
    // Create a temporary success message
    const successDiv = document.createElement('div');
    successDiv.className = 'alert alert-success alert-dismissible fade show position-fixed';
    successDiv.style.cssText = 'top: 20px; right: 20px; z-index: 9999; min-width: 200px;';
    successDiv.innerHTML = `
        <i class="fas fa-check-circle me-2"></i>
        Copied to clipboard!
        <button type="button" class="btn-close" data-bs-dismiss="alert"></button>
    `;
    
    document.body.appendChild(successDiv);
    console.log('Copy success alert created and added to DOM');
    
    // Auto-remove after 3 seconds
    setTimeout(() => {
        console.log('Auto-removing copy success alert after 3 seconds');
        if (successDiv.parentNode) {
            successDiv.remove();
            console.log('Copy success alert removed from DOM');
        } else {
            console.log('Copy success alert already removed from DOM');
        }
    }, 3000);
}

// Initialize the application when DOM is loaded
document.addEventListener('DOMContentLoaded', () => {
    // Ensure Bootstrap is loaded before initializing
    if (typeof bootstrap !== 'undefined') {
        window.uuidApp = new UUIDGeneratorApp();
        window.app = window.uuidApp; // Alias for easier access
    } else {
        // Wait for Bootstrap to load
        setTimeout(() => {
            window.uuidApp = new UUIDGeneratorApp();
            window.app = window.uuidApp; // Alias for easier access
        }, 100);
    }
    
    // Add some sample UUIDs for testing
    const sampleUuids = [
        '550e8400-e29b-41d4-a716-446655440000',
        '550e8400-e29b-41d4-a716-446655440001',
        '6ba7b810-9dad-11d1-80b4-00c04fd430c8'
    ];
    
    // Add sample buttons if they don't exist
    if (!document.getElementById('sampleButtons')) {
        const sampleDiv = document.createElement('div');
        sampleDiv.id = 'sampleButtons';
        sampleDiv.className = 'mt-3';
        sampleDiv.innerHTML = `
            <small class="text-muted">Sample UUIDs for testing:</small><br>
            ${sampleUuids.map(uuid => 
                `<button class="btn btn-sm btn-outline-secondary me-2 mb-1" onclick="document.getElementById('analyzeUuid').value='${uuid}'">${uuid.substring(0, 8)}...</button>`
            ).join('')}
        `;
        document.getElementById('analyze').querySelector('.card-body').appendChild(sampleDiv);
    }
}); 