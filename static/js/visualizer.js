// Initialize Cesium Viewer - Most Stable Configuration
console.log("Visualizer.js version 0.2.3 loading...");

// Use Default Cesium Terrain and OpenStreetMap if default fails
const viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: Cesium.createWorldTerrain(),
    animation: true,
    timeline: true,
    infoBox: false,
    selectionIndicator: false,
    navigationHelpButton: false,
    baseLayerPicker: true, 
    geocoder: false,
    homeButton: true,
    sceneModePicker: true,
    shouldAnimate: true,
    // Add these to debug loading
    requestRenderMode: false,
    maximumRenderTimeChange: Infinity
});

// HUD Elements
const hudAlt = document.getElementById('hud-alt');
const hudSpeed = document.getElementById('hud-speed');
const hudG = document.getElementById('hud-g');

// State
let currentEntity = null;

async function loadSorties() {
    try {
        console.log("API Request: /api/sorties");
        const response = await fetch('/api/sorties');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const sorties = await response.json();
        console.log("Sorties received:", sorties);
        
        const listContainer = document.getElementById('sortieList');
        listContainer.innerHTML = '';

        if (!sorties || sorties.length === 0) {
            listContainer.innerHTML = '<div class="p-4 text-center text-slate-500 text-sm italic">No data. Click "Upload ACMI" to begin.</div>';
            return;
        }

        sorties.forEach(s => {
            const item = document.createElement('div');
            item.className = 'p-4 sortie-item transition border-l-4 border-transparent';
            item.innerHTML = `
                <div class="font-bold text-blue-400">${s.aircraft_type || 'Unknown Unit'}</div>
                <div class="text-xs text-slate-300 mt-1">${s.mission_name}</div>
                <div class="text-[10px] text-slate-500 mt-1">${s.start_time}</div>
            `;
            item.onclick = () => selectSortie(s, item);
            listContainer.appendChild(item);
        });
        
        // Auto-select first sortie if available
        if (sorties.length > 0) {
            console.log("Auto-selecting first mission...");
            selectSortie(sorties[0], listContainer.firstChild);
        }
    } catch (err) {
        console.error("Sortie List Error:", err);
        document.getElementById('sortieList').innerHTML = `<div class="p-4 text-red-400 text-sm">Connection Error: ${err.message}</div>`;
    }
}

async function selectSortie(sortie, element) {
    document.querySelectorAll('.sortie-item').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');

    try {
        console.log(`Fetching Telemetry: /api/sorties/${sortie.id}/telemetry`);
        const response = await fetch(`/api/sorties/${sortie.id}/telemetry`);
        const data = await response.json();
        console.log(`Points received: ${data.length}`);
        
        // Robust Date Handling
        let rawStart = sortie.start_time;
        if (!rawStart.includes('Z') && !rawStart.includes('+')) rawStart += 'Z';
        const flightStartTime = Cesium.JulianDate.fromIso8601(rawStart);
        
        visualizeFlight(data, flightStartTime);
    } catch (err) {
        console.error("Telemetry Visualization Error:", err);
    }
}

function visualizeFlight(telemetry, flightStartTime) {
    if (currentEntity) viewer.entities.remove(currentEntity);

    const positions = new Cesium.SampledPositionProperty();
    
    telemetry.forEach(point => {
        const time = Cesium.JulianDate.addSeconds(
            flightStartTime, 
            point.time_offset, 
            new Cesium.JulianDate()
        );
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        positions.addSample(time, position);
    });

    // Use a simpler entity for maximum compatibility
    currentEntity = viewer.entities.add({
        position: positions,
        orientation: new Cesium.VelocityOrientationProperty(positions),
        path: {
            resolution: 1,
            material: new Cesium.ColorMaterialProperty(Cesium.Color.GOLD.withAlpha(0.8)),
            width: 4,
            trailTime: 1000,
            leadTime: 0
        },
        // Point is much more reliable than external GLB models
        point: {
            pixelSize: 12,
            color: Cesium.Color.RED,
            outlineColor: Cesium.Color.WHITE,
            outlineWidth: 2
        },
        label: {
            text: 'F-16C ACTIVE',
            font: '14pt sans-serif',
            fillColor: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLACK,
            outlineWidth: 2,
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -15)
        }
    });

    // Timeline Sync
    const start = flightStartTime;
    const stop = Cesium.JulianDate.addSeconds(start, telemetry[telemetry.length-1].time_offset, new Cesium.JulianDate());
    
    viewer.clock.startTime = start.clone();
    viewer.clock.stopTime = stop.clone();
    viewer.clock.currentTime = start.clone();
    viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
    viewer.clock.multiplier = 1;
    viewer.timeline.zoomTo(start, stop);

    // Zoom to data
    viewer.zoomTo(currentEntity, new Cesium.HeadingPitchRange(Cesium.Math.toRadians(-90), Cesium.Math.toRadians(-30), 5000));
    
    // HUD Listener
    viewer.clock.onTick.addEventListener(() => {
        const time = viewer.clock.currentTime;
        const offset = Cesium.JulianDate.secondsDifference(time, flightStartTime);
        
        // Efficient HUD searching
        const nearest = telemetry.reduce((prev, curr) => 
            Math.abs(curr.time_offset - offset) < Math.abs(prev.time_offset - offset) ? curr : prev
        );
        
        if (nearest) {
            hudAlt.innerText = `${Math.round(nearest.alt)} m`;
            hudSpeed.innerText = `${Math.round(nearest.ias)} kts`;
            hudG.innerText = nearest.g_force.toFixed(1);
        }
    });
}

// Kickoff
loadSorties();
