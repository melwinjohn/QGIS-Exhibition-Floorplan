// Spatial analysis and proximity features

function showNearbyBooths(boothId, radius = 200) {
    """
    Highlight booths within a certain radius of the selected booth
    """
    if (!boothLayers[boothId]) return;

    const centerBooth = boothLayers[boothId];
    const centerPoint = centerBooth.polygon.getBounds().getCenter();

    // Clear previous highlights
    Object.values(boothLayers).forEach(({ polygon }) => {
        polygon.setStyle({ weight: 2, fillOpacity: 0.6 });
    });

    // Highlight nearby booths
    let nearbyCount = 0;
    Object.entries(boothLayers).forEach(([id, { polygon, feature }]) => {
        if (id === boothId) {
            polygon.setStyle({ weight: 3, fillOpacity: 0.8 });
            return;
        }

        const boothPoint = polygon.getBounds().getCenter();
        const distance = centerPoint.distanceTo(boothPoint);

        if (distance <= radius) {
            polygon.setStyle({
                weight: 2.5,
                fillOpacity: 0.7,
                color: '#f39c12',
                fillColor: '#f39c12'
            });
            nearbyCount++;
        }
    });

    return nearbyCount;
}

function filterBoothsByOccupancy(minOccupancy = 0, maxOccupancy = 100) {
    """
    Filter booths by occupancy percentage range
    """
    const filtered = [];

    Object.values(boothLayers).forEach(({ polygon, feature }) => {
        const occ = feature.properties.occupancy_percentage;

        if (occ >= minOccupancy && occ <= maxOccupancy) {
            polygon.setStyle({ fillOpacity: 0.8 });
            filtered.push(feature);
        } else {
            polygon.setStyle({ fillOpacity: 0.2 });
        }
    });

    return filtered;
}

function highlightByCapacity() {
    """
    Color-code booths by occupancy level
    """
    Object.values(boothLayers).forEach(({ polygon, feature }) => {
        const occ = feature.properties.occupancy_percentage;
        let color, fillColor;

        if (occ < 60) {
            color = fillColor = '#27ae60'; // Green - Low occupancy
        } else if (occ < 80) {
            color = fillColor = '#f39c12'; // Orange - Medium occupancy
        } else {
            color = fillColor = '#e74c3c'; // Red - High occupancy
        }

        polygon.setStyle({
            color: color,
            fillColor: fillColor,
            fillOpacity: 0.6,
            weight: 2
        });
    });
}

function calculateProximityStats(boothId, radius = 300) {
    """
    Calculate statistics for booths within radius of selected booth
    """
    if (!boothLayers[boothId]) return null;

    const centerBooth = boothLayers[boothId];
    const centerPoint = centerBooth.polygon.getBounds().getCenter();

    let totalCapacity = 0;
    let totalOccupancy = 0;
    let boothCount = 0;

    Object.entries(boothLayers).forEach(([id, { polygon, feature }]) => {
        const boothPoint = polygon.getBounds().getCenter();
        const distance = centerPoint.distanceTo(boothPoint);

        if (distance <= radius && distance > 0) {
            totalCapacity += feature.properties.max_occupancy || 0;
            totalOccupancy += feature.properties.current_occupancy || 0;
            boothCount++;
        }
    });

    return {
        boothCount,
        totalCapacity,
        totalOccupancy,
        occupancyPercentage: totalCapacity > 0 ? Math.round((totalOccupancy / totalCapacity) * 100) : 0
    };
}

function getBoothsByCategory(category) {
    """
    Filter booths by category (if implemented in future)
    """
    const filtered = [];

    Object.values(boothLayers).forEach(({ feature }) => {
        if (feature.properties.category === category) {
            filtered.push(feature);
        }
    });

    return filtered;
}

function highlightCrowd() {
    """
    Highlight most crowded booths (high occupancy)
    """
    const sorted = Array.from(Object.values(boothLayers))
        .sort((a, b) => {
            const aOcc = a.feature.properties.occupancy_percentage;
            const bOcc = b.feature.properties.occupancy_percentage;
            return bOcc - aOcc;
        });

    // Highlight top 5 most crowded
    sorted.slice(0, 5).forEach(({ polygon }) => {
        polygon.setStyle({
            fillOpacity: 0.9,
            weight: 3,
            color: '#c0392b'
        });
    });

    // Dim others
    sorted.slice(5).forEach(({ polygon }) => {
        polygon.setStyle({
            fillOpacity: 0.3,
            weight: 1,
            color: '#bdc3c7'
        });
    });
}

function resetSpatialHighlights() {
    """
    Reset all spatial visualization highlights
    """
    highlightByCapacity();
}
