// Routing and wayfinding functionality

let currentRoute = null;
let routeLayer = null;

document.addEventListener('DOMContentLoaded', function() {
    const routeBtn = document.getElementById('routeBtn');
    const clearRouteBtn = document.getElementById('clearRouteBtn');

    routeBtn.addEventListener('click', initiateRouting);
    clearRouteBtn.addEventListener('click', clearRoute);
});

function initiateRouting() {
    if (!selectedBooth) {
        alert('Please select a booth first');
        return;
    }

    const destinationBoothId = selectedBooth.properties.booth_id;

    // Prompt for starting booth
    const startingBooth = prompt(
        `Enter the starting booth ID (or "entrance"):\n\nGoing TO: ${destinationBoothId}`,
        'A-1'
    );

    if (!startingBooth) return;

    // Get starting booth feature
    let fromFeature;

    if (startingBooth.toUpperCase() === 'ENTRANCE') {
        // Create a virtual entrance point (center of map)
        fromFeature = {
            properties: { booth_id: 'ENTRANCE' },
            geometry: {
                type: 'Point',
                coordinates: [0, 0]
            }
        };
    } else {
        const boothLayer = boothLayers[startingBooth.toUpperCase()];
        if (!boothLayer) {
            alert(`Starting booth ${startingBooth} not found`);
            return;
        }
        fromFeature = boothLayer.feature;
    }

    calculateRoute(fromFeature, selectedBooth);
}

function calculateRoute(fromFeature, toFeature) {
    // Clear previous route
    if (routeLayer) {
        map.removeLayer(routeLayer);
    }

    fetch(`/api/route/${currentJobId}`, {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json'
        },
        body: JSON.stringify({
            from: fromFeature.properties.booth_id,
            to: toFeature.properties.booth_id
        })
    })
    .then(response => {
        if (!response.ok) throw new Error('Failed to calculate route');
        return response.json();
    })
    .then(routeData => {
        currentRoute = routeData;

        // Draw route on map
        if (routeData.geometry) {
            const coords = routeData.geometry.coordinates.map(coord => [coord[1], coord[0]]);
            routeLayer = L.polyline(coords, {
                color: '#2980b9',
                weight: 4,
                opacity: 0.8,
                dashArray: '5, 5',
                className: 'route-line'
            }).addTo(map);

            // Fit map to show entire route
            const bounds = L.latLngBounds(coords);
            map.fitBounds(bounds, { padding: [50, 50] });
        }

        // Display route information
        displayRouteInfo(routeData);
    })
    .catch(error => {
        console.error('Route calculation error:', error);
        alert('Failed to calculate route');
    });
}

function displayRouteInfo(routeData) {
    const routeSection = document.getElementById('routeSection');
    const routeDistance = document.getElementById('routeDistance');
    const directionsList = document.getElementById('directionsList');

    routeSection.style.display = 'block';

    const distance = routeData.properties.total_distance;
    routeDistance.textContent = `Distance: ${distance.toFixed(1)} units`;

    // Build directions list
    const directions = routeData.properties.directions || [];
    directionsList.innerHTML = directions.map(dir =>
        `<li>${dir.instruction}</li>`
    ).join('');
}

function clearRoute() {
    if (routeLayer) {
        map.removeLayer(routeLayer);
        routeLayer = null;
    }

    currentRoute = null;
    document.getElementById('routeSection').style.display = 'none';

    // Reset map view to fit all booths
    if (boothsGeoJSON) {
        fitMapToBooths(boothsGeoJSON);
    }
}

// Snap routing to specific booths for more accurate wayfinding
function snapToBoothCenter(boothId) {
    const boothLayer = boothLayers[boothId];
    if (boothLayer) {
        const bounds = boothLayer.polygon.getBounds();
        return bounds.getCenter();
    }
    return null;
}
