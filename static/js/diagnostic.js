/**
 * Frontend Error Diagnostic Tool
 * Captures logs and provides a UI for self-repair suggestions.
 */
(function() {
    const originalConsoleError = console.error;
    const errorLogs = [];

    console.error = function(...args) {
        errorLogs.push({
            time: new Date().toISOString(),
            message: args.join(' '),
            stack: new Error().stack
        });
        originalConsoleError.apply(console, args);
        updateDiagnosticUI();
    };

    function updateDiagnosticUI() {
        let diagDiv = document.getElementById('debug-console');
        if (!diagDiv) {
            diagDiv = document.createElement('div');
            diagDiv.id = 'debug-console';
            diagDiv.className = 'fixed bottom-0 left-0 right-0 bg-black text-xs p-2 max-h-32 overflow-y-auto border-t border-red-500 z-50 font-mono hidden';
            document.body.appendChild(diagDiv);
            
            // Toggle button
            const btn = document.createElement('button');
            btn.innerText = '⚠️ Diag';
            btn.className = 'fixed bottom-4 left-4 bg-red-600 text-[10px] p-1 rounded z-[60] opacity-50 hover:opacity-100';
            btn.onclick = () => diagDiv.classList.toggle('hidden');
            document.body.appendChild(btn);
        }

        diagDiv.innerHTML = errorLogs.map(log => 
            `<div class="mb-1 text-red-400">[${log.time}] ${log.message}</div>`
        ).join('');
    }

    // Auto-fix suggestions for common issues
    window.addEventListener('error', function(event) {
        console.error("Window Error:", event.message, "at", event.filename, ":", event.lineno);
    });

    console.log("Diagnostic v0.1: Monitoring frontend health...");
})();

// Self-Repair Logic
window.repairFrontend = function() {
    console.log("Repair initiated: Clearing caches and resetting viewer...");
    if (typeof viewer !== 'undefined' && viewer) {
        viewer.entities.removeAll();
        console.log("Entities cleared.");
    }
    // Check if Cesium is loaded
    if (typeof Cesium === 'undefined') {
        console.error("Critical: Cesium library missing. Suggestion: Check network or script tag.");
    } else {
        console.log("Cesium core found.");
    }
    // Trigger reload of data
    if (typeof loadSorties === 'function') {
        loadSorties();
    }
};
