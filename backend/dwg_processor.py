import os
import subprocess
import json
import random
from pathlib import Path

try:
    import ezdxf
except ImportError:
    print("Warning: ezdxf not installed. Run: pip install ezdxf")

try:
    from shapely.geometry import Polygon, Point
except ImportError:
    print("Warning: shapely not installed. Run: pip install shapely")


def convert_dwg_to_dxf(dwg_path, output_dir):
    """
    Convert DWG file to DXF using ODA File Converter

    Args:
        dwg_path: Path to input DWG file
        output_dir: Directory to save converted DXF file

    Returns:
        Path to converted DXF file, or None if conversion failed
    """
    try:
        # Create output directory if it doesn't exist
        os.makedirs(output_dir, exist_ok=True)

        # Check if ODA File Converter is available
        try:
            subprocess.run(['ODAFileConverter', '--help'],
                         capture_output=True,
                         timeout=5,
                         check=False)
        except FileNotFoundError:
            print("Warning: ODAFileConverter not found in PATH")
            print("For POC, attempting to parse DWG directly with ezdxf...")
            # Try to read DWG directly (ezdxf can sometimes handle this)
            try:
                doc = ezdxf.readfile(dwg_path)
                # If successful, save as DXF
                dxf_filename = Path(dwg_path).stem + '_converted.dxf'
                dxf_path = os.path.join(output_dir, dxf_filename)
                doc.saveas(dxf_path)
                return dxf_path
            except Exception as e:
                print(f"Direct DWG parsing failed: {e}")
                return None

        # Call ODA File Converter
        input_dir = os.path.dirname(dwg_path)
        filename = os.path.basename(dwg_path)

        print(f"Converting {filename} to DXF...")
        result = subprocess.run([
            'ODAFileConverter',
            input_dir,          # Input folder
            output_dir,         # Output folder
            'ACAD2018',         # Output version
            'DXF',              # Output format
            '0',                # Recurse subdirs (0=no)
            '1'                 # Audit (1=yes)
        ], capture_output=True, text=True, timeout=30)

        if result.returncode != 0:
            print(f"ODA conversion error: {result.stderr}")
            return None

        # Return path to converted DXF file
        dxf_filename = Path(filename).stem + '.dxf'
        dxf_path = os.path.join(output_dir, dxf_filename)

        if os.path.exists(dxf_path):
            print(f"Successfully converted to: {dxf_path}")
            return dxf_path
        else:
            print(f"DXF file not created at expected path: {dxf_path}")
            return None

    except subprocess.TimeoutExpired:
        print("ODA File Converter timed out")
        return None
    except Exception as e:
        print(f"Error during DWG conversion: {e}")
        return None


def parse_dxf(dxf_path):
    """
    Parse DXF file and extract entities

    Returns:
        Tuple of (booths, walkways, amenities) as lists of entities
    """
    try:
        doc = ezdxf.readfile(dxf_path)
        msp = doc.modelspace()

        booths = []
        walkways = []
        amenities = []

        print(f"Parsing DXF file: {dxf_path}")

        for entity in msp:
            dxf_type = entity.dxftype()

            # Closed polylines are potential booths
            if dxf_type in ['LWPOLYLINE', 'POLYLINE']:
                try:
                    if entity.is_closed:
                        booths.append(entity)
                    else:
                        walkways.append(entity)
                except:
                    walkways.append(entity)

            # Points are potential amenities
            elif dxf_type == 'POINT':
                amenities.append(entity)

        print(f"Extracted: {len(booths)} potential booths, {len(walkways)} walkways, {len(amenities)} points")
        return booths, walkways, amenities

    except Exception as e:
        print(f"Error parsing DXF: {e}")
        return [], [], []


def process_booth_geometry(polyline, min_area=50, max_area=5000):
    """
    Convert DXF polyline to Shapely polygon and calculate properties

    Returns:
        Dict with geometry and properties, or None if area is outside threshold
    """
    try:
        # Extract coordinates
        coords = []
        for point in polyline.get_points():
            coords.append((point[0], point[1]))

        if len(coords) < 3:
            return None

        # Create Shapely polygon
        polygon = Polygon(coords)

        # Validate polygon
        if not polygon.is_valid:
            return None

        # Calculate area
        area_sqft = polygon.area

        # Apply area filtering
        if area_sqft < min_area or area_sqft > max_area:
            return None

        # Calculate centroid and bounds
        centroid = polygon.centroid
        bounds = polygon.bounds

        return {
            'geometry': polygon,
            'area_sqft': round(area_sqft, 2),
            'centroid': (round(centroid.x, 2), round(centroid.y, 2)),
            'bounds': bounds
        }

    except Exception as e:
        print(f"Error processing booth geometry: {e}")
        return None


def calculate_capacity(area_sqft):
    """
    Calculate booth occupancy

    Industry standard: 10 sq ft per person for exhibitions
    """
    try:
        max_occupancy = max(1, int(area_sqft / 10))

        # Mock current occupancy (60-95% of max for demo)
        current_occupancy = int(max_occupancy * random.uniform(0.6, 0.95))

        return {
            'max_occupancy': max_occupancy,
            'current_occupancy': current_occupancy,
            'occupancy_percentage': round((current_occupancy / max_occupancy) * 100, 1)
        }
    except Exception as e:
        print(f"Error calculating capacity: {e}")
        return {
            'max_occupancy': 0,
            'current_occupancy': 0,
            'occupancy_percentage': 0
        }


def assign_booth_ids(booths_with_geometry):
    """
    Assign booth IDs based on spatial position
    Sort by Y coordinate (rows), then X coordinate (columns)
    Generate IDs: A-1, A-2, A-3, ... B-1, B-2, etc.
    """
    if not booths_with_geometry:
        return []

    # Sort by Y (rows), then X (columns)
    sorted_booths = sorted(
        booths_with_geometry,
        key=lambda b: (-b['centroid'][1], b['centroid'][0])  # Note: negative Y for top-to-bottom
    )

    # Group into rows (similar Y coordinates)
    rows = []
    current_row = []
    row_threshold = 50  # If Y differs by more than 50 units, new row

    for booth in sorted_booths:
        if current_row and abs(booth['centroid'][1] - current_row[0]['centroid'][1]) > row_threshold:
            rows.append(current_row)
            current_row = [booth]
        else:
            current_row.append(booth)

    if current_row:
        rows.append(current_row)

    # Sort each row by X coordinate and assign IDs
    booth_ids = []
    for row_idx, row in enumerate(rows):
        sorted_row = sorted(row, key=lambda b: b['centroid'][0])
        for col_idx, booth in enumerate(sorted_row):
            row_letter = chr(65 + row_idx)  # A, B, C, ...
            booth_id = f"{row_letter}-{col_idx + 1}"
            booth['booth_id'] = booth_id
            booth_ids.append(booth)

    return booth_ids


def booths_to_geojson(booths_with_ids):
    """
    Convert booth geometries to GeoJSON FeatureCollection
    """
    features = []

    for booth in booths_with_ids:
        try:
            geometry = booth['geometry']

            # Convert Shapely polygon to GeoJSON coordinates
            coords = list(geometry.exterior.coords)
            geojson_coords = [coords]  # Add hole support (empty for simple polygons)

            capacity = calculate_capacity(booth['area_sqft'])

            feature = {
                'type': 'Feature',
                'geometry': {
                    'type': 'Polygon',
                    'coordinates': geojson_coords
                },
                'properties': {
                    'booth_id': booth['booth_id'],
                    'area_sqft': booth['area_sqft'],
                    'max_occupancy': capacity['max_occupancy'],
                    'current_occupancy': capacity['current_occupancy'],
                    'occupancy_percentage': capacity['occupancy_percentage'],
                    'category': 'Unassigned',
                    'exhibitor_name': None,
                    'description': None,
                    'contact': None,
                    'products': []
                }
            }

            features.append(feature)

        except Exception as e:
            print(f"Error converting booth to GeoJSON: {e}")
            continue

    return {
        'type': 'FeatureCollection',
        'features': features,
        'metadata': {
            'created': str(Path.cwd()),
            'booth_count': len(features),
            'coordinate_system': 'Local (CAD coordinates)'
        }
    }


def process_dwg_file(dwg_path, output_dir):
    """
    Complete DWG/DXF processing pipeline:
    DWG → DXF → Parse → Extract Booths → Calculate Properties → GeoJSON
    OR (for DXF files):
    DXF → Parse → Extract Booths → Calculate Properties → GeoJSON

    Returns:
        GeoJSON FeatureCollection, or None if processing failed
    """
    try:
        print("\n" + "="*60)
        print("Floorplan Processing Pipeline Started")
        print("="*60)

        # Step 0: Check if file is already DXF
        if dwg_path.lower().endswith('.dxf'):
            print("\n[Step 1] DXF file detected - skipping conversion...")
            dxf_path = dwg_path
        else:
            # Step 1: Convert DWG to DXF
            print("\n[Step 1] Converting DWG to DXF...")
            dxf_path = convert_dwg_to_dxf(dwg_path, output_dir)

        if not dxf_path:
            print("Failed to convert DWG to DXF")
            return None

        # Step 2: Parse DXF
        print("\n[Step 2] Parsing DXF file...")
        booths_raw, walkways, amenities = parse_dxf(dxf_path)

        if not booths_raw:
            print("No booths found in DXF file")
            return None

        # Step 3: Process booth geometries
        print("\n[Step 3] Processing booth geometries...")
        booths_processed = []
        for booth in booths_raw:
            processed = process_booth_geometry(booth)
            if processed:
                booths_processed.append(processed)

        print(f"Valid booths after filtering: {len(booths_processed)}")

        if not booths_processed:
            print("No valid booths after geometry filtering")
            return None

        # Step 4: Assign booth IDs
        print("\n[Step 4] Assigning booth IDs...")
        booths_with_ids = assign_booth_ids(booths_processed)

        # Step 5: Export to GeoJSON
        print("\n[Step 5] Exporting to GeoJSON...")
        geojson = booths_to_geojson(booths_with_ids)

        # Save GeoJSON to file
        geojson_filename = f"{Path(dwg_path).stem}_floorplan.geojson"
        geojson_path = os.path.join(output_dir, geojson_filename)

        with open(geojson_path, 'w') as f:
            json.dump(geojson, f, indent=2)

        print(f"GeoJSON saved to: {geojson_path}")

        print("\n" + "="*60)
        print(f"Processing Complete! Found {len(booths_with_ids)} booths")
        print("="*60 + "\n")

        return geojson

    except Exception as e:
        print(f"Error in DWG processing pipeline: {e}")
        import traceback
        traceback.print_exc()
        return None
