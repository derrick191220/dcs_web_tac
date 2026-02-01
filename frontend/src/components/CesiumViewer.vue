<template>
  <div class="flex h-screen w-full flex-col">
    <!-- Header -->
    <header class="h-16 border-b border-gray-700 flex items-center px-6 justify-between bg-gray-800 shrink-0">
        <div class="flex items-center space-x-3">
            <div class="w-8 h-8 bg-blue-500 rounded-full flex items-center justify-center font-bold">W</div>
            <h1 class="text-xl font-semibold tracking-tight">DCS Web-Tac <span class="text-xs text-gray-400">v0.3.0 (Vue)</span></h1>
        </div>
        <div class="flex space-x-4">
            <input ref="fileInput" type="file" class="hidden" @change="onFileSelected" accept=".acmi,.zip,.gz,.zip.acmi" />
            <button @click="triggerUpload" class="bg-blue-600 hover:bg-blue-500 px-4 py-1.5 rounded text-sm transition font-medium">Upload ACMI</button>
            <div class="h-8 w-px bg-gray-700"></div>
            <span class="text-sm text-gray-300 self-center">
                Pilot: {{ currentObject?.pilot || 'Unknown' }} | {{ currentObject?.name || 'Aircraft' }}
            </span>
        </div>
    </header>

    <main class="flex flex-1 overflow-hidden">
        <!-- Sidebar -->
        <aside class="w-80 border-r border-gray-700 bg-gray-800 flex flex-col">
            <div class="p-4 border-b border-gray-700 space-y-3">
                <h2 class="text-sm font-bold uppercase text-gray-400">Sortie History</h2>
                <div>
                    <label class="text-[10px] uppercase text-gray-500">Aircraft</label>
                    <select
                      class="mt-1 w-full bg-gray-900 border border-gray-700 rounded px-2 py-1 text-sm"
                      v-model="currentObject"
                      @change="onObjectChange"
                    >
                      <option v-for="o in objects" :key="o.obj_id" :value="o">
                        {{ o.name || o.obj_id }} ({{ o.pilot || 'Unknown' }})
                      </option>
                    </select>
                </div>
            </div>
            <div class="flex-1 overflow-y-auto divide-y divide-gray-700">
                <div v-if="loading" class="p-4 text-center text-gray-500 text-sm italic">Loading missions...</div>
                <div v-else-if="sorties.length === 0" class="p-4 text-center text-gray-500 text-sm italic">No data found.</div>
                
                <div 
                  v-for="s in sorties" 
                  :key="s.id"
                  @click="selectSortie(s)"
                  :class="['p-4 cursor-pointer transition border-l-4', currentSortie?.id === s.id ? 'border-blue-500 bg-gray-700' : 'border-transparent hover:bg-gray-700']"
                >
                    <div class="font-bold text-blue-400">{{ s.aircraft_type || 'DCS Unit' }}</div>
                    <div class="text-xs text-gray-300 mt-1">{{ s.mission_name }}</div>
                    <div class="text-[10px] text-gray-500 mt-1">{{ s.start_time }}</div>
                </div>
            </div>
        </aside>

        <!-- Cesium View -->
        <section class="flex-1 relative">
            <div id="cesiumContainer" class="w-full h-full"></div>
            
            <!-- HUD -->
            <div class="absolute top-4 right-4 bg-black bg-opacity-60 p-4 rounded-lg border border-white border-opacity-10 w-64 pointer-events-none select-none z-10">
                <h3 class="text-xs font-bold text-blue-400 mb-2 uppercase">Telemetry Data</h3>
                <div class="grid grid-cols-2 gap-2 text-sm">
                    <span class="text-gray-400">Alt:</span> <span>{{ Math.round(hud.alt) }} m</span>
                    <span class="text-gray-400">Speed:</span> <span>{{ Math.round(hud.ias) }} kts</span>
                    <span class="text-gray-400">G-Force:</span> <span>{{ hud.g.toFixed(1) }}</span>
                </div>
                <div class="grid grid-cols-2 gap-2 text-[10px] border-t border-gray-700 pt-2 mt-2">
                    <span class="text-gray-500">Lat:</span> <span class="text-gray-300">{{ hud.lat.toFixed(4) }}</span>
                    <span class="text-gray-500">Lon:</span> <span class="text-gray-300">{{ hud.lon.toFixed(4) }}</span>
                    <span class="text-gray-500">Pitch:</span> <span class="text-gray-300">{{ Math.round(hud.pitch) }}°</span>
                    <span class="text-gray-500">Roll:</span> <span class="text-gray-300">{{ Math.round(hud.roll) }}°</span>
                    <span class="text-gray-500">Yaw:</span> <span class="text-gray-300">{{ Math.round(hud.yaw) }}°</span>
                </div>
            </div>
        </section>
    </main>
  </div>
</template>

<script setup>
import { onMounted, ref, reactive } from 'vue';
import * as Cesium from 'cesium';

// State
const sorties = ref([]);
const currentSortie = ref(null);
const objects = ref([]);
const currentObject = ref(null);
const loading = ref(true);
const hud = reactive({
    alt: 0, ias: 0, g: 1.0,
    lat: 0, lon: 0, pitch: 0, roll: 0, yaw: 0
});

let viewer = null;
let currentEntity = null;

onMounted(async () => {
    initCesium();
    await loadSorties();
});

function initCesium() {
    Cesium.Ion.defaultAccessToken = ''; // Zero CDN / No Ion
    
    viewer = new Cesium.Viewer('cesiumContainer', {
        animation: true,
        timeline: true,
        infoBox: false,
        selectionIndicator: false,
        navigationHelpButton: false,
        baseLayerPicker: false, // Critical for Zero CDN
        geocoder: false,
        homeButton: true,
        sceneModePicker: true,
        shouldAnimate: true,
        terrainProvider: new Cesium.EllipsoidTerrainProvider(),
        baseLayer: new Cesium.ImageryLayer(new Cesium.UrlTemplateImageryProvider({
            url: 'https://server.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer/tile/{z}/{y}/{x}',
            maximumLevel: 19
        }))
    });
    
    viewer.scene.globe.baseColor = Cesium.Color.BLACK;
    
    // HUD Update Loop
    viewer.clock.onTick.addEventListener(() => {
        if (!currentSortie.value || !currentEntity) return;
        
        // This is a simplified HUD update. 
        // In Vue, we update the reactive 'hud' object, and DOM updates automatically.
        // We need the telemetry data. For simplicity, we'll store active telemetry in a variable.
    });
}

let activeTelemetry = [];
let flightStartTime = null;
const fileInput = ref(null);

async function loadSorties() {
    try {
        const res = await fetch('/api/sorties');
        sorties.value = await res.json();
        
        if (sorties.value.length > 0) {
            await selectSortie(sorties.value[0]);
        }
    } catch (e) {
        console.error("API Error", e);
    } finally {
        loading.value = false;
    }
}

async function loadObjects(sortieId) {
    const res = await fetch(`/api/sorties/${sortieId}/objects`);
    objects.value = await res.json();
    if (objects.value.length > 0) {
        currentObject.value = objects.value[0];
    } else {
        currentObject.value = null;
    }
}

async function selectSortie(sortie) {
    currentSortie.value = sortie;
    try {
        await loadObjects(sortie.id);
        if (currentObject.value) {
            await loadTelemetry(sortie.id, currentObject.value.obj_id);
        }
    } catch (e) {
        console.error("Telemetry fetch failed", e);
    }
}

async function onObjectChange() {
    if (!currentSortie.value || !currentObject.value) return;
    await loadTelemetry(currentSortie.value.id, currentObject.value.obj_id);
}

async function loadTelemetry(sortieId, objId) {
    const res = await fetch(`/api/sorties/${sortieId}/telemetry?obj_id=${objId}`);
    activeTelemetry = await res.json();

    let rawStart = currentSortie.value.start_time;
    if (!rawStart.includes('Z')) rawStart += 'Z';
    flightStartTime = Cesium.JulianDate.fromIso8601(rawStart);

    visualizeFlight(activeTelemetry, flightStartTime);
}

function triggerUpload() {
    if (fileInput.value) fileInput.value.click();
}

async function onFileSelected(e) {
    const file = e.target.files && e.target.files[0];
    if (!file) return;
    const formData = new FormData();
    formData.append('file', file);

    try {
        await fetch('/api/upload', { method: 'POST', body: formData });
        // refresh sorties list after upload
        await loadSorties();
    } catch (err) {
        console.error('Upload failed', err);
    } finally {
        if (fileInput.value) fileInput.value.value = '';
    }
}

function visualizeFlight(telemetry, start) {
    if (currentEntity) viewer.entities.remove(currentEntity);
    
    const positions = new Cesium.SampledPositionProperty();
    const orientations = new Cesium.SampledProperty(Cesium.Quaternion);
    
    telemetry.forEach(point => {
        const time = Cesium.JulianDate.addSeconds(start, point.time_offset, new Cesium.JulianDate());
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        positions.addSample(time, position);
        
        // ACMI angles are in degrees (yaw=heading). Convert directly to Cesium HPR
        const headingOffset = Cesium.Math.toRadians(180); // model forward axis fix
        const yawDeg = point.yaw || 0;
        const pitchDeg = point.pitch || 0;
        const rollDeg = point.roll || 0;

        const heading = Cesium.Math.toRadians(yawDeg) + headingOffset;
        const pitch = Cesium.Math.toRadians(pitchDeg);
        const roll = Cesium.Math.toRadians(rollDeg);

        const hpr = new Cesium.HeadingPitchRoll(heading, pitch, roll);
        const orientation = Cesium.Transforms.headingPitchRollQuaternion(position, hpr);
        orientations.addSample(time, orientation);
    });
    
    currentEntity = viewer.entities.add({
        position: positions,
        orientation: orientations,
        model: {
            uri: '/models/f16.glb', // Absolute path
            minimumPixelSize: 128,
            maximumScale: 20000
        },
        path: {
            show: true,
            leadTime: 0,
            trailTime: Number.POSITIVE_INFINITY,
            material: Cesium.Color.YELLOW,
            width: 3,
            resolution: 1
        }
    });
    
    // Timeline setup
    const stop = Cesium.JulianDate.addSeconds(start, telemetry[telemetry.length-1].time_offset, new Cesium.JulianDate());
    viewer.clock.startTime = start.clone();
    viewer.clock.stopTime = stop.clone();
    viewer.clock.currentTime = start.clone();
    viewer.clock.clockRange = Cesium.ClockRange.LOOP_STOP;
    viewer.timeline.zoomTo(start, stop);
    viewer.zoomTo(currentEntity);
    
    // Bind HUD updater
    viewer.clock.onTick.addEventListener(updateHud);
}

function updateHud() {
    if (!activeTelemetry.length) return;
    
    const time = viewer.clock.currentTime;
    const offset = Cesium.JulianDate.secondsDifference(time, flightStartTime);
    
    // Simple nearest neighbor search
    // Optimization: activeTelemetry is sorted by time_offset. 
    // binary search would be better but find is ok for small datasets.
    const nearest = activeTelemetry.reduce((prev, curr) => 
        Math.abs(curr.time_offset - offset) < Math.abs(prev.time_offset - offset) ? curr : prev
    );

    if (nearest) {
        // Skip bogus zero points
        if (nearest.lat === 0 && nearest.lon === 0 && nearest.alt === 0) return;
        hud.alt = nearest.alt;
        hud.ias = nearest.ias;
        hud.g = nearest.g_force;
        hud.lat = nearest.lat;
        hud.lon = nearest.lon;
        hud.pitch = nearest.pitch;
        hud.roll = nearest.roll;
        hud.yaw = nearest.yaw;
    }
}
</script>

<style>
/* Leaflet/Cesium specific overrides if needed */
</style>
