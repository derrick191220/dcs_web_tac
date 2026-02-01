// Initialize Cesium Viewer - Professional & Robust Configuration
console.log("Visualizer.js v0.2.4: Initializing flight visualizer...");

let viewer;

// Initialize the Cesium viewer with a more compatible setup
try {
    viewer = new Cesium.Viewer('cesiumContainer', {
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
        useDefaultRenderLoop: true,
        showRenderLoopErrors: true,
        terrainProvider: new Cesium.EllipsoidTerrainProvider(),
        // Use OpenStreetMap as default - High Visibility & No Token Needed
        baseLayer: new Cesium.ImageryLayer(new Cesium.OpenStreetMapImageryProvider({
            url : 'https://a.tile.openstreetmap.org/'
        }))
    });
    Cesium.Ion.defaultAccessToken = ''; 
    viewer.scene.globe.baseColor = Cesium.Color.BLACK; 
    console.log("Cesium Viewer initialized with OSM imagery.");
} catch (error) {
    console.error("Failed to initialize Cesium Viewer:", error);
    document.getElementById('cesiumContainer').innerHTML = `<div class="p-10 text-red-500">3D Engine Error: ${error.message}</div>`;
}

// HUD Elements
const hudAlt = document.getElementById('hud-alt');
const hudSpeed = document.getElementById('hud-speed');
const hudG = document.getElementById('hud-g');

// State
let currentEntity = null;

async function loadSorties() {
    try {
        console.log("Fetching sorties from API...");
        const response = await fetch('/api/sorties');
        if (!response.ok) throw new Error(`HTTP error! status: ${response.status}`);
        
        const sorties = await response.json();
        console.log("Sorties loaded:", sorties);
        
        const listContainer = document.getElementById('sortieList');
        listContainer.innerHTML = '';

        if (!sorties || sorties.length === 0) {
            listContainer.innerHTML = '<div class="p-4 text-center text-gray-500 text-sm italic">No data found.</div>';
            return;
        }

        sorties.forEach(s => {
            const item = document.createElement('div');
            item.className = 'p-4 sortie-item transition border-l-4 border-transparent';
            item.innerHTML = `
                <div class="font-bold text-blue-400">${s.aircraft_type || 'DCS Unit'}</div>
                <div class="text-xs text-gray-300 mt-1">${s.mission_name}</div>
                <div class="text-[10px] text-gray-500 mt-1">${s.start_time}</div>
            `;
            item.onclick = () => selectSortie(s, item);
            listContainer.appendChild(item);
        });
        
        // Auto-select first sortie
        if (sorties.length > 0) {
            selectSortie(sorties[0], listContainer.firstChild);
        }
    } catch (err) {
        console.error("Sortie List Error:", err);
        document.getElementById('sortieList').innerHTML = `<div class="p-4 text-red-400 text-sm">Connection Error</div>`;
    }
}

async function selectSortie(sortie, element) {
    document.querySelectorAll('.sortie-item').forEach(el => el.classList.remove('active'));
    if (element) element.classList.add('active');

    try {
        console.log(`Fetching Telemetry for ID ${sortie.id}...`);
        const response = await fetch(`/api/sorties/${sortie.id}/telemetry`);
        const data = await response.json();
        
        // Date parsing: Render/Python often omits the 'Z'
        let rawStart = sortie.start_time;
        if (!rawStart.includes('Z')) rawStart += 'Z';
        const flightStartTime = Cesium.JulianDate.fromIso8601(rawStart);
        
        visualizeFlight(data, flightStartTime);
    } catch (err) {
        console.error("Telemetry Error:", err);
    }
}

function visualizeFlight(telemetry, flightStartTime) {
    if (currentEntity) viewer.entities.remove(currentEntity);

    const positions = new Cesium.SampledPositionProperty();
    const orientations = new Cesium.SampledProperty(Cesium.Quaternion);
    
    telemetry.forEach(point => {
        const time = Cesium.JulianDate.addSeconds(
            flightStartTime, 
            point.time_offset, 
            new Cesium.JulianDate()
        );
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        positions.addSample(time, position);

        // Calculate orientation from Pitch, Roll, Yaw
        // Note: DCS use specific Euler order, but standard heading/pitch/roll usually works for visual
        const hpr = new Cesium.HeadingPitchRoll(
            Cesium.Math.toRadians(point.yaw || 0),
            Cesium.Math.toRadians(point.pitch || 0),
            Cesium.Math.toRadians(point.roll || 0)
        );
        const orientation = Cesium.Transforms.headingPitchRollQuaternion(position, hpr);
        orientations.addSample(time, orientation);
    });

    currentEntity = viewer.entities.add({
        position: positions,
        orientation: orientations, // Use the real orientations from telemetry
        model: {
            uri: 'https://assets.agi.com/models/F-16.glb', // Professional F-16 model
            minimumPixelSize: 128,
            maximumScale: 20000
        },
        path: {
            resolution: 1,
            material: new Cesium.PolylineGlowMaterialProperty({
                glowPower: 0.25,
                color: Cesium.Color.GOLD
            }),
            width: 8,
            leadTime: 0,
            trailTime: 100000 // Show much longer trail
        },
        label: {
            text: 'PILOT: DERRICK',
            font: 'bold 12pt sans-serif',
            style: Cesium.LabelStyle.FILL_AND_OUTLINE,
            outlineWidth: 2,
            verticalOrigin: Cesium.VerticalOrigin.BOTTOM,
            pixelOffset: new Cesium.Cartesian2(0, -50)
        }
    });

    // Ensure ground clamping or relative height
    viewer.scene.globe.depthTestAgainstTerrain = true;


    const start = flightStartTime;
    const stop = Cesium.JulianDate.addSeconds(start, telemetry[telemetry.length-1].time_offset, new Cesium.JulianDate());
    
    viewer.clock.startTime = start.clone();
    viewer.clock.stopTime = stop.clone();
    viewer.clock.currentTime = start.clone();
    viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
    viewer.timeline.zoomTo(start, stop);

    viewer.zoomTo(currentEntity);
    
    // HUD Update
    viewer.clock.onTick.addEventListener(() => {
        const time = viewer.clock.currentTime;
        const offset = Cesium.JulianDate.secondsDifference(time, flightStartTime);
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

// Initial API Load
if (viewer) {
    loadSorties();
}
