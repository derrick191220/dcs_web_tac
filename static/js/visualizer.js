// Initialize Cesium Viewer - Use a more robust setup
// Note: World terrain and high-res imagery often require a Cesium Ion token.
// For now, we use default tiles to ensure visibility.

const viewer = new Cesium.Viewer('cesiumContainer', {
    terrainProvider: Cesium.createWorldTerrain(),
    animation: true,
    timeline: true,
    infoBox: false,
    selectionIndicator: false,
    navigationHelpButton: false,
    baseLayerPicker: true, // Allow user to switch imagery if one fails
    geocoder: false,
    homeButton: true,
    sceneModePicker: true,
    shouldAnimate: true
});

// HUD Elements
const hudAlt = document.getElementById('hud-alt');
const hudSpeed = document.getElementById('hud-speed');
const hudG = document.getElementById('hud-g');

// State
let currentEntity = null;
let flightStartTime = null;

async function loadSorties() {
    try {
        console.log("Fetching sorties...");
        const response = await fetch('/api/sorties');
        const sorties = await response.json();
        console.log("Sorties loaded:", sorties);
        
        const listContainer = document.getElementById('sortieList');
        listContainer.innerHTML = '';

        if (sorties.length === 0) {
            listContainer.innerHTML = '<div class="p-4 text-center text-slate-500 text-sm italic">No sorties found in database.</div>';
            return;
        }

        sorties.forEach(s => {
            const item = document.createElement('div');
            item.className = 'p-4 sortie-item transition border-l-4 border-transparent';
            item.innerHTML = `
                <div class="font-bold text-blue-400">${s.aircraft_type || 'Unknown AC'}</div>
                <div class="text-xs text-slate-300 mt-1">${s.mission_name}</div>
                <div class="text-[10px] text-slate-500 mt-1">${new Date(s.start_time).toLocaleString()}</div>
            `;
            item.onclick = () => selectSortie(s, item);
            listContainer.appendChild(item);
        });
    } catch (err) {
        console.error("Failed to load sorties:", err);
        document.getElementById('sortieList').innerHTML = '<div class="p-4 text-red-400 text-sm">Error connecting to API.</div>';
    }
}

async function selectSortie(sortie, element) {
    document.querySelectorAll('.sortie-item').forEach(el => el.classList.remove('active'));
    element.classList.add('active');

    try {
        console.log(`Loading telemetry for sortie ${sortie.id}...`);
        const response = await fetch(`/api/sorties/${sortie.id}/telemetry`);
        const data = await response.json();
        console.log(`Loaded ${data.length} data points.`);
        
        // Use the actual start time from the sortie
        flightStartTime = Cesium.JulianDate.fromIso8601(sortie.start_time.replace(' ', 'T') + 'Z');
        visualizeFlight(data);
    } catch (err) {
        console.error("Telemetry error:", err);
        alert("Failed to load telemetry for this mission.");
    }
}

function visualizeFlight(telemetry) {
    if (currentEntity) viewer.entities.remove(currentEntity);

    const positions = new Cesium.SampledPositionProperty();
    
    telemetry.forEach(point => {
        const time = Cesium.JulianDate.addSeconds(
            flightStartTime, 
            point.time_offset, 
            new Cesium.JulianDate()
        );
        // Ensure coords are valid
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        positions.addSample(time, position);
    });

    // Create the aircraft entity
    currentEntity = viewer.entities.add({
        position: positions,
        orientation: new Cesium.VelocityOrientationProperty(positions), // Auto-calculate orientation based on movement
        path: {
            resolution: 1,
            material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.2,
                color: Cesium.Color.GOLD
            }),
            width: 5,
            leadTime: 0,
            trailTime: 1000
        },
        // Use a built-in Cesium model if external GLB fails
        point: {
            pixelSize: 10,
            color: Cesium.Color.WHITE,
            outlineColor: Cesium.Color.BLUE,
            outlineWidth: 2
        },
        label: {
            text: 'F-16C',
            font: '12pt monospace',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            outlineWidth: 2,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -20)
        }
    });

    // Set timeline to flight duration
    const start = flightStartTime;
    const stop = Cesium.JulianDate.addSeconds(start, telemetry[telemetry.length-1].time_offset, new Cesium.JulianDate());
    
    viewer.clock.startTime = start.clone();
    viewer.clock.stopTime = stop.clone();
    viewer.clock.currentTime = start.clone();
    viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
    viewer.timeline.zoomTo(start, stop);

    viewer.trackedEntity = currentEntity;
    
    // HUD Update
    viewer.clock.onTick.addEventListener(() => {
        const time = viewer.clock.currentTime;
        const pos = positions.getValue(time);
        if (pos) {
            const offset = Cesium.JulianDate.secondsDifference(time, flightStartTime);
            const nearest = telemetry.reduce((prev, curr) => 
                Math.abs(curr.time_offset - offset) < Math.abs(prev.time_offset - offset) ? curr : prev
            );
            
            hudAlt.innerText = `${Math.round(nearest.alt)} m`;
            hudSpeed.innerText = `${Math.round(nearest.ias)} kts`;
            hudG.innerText = nearest.g_force.toFixed(1);
        }
    });
}

loadSorties();
