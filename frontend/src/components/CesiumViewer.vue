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
            <span class="text-xs text-gray-300 self-center" v-if="uploadJob.status">
                Upload: {{ uploadJob.status }} {{ uploadJob.progress ? `(${uploadJob.progress}%)` : '' }}
            </span>
            <span class="text-sm text-gray-300 self-center" v-else>
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
            <div class="p-4 border-t border-gray-700 space-y-2">
                <h3 class="text-xs uppercase text-gray-400">Attitude Calibration</h3>
                <div class="grid grid-cols-3 gap-2">
                    <label class="text-[10px] text-gray-500">Yaw Offset</label>
                    <input v-model.number="attitudeConfig.yawOffset" type="number" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs" />
                    <label class="text-[10px] text-gray-500">Pitch Sign</label>
                    <select v-model.number="attitudeConfig.pitchSign" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs">
                        <option :value="1">+1</option>
                        <option :value="-1">-1</option>
                    </select>
                    <label class="text-[10px] text-gray-500">Roll Sign</label>
                    <select v-model.number="attitudeConfig.rollSign" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs">
                        <option :value="1">+1</option>
                        <option :value="-1">-1</option>
                    </select>
                </div>
                <div class="grid grid-cols-3 gap-2">
                    <label class="text-[10px] text-gray-500">Start (s)</label>
                    <input v-model.number="telemetryQuery.start" type="number" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs" />
                    <label class="text-[10px] text-gray-500">End (s)</label>
                    <input v-model.number="telemetryQuery.end" type="number" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs" />
                    <label class="text-[10px] text-gray-500">Step (s)</label>
                    <input v-model.number="telemetryQuery.downsample" type="number" :disabled="telemetryQuery.auto" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs" />
                    <label class="text-[10px] text-gray-500">Auto</label>
                    <input type="checkbox" v-model="telemetryQuery.auto" class="col-span-2" />
                    <label class="text-[10px] text-gray-500">Target Pts</label>
                    <input v-model.number="telemetryQuery.targetPoints" type="number" class="col-span-2 bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs" />
                    <div></div>
                    <button @click="applyTelemetryQuery" class="col-span-2 bg-gray-700 hover:bg-gray-600 rounded px-2 py-1 text-xs">Apply</button>
                </div>
                <div class="text-[10px] text-gray-500" v-if="attitudeChecks.alerts.length">
                    <div v-for="(a,i) in attitudeChecks.alerts.slice(-3)" :key="i">⚠️ {{ a }}</div>
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
const uploadJob = reactive({ status: null, progress: 0, error: null });
const telemetryQuery = reactive({ start: null, end: null, downsample: 1, auto: true, targetPoints: 8000 });
const hud = reactive({
    alt: 0, ias: 0, g: 1.0,
    lat: 0, lon: 0, pitch: 0, roll: 0, yaw: 0
});

const attitudeConfig = reactive({
    yawOffset: 180,
    pitchSign: 1,
    rollSign: 1
});
const attitudeChecks = reactive({
    enabled: true,
    maxYawDelta: 45,
    maxPitchDelta: 30,
    maxRollDelta: 60,
    last: null,
    alerts: []
});

let viewer = null;
let currentEntity = null;
let axesPrimitive = null;

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

    // Debug axes for attitude verification
    viewer.entities.add({
        position: Cesium.Cartesian3.fromDegrees(0, 0, 0),
        point: { pixelSize: 6, color: Cesium.Color.WHITE }
    });
    
    // HUD Update Loop + Attitude Axes
    viewer.clock.onTick.addEventListener(() => {
        if (!currentSortie.value || !currentEntity) return;

        if (axesPrimitive) {
            viewer.scene.primitives.remove(axesPrimitive);
            axesPrimitive = null;
        }
        const time = viewer.clock.currentTime;
        const modelMatrix = currentEntity.computeModelMatrix(time, new Cesium.Matrix4());
        axesPrimitive = new Cesium.DebugModelMatrixPrimitive({
            modelMatrix,
            length: 500
        });
        viewer.scene.primitives.add(axesPrimitive);
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
    const params = new URLSearchParams();
    params.set('obj_id', objId);
    if (telemetryQuery.start !== null && telemetryQuery.start !== undefined) params.set('start', telemetryQuery.start);
    if (telemetryQuery.end !== null && telemetryQuery.end !== undefined) params.set('end', telemetryQuery.end);

    // Auto downsample: estimate step to keep target points
    if (telemetryQuery.auto) {
        const start = telemetryQuery.start ?? 0;
        const end = telemetryQuery.end ?? 0;
        const duration = Math.max(1, end - start);
        const step = Math.max(1, duration / telemetryQuery.targetPoints);
        telemetryQuery.downsample = Math.round(step);
    }
    if (telemetryQuery.downsample) params.set('downsample', telemetryQuery.downsample);

    const res = await fetch(`/api/sorties/${sortieId}/telemetry?${params.toString()}`);
    activeTelemetry = await res.json();

    let rawStart = currentSortie.value.start_time;
    if (!rawStart.includes('Z')) rawStart += 'Z';
    flightStartTime = Cesium.JulianDate.fromIso8601(rawStart);

    visualizeFlight(activeTelemetry, flightStartTime);
}

async function applyTelemetryQuery() {
    if (!currentSortie.value || !currentObject.value) return;
    await loadTelemetry(currentSortie.value.id, currentObject.value.obj_id);
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
        const res = await fetch('/api/upload', { method: 'POST', body: formData });
        const data = await res.json();
        if (data.job_id) {
            pollJob(data.job_id);
        }
    } catch (err) {
        console.error('Upload failed', err);
        uploadJob.status = 'failed';
        uploadJob.error = String(err);
    } finally {
        if (fileInput.value) fileInput.value.value = '';
    }
}

async function pollJob(jobId) {
    uploadJob.status = 'queued';
    uploadJob.progress = 0;
    uploadJob.error = null;

    const timer = setInterval(async () => {
        try {
            const res = await fetch(`/api/jobs/${jobId}`);
            const job = await res.json();
            uploadJob.status = job.status;
            uploadJob.progress = Math.round(job.progress_pct || 0);
            uploadJob.error = job.error;

            if (job.status === 'done' || job.status === 'failed') {
                clearInterval(timer);
                await loadSorties();
            }
        } catch (e) {
            clearInterval(timer);
        }
    }, 1500);
}

function visualizeFlight(telemetry, start) {
    if (currentEntity) viewer.entities.remove(currentEntity);
    
    const positions = new Cesium.SampledPositionProperty();
    const orientations = new Cesium.SampledProperty(Cesium.Quaternion);

    // reset attitude checks
    attitudeChecks.last = null;
    attitudeChecks.alerts = [];
    
    telemetry.forEach(point => {
        const time = Cesium.JulianDate.addSeconds(start, point.time_offset, new Cesium.JulianDate());
        const position = Cesium.Cartesian3.fromDegrees(point.lon, point.lat, point.alt);
        positions.addSample(time, position);
        
        // ACMI angles are in degrees (yaw=heading). Convert directly to Cesium HPR
        const headingOffset = Cesium.Math.toRadians(attitudeConfig.yawOffset);
        const yawDeg = point.yaw || 0;
        const pitchDeg = (point.pitch || 0) * attitudeConfig.pitchSign;
        const rollDeg = (point.roll || 0) * attitudeConfig.rollSign;

        const heading = Cesium.Math.toRadians(yawDeg) + headingOffset;
        const pitch = Cesium.Math.toRadians(pitchDeg);
        const roll = Cesium.Math.toRadians(rollDeg);

        const hpr = new Cesium.HeadingPitchRoll(heading, pitch, roll);
        const orientation = Cesium.Transforms.headingPitchRollQuaternion(position, hpr);
        orientations.addSample(time, orientation);

        if (attitudeChecks.enabled) {
            const last = attitudeChecks.last;
            if (last) {
                const dy = Math.abs(yawDeg - last.yaw);
                const dp = Math.abs(pitchDeg - last.pitch);
                const dr = Math.abs(rollDeg - last.roll);
                if (dy > attitudeChecks.maxYawDelta || dp > attitudeChecks.maxPitchDelta || dr > attitudeChecks.maxRollDelta) {
                    attitudeChecks.alerts.push(`Δ yaw ${dy.toFixed(1)} pitch ${dp.toFixed(1)} roll ${dr.toFixed(1)}`);
                }
            }
            attitudeChecks.last = { yaw: yawDeg, pitch: pitchDeg, roll: rollDeg };
        }
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
            width: 2,
            resolution: 1
        }
    });

    // Attitude reference axes handled by DebugModelMatrixPrimitive
    
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
    // pick nearest valid point (non-zero position)
    let nearest = null;
    let minDiff = Infinity;
    for (const p of activeTelemetry) {
        const diff = Math.abs(p.time_offset - offset);
        if (diff < minDiff && !(p.lat === 0 && p.lon === 0 && p.alt === 0)) {
            minDiff = diff;
            nearest = p;
        }
    }

    if (nearest) {
        hud.alt = nearest.alt;
        hud.ias = nearest.ias;
        hud.g = nearest.g_force;
        hud.lat = nearest.lat;
        hud.lon = nearest.lon;
        hud.pitch = nearest.pitch;
        hud.roll = nearest.roll;
        hud.yaw = nearest.yaw;

        // Fallback IAS estimation when missing (use ground speed)
        if (!hud.ias || hud.ias === 0) {
            const idx = activeTelemetry.findIndex(p => p === nearest);
            if (idx > 0) {
                const prev = activeTelemetry[idx - 1];
                const p1 = Cesium.Cartesian3.fromDegrees(prev.lon, prev.lat, prev.alt);
                const p2 = Cesium.Cartesian3.fromDegrees(nearest.lon, nearest.lat, nearest.alt);
                const dt = Math.max(0.001, nearest.time_offset - prev.time_offset);
                const speed_mps = Cesium.Cartesian3.distance(p1, p2) / dt;
                hud.ias = speed_mps * 1.94384; // m/s to knots
            }
        }
    }
}
</script>

<style>
/* Leaflet/Cesium specific overrides if needed */
</style>
