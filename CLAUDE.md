# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**Exhibition Floorplan Interactive Mapping Application** - Converts AutoCAD DWG floorplans into interactive web-based maps with spatial analysis capabilities for event organizers and attendees.

**Problem Solved**: Bridges the gap between static CAD floorplans and dynamic, spatially-aware interactive maps that support wayfinding, proximity analysis, and booth capacity visualization.

## Technology Stack

### Backend
- **Framework**: Flask (Python web server)
- **DWG Processing**: ODA File Converter (external command-line tool)
- **DXF Parsing**: ezdxf (pure Python, excellent DXF support)
- **Spatial Analysis**: Shapely + GeoPandas (geometry operations, spatial queries)
- **Routing**: NetworkX (pathfinding algorithms)
- **Data Format**: GeoJSON (vector data interchange)

### Frontend
- **Mapping Library**: Leaflet.js (interactive zoomable maps)
- **UI**: HTML5 + CSS3 + Vanilla JavaScript
- **Coordinate System**: Leaflet's `CRS.Simple` (non-geographic, for indoor floorplans)

### Why This Stack
- ✅ **No Complex Dependencies**: All Python packages install via pip
- ✅ **Windows-Friendly**: ODA File Converter is official, reliable, and easy to install
- ✅ **Avoided PyQGIS**: Would require 2GB QGIS download + complex Windows configuration
- ✅ **Avoided GDAL**: Limited DWG support; ezdxf provides better DXF parsing
- ✅ **Proven Libraries**: Flask, Leaflet.js, Shapely are production-ready

## Architecture & Data Flow

```
User uploads DWG file
        ↓
[Flask] receives upload
        ↓
[ODA File Converter] converts DWG → DXF
        ↓
[ezdxf] parses DXF file → extracts booths, walkways, amenities
        ↓
[Shapely] processes geometries → calculates areas, capacity
        ↓
[GeoJSON] serializes booth/amenity data
        ↓
[Flask API] serves GeoJSON to frontend
        ↓
[Leaflet.js] renders interactive map in browser
        ↓
User interacts: search, zoom, click for info, route finding
```

### Key Design Decisions

1. **Closed Polyline Detection**: Booths are identified as closed polylines/rectangles with area-based filtering (50-5000 sq ft)
2. **Auto-Generated Booth IDs**: If no text labels present, IDs are generated as A-1, A-2, etc. based on spatial position
3. **Mock Capacity Data**: Current occupancy is randomly generated (60-95% of max) for POC demo purposes
4. **Local Coordinate System**: Uses arbitrary CAD coordinates, not real-world lat/long (appropriate for indoor floorplans)
5. **Lazy Loading**: Booth details loaded on-click, not all at once (performance optimization)

## Directory Structure

```
c:\QCIS-Project\
├── backend/
│   ├── app.py                    # Flask application, API endpoints
│   ├── dwg_processor.py          # DWG→DXF conversion, DXF parsing, booth extraction
│   ├── spatial_analysis.py       # Proximity analysis, routing, spatial queries
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── index.html                # Main UI (map container, search, filters)
│   ├── css/
│   │   └── style.css             # Styling (map, popups, sidebar)
│   └── js/
│       ├── map.js                # Leaflet initialization, booth rendering
│       ├── booth-info.js         # Booth popup interactions, info display
│       ├── routing.js            # Wayfinding UI and event handlers
│       └── spatial.js            # Proximity analysis features
├── data/
│   ├── uploads/                  # Temporary storage for uploaded DWG files
│   ├── processed/                # Generated DXF and GeoJSON files
│   └── sample/                   # Sample test files
├── CLAUDE.md                     # This file
├── README.md                     # User-facing documentation
└── .gitignore                    # Exclude uploads/, processed/, venv/
```

## Setup Instructions

### One-Time Environment Setup

1. **Install ODA File Converter** (required for DWG→DXF conversion)
   ```bash
   # Download from: https://www.opendesign.com/guestfiles/oda_file_converter
   # Run Windows installer
   # Verify: ODAFileConverter should be accessible from terminal
   ```

2. **Create Python virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **Create required directories**
   ```bash
   mkdir -p data/uploads data/processed data/sample
   ```

### Verification
- Test ODA converter: `ODAFileConverter` (should show help text)
- Test Python dependencies: `python -c "import flask, ezdxf, shapely, networkx"`

## Common Development Tasks

### Run the Application
```bash
# Activate environment (if not already)
venv\Scripts\activate

# Start Flask development server
python backend/app.py
# Server runs at http://localhost:5000
```

### Process a Sample DWG File
```bash
# Place DWG file in data/uploads/
# Upload via browser UI, or test backend directly:
python -c "from backend.dwg_processor import convert_dwg_to_dxf; convert_dwg_to_dxf('path/to/file.dwg', 'data/processed')"
```

### Test Spatial Analysis Functions
```bash
# Test individual functions (useful for debugging)
python -c "from backend.spatial_analysis import find_nearby_amenities; ..."
```

### Debug GeoJSON Output
- Uploaded GeoJSON files are saved in `data/processed/`
- Use online GeoJSON viewers (https://geojson.io) to visualize
- Check API responses: `http://localhost:5000/api/floorplan/<job_id>`

## Key Implementation Details

### Booth Identification Algorithm
1. Parse DXF file with ezdxf
2. Filter entities: keep only closed polylines/LWPOLYLINEs
3. Calculate area for each closed shape
4. Apply thresholds: area must be between 50-5000 sq ft
5. Convert to Shapely polygons for further processing

### Capacity Calculation
```python
max_occupancy = int(area_sqft / 10)  # 10 sq ft per person (industry standard)
current_occupancy = int(max_occupancy * random.uniform(0.6, 0.95))  # Mock data
```

### GeoJSON Properties
Each booth feature includes:
- `booth_id` (auto-generated or from CAD label)
- `area_sqft` (calculated from polygon area)
- `max_occupancy` (area / 10)
- `current_occupancy` (mock 60-95% of max)
- `occupancy_percentage` (for visualization)
- Placeholder fields for future exhibitor data: `exhibitor_name`, `category`, `description`, `contact`, `products`

### Routing Algorithm
1. Build network graph from walkway polylines (via NetworkX)
2. Find nearest graph nodes to start/end points
3. Calculate shortest path using Dijkstra's algorithm
4. Convert path to GeoJSON LineString for map visualization
5. Generate turn-by-turn directions based on path vertices

### Zoom-Dependent Visualization (Leaflet)
```javascript
map.on('zoomend', function() {
  if (map.getZoom() > 3) {
    // Show booth labels and capacity gauges
  } else {
    // Show only booth polygons (no labels)
  }
});
```

## Known Limitations & Mitigations

| Challenge | Impact | Mitigation |
|-----------|--------|-----------|
| **DWG file variability** | Different organizations structure CAD differently | Implement configurable filters for area thresholds, layer names; add debug logging |
| **Booth vs. non-booth detection** | Hard to distinguish booths from walls/furniture | Use area filtering (100-1000 sq ft typical); allow manual editing in future |
| **Missing amenity layer** | Restrooms/exits may not be standardized in CAD | Try layer name detection; fall back to manual addition via UI |
| **Real-time occupancy** | POC uses mock data only | Future: requires WiFi tracking, cameras, RFID, or manual clickers |
| **No exhibitor database** | Initial POC has only booth IDs | GeoJSON structure supports future database integration |

## Testing Strategy

### Manual Testing Checklist
1. **File Conversion**: Upload sample DWG → verify DXF created and parsed correctly
2. **Map Rendering**: Verify booths appear as polygons with auto-generated IDs
3. **Interactions**: Click booth → popup shows all info; search booth → highlights on map
4. **Routing**: Select two points → route draws on map with turn-by-turn directions
5. **Zoom Levels**: Low zoom shows overview; high zoom shows detailed labels + capacity gauges
6. **Mobile**: Test on tablet/phone; verify touch gestures work

### Unit Test Areas (to be implemented)
- DWG→DXF conversion with various file versions
- Booth identification (area filtering, closed polyline detection)
- Capacity calculation (area-based max occupancy)
- Routing pathfinding (shortest path correctness)
- API endpoint JSON structure and status codes

## Important Notes

- **ODA File Converter PATH**: If `ODAFileConverter` is not in system PATH, update `backend/dwg_processor.py` with full path
- **File Uploads**: Temporary DWG files are stored in `data/uploads/`; consider cleanup strategy for production
- **GeoJSON Size**: Large floorplans (>1000 booths) need clustering at low zoom levels
- **CORS**: If frontend is served separately, enable CORS in Flask app
- **Production**: POC uses file-based storage; production should use PostGIS database

## Future Enhancement Priorities

1. **Exhibitor Database Integration**: Link booth polygons to vendor information
2. **Real-Time Capacity Tracking**: WiFi/RFID-based occupancy detection
3. **Multi-Floor Support**: Handle multiple floor levels
4. **Admin Dashboard**: Organizer tools to manage events, edit booths, view analytics
5. **PWA Features**: Offline capability, installable web app

---

**Last Updated**: 2026-03-14
**Status**: Proof of Concept Implementation Plan
