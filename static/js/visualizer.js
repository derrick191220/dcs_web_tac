// Initialize Cesium Viewer
const viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: Cesium.createWorldTerrain(),
    animation: true,
    timeline: true,
    infoBox: false,
    selectionIndicator: false,
    navigationHelpButton: false,
    baseLayerPicker: false,
    geocoder: false,
    homeButton: false,
    sceneModePicker: true
});

// HUD Elements
const hudAlt = document.getElementById('hud-alt');
const hudSpeed = document.getElementById('hud-speed');
const hudG = document.getElementById('hud-g');

// State
let currentEntity = null;

async function loadSorties() {
    try {
        const response = await fetch('/api/sorties');
        const sorties = await response.json();
        const listContainer = document.getElementById('sortieList');
        listContainer.innerHTML = '';

        sorties.forEach(s => {
            const item = document.createElement('div');
            item.className = 'p-4 sortie-item transition border-l-4 border-transparent';
            item.innerHTML = `
                <div class="font-bold text-blue-400">${s.aircraft_type}</div>
                <div class="text-xs text-slate-300 mt-1">${s.mission_name}</div>
                <div class="text-[10px] text-slate-500 mt-1">${new Date(s.start_time).toLocaleString()}</div>
            `;
            item.onclick = () => selectSortie(s.id, item);
            listContainer.appendChild(item);
        });
    } catch (err) {
        console.error("Failed to load sorties:", err);
    }
}

async function selectSortie(id, element) {
    // UI feedback
    document.querySelectorAll('.sortie-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    try {
        const response = await fetch(`/api/sorties/${id}/telemetry`);
        const data = await response.json();
        
        visualizeFlight(data);
    } catch (err) {
        alert("Failed to load telemetry for this mission.");
    }
}

function visualizeFlight(telemetry) {
    if (currentEntity) viewer.entities.remove(currentEntity);

    const positions = new Cesium.SampledPositionProperty();
    
    telemetry.forEach(point => {
        const time = Cesium.JulianDate.addSeconds(
            Cesium.JulianDate.fromIso8601("2026-02-01T10:00:00Z"), 
            point.time_offset, 
            new Cesium.JulianDate()
        );
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        positions.addSample(time, position);
    });

    currentEntity = viewer.entities.add({
        position: positions,
        path: {
            resolution: 1,
            material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.1,
                color: Cesium.Color.YELLOW
            }),
            width: 10
        },
        model: {
            uri: 'https://assets.agi.com/models/f-16.glb', // Placeholder F-16 model
            minimumPixelSize: 64
        }
    });

    viewer.trackedEntity = currentEntity;
    
    // Update HUD during playback
    viewer.clock.onTick.addEventListener(() => {
        const time = viewer.clock.currentTime;
        const pos = positions.getValue(time);
        if (pos) {
            // Finding the nearest data point for HUD (optimized approach needed later)
            const offset = Cesium.JulianDate.secondsDifference(time, Cesium.JulianDate.fromIso8601("2026-02-01T10:00:00Z"));
            const nearest = telemetry.reduce((prev, curr) => 
                Math.abs(curr.time_offset - offset) < Math.abs(prev.time_offset - offset) ? curr : prev
            );
            
            hudAlt.innerText = `${Math.round(nearest.alt)} m`;
            hudSpeed.innerText = `${Math.round(nearest.ias)} kts`;
            hudG.innerText = nearest.g_force.toFixed(1);
        }
    });
}

// Initial load
loadSorties();
