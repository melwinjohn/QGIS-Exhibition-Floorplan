// Global variables
let map;
let currentJobId;
let boothsGeoJSON;
let boothLayers = {};
let selectedBooth = null;

// Initialize map on page load
document.addEventListener('DOMContentLoaded', function() {
    initializeMap();
    setupFileUpload();
    setupEventListeners();
});

function initializeMap() {
    // Initialize Leaflet map with simple CRS (for local coordinates, not real-world)
    map = L.map('map', {
        crs: L.CRS.Simple,
        minZoom: -10,
        maxZoom: 10,
        zoom: 1,
        center: [0, 0]
    });

    console.log('Map initialized - ready for booth data');
}

function setupFileUpload() {
    const uploadBox = document.getElementById('uploadBox');
    const fileInput = document.getElementById('fileInput');

    // Click to upload
    uploadBox.addEventListener('click', () => fileInput.click());

    // File input change
    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            uploadFile(e.target.files[0]);
        }
    });

    // Drag and drop
    uploadBox.addEventListener('dragover', (e) => {
        e.preventDefault();
        uploadBox.style.borderColor = '#e74c3c';
        uploadBox.style.backgroundColor = '#fadbd8';
    });

    uploadBox.addEventListener('dragleave', () => {
        uploadBox.style.borderColor = '#3498db';
        uploadBox.style.backgroundColor = '#f8f9fa';
    });

    uploadBox.addEventListener('drop', (e) => {
        e.preventDefault();
        uploadBox.style.borderColor = '#3498db';
        uploadBox.style.backgroundColor = '#f8f9fa';
        if (e.dataTransfer.files.length > 0) {
            uploadFile(e.dataTransfer.files[0]);
        }
    });
}

function uploadFile(file) {
    if (!file.name.toLowerCase().endsWith('.dwg') && !file.name.toLowerCase().endsWith('.dxf')) {
        alert('Please upload a DWG or DXF file');
        return;
    }

    // Show loading state
    const uploadBox = document.getElementById('uploadBox');
    const uploadStatus = document.getElementById('uploadStatus');
    const statusText = document.getElementById('statusText');

    uploadBox.style.display = 'none';
    uploadStatus.style.display = 'block';
    statusText.textContent = 'Uploading file...';

    // Create form data
    const formData = new FormData();
    formData.append('file', file);

    // Send to server
    fetch('/api/upload', {
        method: 'POST',
        body: formData
    })
    .then(response => response.json())  // Always parse JSON first (both success and error responses)
    .then(data => {
        if (data.error) {
            throw new Error(data.error);  // This now gets the detailed error message from the backend
        }

        currentJobId = data.job_id;
        statusText.textContent = `Processing complete! Found ${data.booth_count} booths`;

        // Load floorplan after a short delay
        setTimeout(() => {
            loadFloorplan(currentJobId);
        }, 500);
    })
    .catch(error => {
        console.error('Upload error:', error);

        // Create detailed error message
        let errorHTML = '<strong style="color: #e74c3c;">Upload Failed</strong><br>';
        errorHTML += error.message + '<br><br>';
        errorHTML += '<small style="color: #7f8c8d;"><strong>Tips:</strong><br>';
        errorHTML += '• Use DXF files (recommended for testing)<br>';
        errorHTML += '• Or install ODA File Converter for DWG files<br>';
        errorHTML += '• Download from: https://www.opendesign.com/guestfiles/oda_file_converter</small>';

        statusText.innerHTML = errorHTML;
        statusText.style.color = '#e74c3c';

        // Keep error visible
        uploadBox.style.display = 'block';
        uploadStatus.style.display = 'block';
    });
}

function loadFloorplan(jobId) {
    fetch(`/api/floorplan/${jobId}`)
        .then(response => {
            if (!response.ok) throw new Error('Failed to load floorplan');
            return response.json();
        })
        .then(geojson => {
            boothsGeoJSON = geojson;

            // Clear existing layers
            Object.values(boothLayers).forEach(layer => map.removeLayer(layer));
            boothLayers = {};

            // Add booth layers
            renderBooths(geojson);

            // Show sidebar sections
            document.getElementById('searchSection').style.display = 'block';
            document.getElementById('statsSection').style.display = 'block';

            // Calculate and display statistics
            updateStatistics(geojson);

            // Fit map to booths
            fitMapToBooths(geojson);

            // Hide upload status
            document.getElementById('uploadBox').style.display = 'block';
            document.getElementById('uploadStatus').style.display = 'none';

            console.log(`Loaded ${geojson.features.length} booths`);
        })
        .catch(error => {
            console.error('Floorplan load error:', error);
            alert('Failed to load floorplan');
        });
}

function renderBooths(geojson) {
    const features = geojson.features || [];
    console.log(`Rendering ${features.length} booths...`);

    features.forEach(feature => {
        if (feature.geometry.type !== 'Polygon') return;

        const coords = feature.geometry.coordinates[0];
        const boothId = feature.properties.booth_id;

        // Convert GeoJSON coordinates to Leaflet format
        const latLngs = coords.map(coord => [coord[1], coord[0]]);

        // Determine color based on occupancy
        const occupancy = feature.properties.occupancy_percentage || 0;
        let color, fillColor;

        if (occupancy < 60) {
            color = fillColor = '#27ae60'; // Green
        } else if (occupancy < 80) {
            color = fillColor = '#f39c12'; // Orange
        } else {
            color = fillColor = '#e74c3c'; // Red
        }

        // Create polygon layer
        const polygon = L.polygon(latLngs, {
            color: color,
            fillColor: fillColor,
            fillOpacity: 0.6,
            weight: 2,
            className: 'booth-polygon'
        }).addTo(map);

        // Add booth ID label at high zoom levels
        const bounds = L.latLngBounds(latLngs);
        const center = bounds.getCenter();

        // Create a marker for the label
        const marker = L.marker(center, {
            icon: L.divIcon({
                className: 'booth-label',
                html: `<div style="font-weight: bold; font-size: 12px; color: white; text-shadow: 1px 1px 2px black;">${boothId}</div>`,
                iconSize: [50, 30]
            })
        }).addTo(map);

        // Create popup
        const popupContent = createBoothPopup(feature);

        polygon.bindPopup(popupContent, {
            maxWidth: 300,
            minWidth: 250
        });

        marker.bindPopup(popupContent, {
            maxWidth: 300,
            minWidth: 250
        });

        // Click events
        polygon.on('click', () => {
            selectBooth(feature, polygon);
        });

        marker.on('click', () => {
            selectBooth(feature, polygon);
        });

        // Store reference
        boothLayers[boothId] = { polygon, marker, feature };
    });

    // Hide labels at low zoom levels
    map.on('zoomend', updateLabelsVisibility);
    updateLabelsVisibility();
}

function updateLabelsVisibility() {
    const zoomLevel = map.getZoom();
    Object.values(boothLayers).forEach(({ marker }) => {
        if (zoomLevel > 2) {
            marker.setOpacity(1);
        } else {
            marker.setOpacity(0);
        }
    });
}

function createBoothPopup(feature) {
    const props = feature.properties;
    const html = `
        <div class="booth-popup">
            <h3>${props.booth_id}</h3>
            <div class="booth-popup-item">
                <strong>Area:</strong> ${props.area_sqft} sq ft
            </div>
            <div class="booth-popup-item">
                <strong>Capacity:</strong> ${props.current_occupancy}/${props.max_occupancy}
            </div>
            <div class="booth-popup-item">
                <div style="margin-bottom: 4px;">
                    <strong>Occupancy:</strong> ${props.occupancy_percentage}%
                </div>
                <div style="width: 100%; height: 16px; background: #e0e0e0; border-radius: 8px; overflow: hidden;">
                    <div style="width: ${props.occupancy_percentage}%; height: 100%; background: linear-gradient(90deg, #27ae60, #f39c12, #e74c3c);"></div>
                </div>
            </div>
            <button class="btn btn-primary" style="width: 100%; margin-top: 10px;" onclick="selectBoothFromPopup('${props.booth_id}')">
                View Details
            </button>
        </div>
    `;
    return html;
}

function selectBooth(feature, polygon) {
    // Remove previous highlight
    Object.values(boothLayers).forEach(({ polygon: p }) => {
        p.setStyle({ weight: 2, fillOpacity: 0.6 });
    });

    // Highlight selected booth
    polygon.setStyle({ weight: 3, fillOpacity: 0.8 });
    selectedBooth = feature;

    // Show booth details
    showBoothDetails(feature);
}

function selectBoothFromPopup(boothId) {
    const boothLayer = boothLayers[boothId];
    if (boothLayer) {
        selectBooth(boothLayer.feature, boothLayer.polygon);
    }
}

function showBoothDetails(feature) {
    const props = feature.properties;

    document.getElementById('boothInfo').style.display = 'block';
    document.getElementById('boothId').textContent = props.booth_id;
    document.getElementById('boothArea').textContent = props.area_sqft;
    document.getElementById('boothCapacity').textContent = `${props.max_occupancy} people`;
    document.getElementById('boothOccupancy').textContent = `${props.current_occupancy}/${props.max_occupancy} (${props.occupancy_percentage}%)`;

    // Update capacity bar
    const capacityFill = document.getElementById('capacityFill');
    capacityFill.style.width = props.occupancy_percentage + '%';

    // Update nearby booths (simplified)
    const nearbyList = document.getElementById('nearbyList');
    nearbyList.innerHTML = '<li>Loading nearby booths...</li>';

    // Fetch nearby amenities
    fetch(`/api/booth/${currentJobId}/${props.booth_id}`)
        .then(r => r.json())
        .then(data => {
            const nearby = data.properties.nearby_amenities || [];
            if (nearby.length === 0) {
                nearbyList.innerHTML = '<li>No nearby booths</li>';
            } else {
                nearbyList.innerHTML = nearby.map(b =>
                    `<li>${b.booth_id} (${b.distance.toFixed(0)} units away)</li>`
                ).join('');
            }
        })
        .catch(err => {
            nearbyList.innerHTML = '<li>Error loading nearby booths</li>';
            console.error('Error loading nearby booths:', err);
        });
}

function fitMapToBooths(geojson) {
    if (geojson.features.length === 0) return;

    let minX = Infinity, maxX = -Infinity, minY = Infinity, maxY = -Infinity;

    geojson.features.forEach(feature => {
        if (feature.geometry.type === 'Polygon') {
            feature.geometry.coordinates[0].forEach(coord => {
                minX = Math.min(minX, coord[0]);
                maxX = Math.max(maxX, coord[0]);
                minY = Math.min(minY, coord[1]);
                maxY = Math.max(maxY, coord[1]);
            });
        }
    });

    console.log(`Map bounds: minX=${minX}, maxX=${maxX}, minY=${minY}, maxY=${maxY}`);
    const bounds = [[minY, minX], [maxY, maxX]];
    console.log(`Fitting map to bounds:`, bounds);

    // Use larger padding for large venues and set maxZoom to ensure we see everything
    map.fitBounds(bounds, {
        padding: [50, 50],
        maxZoom: 8  // Limit zoom so entire venue is visible
    });
}

function updateStatistics(geojson) {
    const features = geojson.features || [];

    const totalBooths = features.length;
    const totalCapacity = features.reduce((sum, f) => sum + (f.properties.max_occupancy || 0), 0);
    const currentOccupancy = features.reduce((sum, f) => sum + (f.properties.current_occupancy || 0), 0);
    const occupancyRate = totalCapacity > 0 ? Math.round((currentOccupancy / totalCapacity) * 100) : 0;

    document.getElementById('totalBooths').textContent = totalBooths;
    document.getElementById('totalCapacity').textContent = totalCapacity;
    document.getElementById('currentOccupancy').textContent = currentOccupancy;
    document.getElementById('occupancyRate').textContent = `${occupancyRate}%`;
}

function setupEventListeners() {
    // These will be set up in booth-info.js and routing.js
}
