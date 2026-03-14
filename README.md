# Exhibition Floorplan Interactive Mapping Application

An interactive web-based mapping application that converts AutoCAD DWG/DXF floorplans into digital maps with spatial analysis capabilities for event organizers and attendees.

## Features

- 📍 **Interactive Zoomable Floorplan**: Leaflet.js-based map showing booth polygons
- 🔍 **Booth Search**: Search by booth ID and instantly locate on map
- 📊 **Capacity Visualization**: Color-coded booths by occupancy (Green: <60%, Yellow: 60-80%, Red: 80%+)
- 🚦 **Wayfinding**: Calculate shortest path between booths with turn-by-turn directions
- 📏 **Proximity Analysis**: Find nearby amenities and booths
- 📈 **Live Statistics**: Total booths, capacity, and occupancy rate
- 🎯 **Automatic Booth Detection**: Extracts closed polylines from CAD files as individual booths

## Tech Stack

- **Backend**: Flask (Python)
- **CAD Processing**: ODA File Converter + ezdxf (DXF parsing)
- **Spatial Analysis**: Shapely + GeoPandas
- **Routing**: NetworkX (Dijkstra's algorithm)
- **Frontend**: Leaflet.js + HTML5/CSS3/JavaScript
- **Data Format**: GeoJSON

## Installation

### Requirements
- Python 3.8+
- ODA File Converter (optional, for DWG support)

### Setup

1. **Clone the repository**
   ```bash
   git clone <your-repo-url>
   cd QCIS-Project
   ```

2. **Create virtual environment**
   ```bash
   python -m venv venv
   venv\Scripts\activate  # Windows
   source venv/bin/activate  # macOS/Linux
   ```

3. **Install dependencies**
   ```bash
   pip install -r backend/requirements.txt
   ```

4. **(Optional) Install ODA File Converter**
   - Download from: https://www.opendesign.com/guestfiles/oda_file_converter
   - Run installer
   - Verify: `ODAFileConverter` should work in terminal

5. **Create required directories**
   ```bash
   mkdir -p data/uploads data/processed data/sample
   ```

## Usage

### Start the Application

```bash
python backend/app.py
```

Then open in your browser:
```
http://localhost:5000
```

### Upload a DXF/DWG File

1. Click the upload box
2. Select your DXF or DWG file
3. Wait for processing (shows "Processing complete! Found X booths")
4. Booths will render on the interactive map

### Generate Sample Data

```bash
python backend/create_sample_dxf.py
```

This creates `data/sample/test_floorplan.dxf` with 6 sample booths for testing.

## API Endpoints

- `POST /api/upload` - Upload and process DWG/DXF file
- `GET /api/floorplan/<job_id>` - Retrieve booth GeoJSON
- `GET /api/booth/<job_id>/<booth_id>` - Get booth details with nearby amenities
- `GET /api/search/<job_id>?q=<query>` - Search booths by ID
- `POST /api/route/<job_id>` - Calculate route between booths
- `GET /api/health` - Health check

## Project Structure

```
c:\QCIS-Project\
├── backend/
│   ├── app.py                    # Flask API server
│   ├── dwg_processor.py          # DWG→DXF conversion, booth extraction
│   ├── spatial_analysis.py       # Proximity and routing analysis
│   └── requirements.txt          # Python dependencies
├── frontend/
│   ├── index.html                # Main UI
│   ├── css/
│   │   └── style.css             # Application styling
│   └── js/
│       ├── map.js                # Leaflet map initialization
│       ├── booth-info.js         # Booth details popup
│       ├── routing.js            # Wayfinding UI
│       └── spatial.js            # Proximity analysis
├── data/
│   ├── uploads/                  # Temporary uploaded files
│   ├── processed/                # Generated GeoJSON outputs
│   └── sample/                   # Sample DXF files for testing
├── CLAUDE.md                     # Development guidelines
├── README.md                     # This file
└── .gitignore
```

## How It Works

### DWG Processing Pipeline

```
DWG/DXF Upload
    ↓
[ODA File Converter] (converts DWG → DXF)
    ↓
[ezdxf] (parses DXF file)
    ↓
[Closed Polyline Detection] (identifies booths)
    ↓
[Area Filtering] (50-5000 sq ft threshold)
    ↓
[Spatial Sorting] (generates IDs: A-1, A-2, etc.)
    ↓
[Capacity Calculation] (10 sq ft per person)
    ↓
[GeoJSON Export] (sends to frontend)
    ↓
[Leaflet Rendering] (displays on interactive map)
```

### Booth Detection

- Booths are identified as **closed polylines** in the DXF file
- Area must be between **50-5000 sq ft**
- Booths are auto-assigned IDs based on spatial position
- Capacity calculated as: `max_occupancy = area_sqft / 10`

## Known Limitations

- POC uses mock occupancy data (60-95% of max capacity)
- No real-time tracking (requires sensor integration)
- Single floor only (no multi-floor support yet)
- File-based storage (no database persistence)

## Future Enhancements

- [ ] Real-time capacity tracking (WiFi/RFID)
- [ ] Exhibitor database integration
- [ ] Multi-floor support
- [ ] Admin dashboard for organizers
- [ ] QR codes linking to digital map
- [ ] PWA (offline capability)

## Troubleshooting

### No booths appear on map
- Check browser console (F12) for errors
- Verify DXF file has closed rectangles
- Ensure booth sizes are 50-5000 sq ft

### DWG conversion fails
- Install ODA File Converter OR
- Convert DWG to DXF manually in AutoCAD

### Map shows statistics but no booths
- This usually means the map bounds are misconfigured
- Try zooming out (scroll wheel or - button)
- Refresh browser and re-upload file

## Contributing

This is a proof-of-concept application. Feel free to extend with:
- Better booth detection algorithms
- Real-time data integration
- Advanced spatial queries
- Multi-floor support

## License

MIT License - feel free to use and modify

## Contact

For issues or questions about this application, please refer to the CLAUDE.md file for development context.

---

**Last Updated**: March 14, 2026
**Status**: Proof of Concept
