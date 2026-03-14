// Booth info handling

document.addEventListener('DOMContentLoaded', function() {
    // Search functionality
    const searchBtn = document.getElementById('searchBtn');
    const clearSearchBtn = document.getElementById('clearSearchBtn');
    const searchInput = document.getElementById('searchInput');

    searchBtn.addEventListener('click', searchBooths);
    clearSearchBtn.addEventListener('click', clearSearch);

    searchInput.addEventListener('keypress', (e) => {
        if (e.key === 'Enter') {
            searchBooths();
        }
    });
});

function searchBooths() {
    if (!currentJobId) {
        alert('Please upload a floorplan first');
        return;
    }

    const query = document.getElementById('searchInput').value.trim();

    if (!query) {
        alert('Please enter a booth ID to search');
        return;
    }

    // Clear previous highlights
    Object.values(boothLayers).forEach(({ polygon }) => {
        polygon.setStyle({ weight: 2, fillOpacity: 0.6 });
    });

    // Find matching booth
    const boothLayer = boothLayers[query.toUpperCase()];

    if (!boothLayer) {
        alert(`Booth ${query} not found`);
        return;
    }

    // Highlight and select booth
    const { polygon, feature } = boothLayer;
    selectBooth(feature, polygon);

    // Pan to booth
    map.setView(polygon.getBounds().getCenter(), 3);

    // Open popup
    polygon.openPopup();
}

function clearSearch() {
    document.getElementById('searchInput').value = '';

    // Clear highlights
    Object.values(boothLayers).forEach(({ polygon }) => {
        polygon.setStyle({ weight: 2, fillOpacity: 0.6 });
    });

    // Close any open popups
    map.closePopup();

    // Hide details
    document.getElementById('boothInfo').style.display = 'none';
    document.getElementById('routeSection').style.display = 'none';
}

// Debounce function for search-as-you-type (optional future feature)
function debounce(func, wait) {
    let timeout;
    return function executedFunction(...args) {
        const later = () => {
            clearTimeout(timeout);
            func(...args);
        };
        clearTimeout(timeout);
        timeout = setTimeout(later, wait);
    };
}
