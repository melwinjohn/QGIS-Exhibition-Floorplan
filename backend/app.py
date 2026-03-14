import os
import json
import uuid
from flask import Flask, render_template, request, jsonify, send_from_directory
from datetime import datetime
from dwg_processor import convert_dwg_to_dxf, process_dwg_file
from spatial_analysis import find_nearby_amenities, calculate_route

app = Flask(__name__, template_folder='../frontend')

# Configuration
FRONTEND_PATH = os.path.join(os.path.dirname(__file__), '..', 'frontend')
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'uploads')
PROCESSED_FOLDER = os.path.join(os.path.dirname(__file__), '..', 'data', 'processed')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(PROCESSED_FOLDER, exist_ok=True)

# In-memory storage for processing jobs (POC only - would use database in production)
jobs = {}

@app.route('/')
def index():
    """Serve main HTML interface"""
    return send_from_directory(FRONTEND_PATH, 'index.html')

# Static file routes for CSS
@app.route('/css/<path:filename>')
def serve_css(filename):
    """Serve CSS files"""
    return send_from_directory(os.path.join(FRONTEND_PATH, 'css'), filename)

# Static file routes for JavaScript
@app.route('/js/<path:filename>')
def serve_js(filename):
    """Serve JavaScript files"""
    return send_from_directory(os.path.join(FRONTEND_PATH, 'js'), filename)

@app.route('/api/upload', methods=['POST'])
def upload_file():
    """Handle DWG file upload and processing"""
    if 'file' not in request.files:
        return jsonify({'error': 'No file provided'}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({'error': 'No file selected'}), 400

    if not (file.filename.lower().endswith('.dwg') or file.filename.lower().endswith('.dxf')):
        return jsonify({'error': 'Only DWG and DXF files are supported'}), 400

    try:
        # Generate job ID
        job_id = str(uuid.uuid4())[:8]

        # Save uploaded file
        filename = f"{job_id}_{file.filename}"
        filepath = os.path.join(UPLOAD_FOLDER, filename)
        file.save(filepath)

        # Process DWG file
        print(f"[{job_id}] Processing DWG file: {filename}")
        geojson_data = process_dwg_file(filepath, PROCESSED_FOLDER)

        if not geojson_data:
            return jsonify({'error': 'Failed to process DWG file'}), 400

        # Store job info
        jobs[job_id] = {
            'status': 'completed',
            'filename': filename,
            'timestamp': datetime.now().isoformat(),
            'booth_count': len(geojson_data.get('features', [])),
            'geojson': geojson_data
        }

        print(f"[{job_id}] Processing complete. Found {jobs[job_id]['booth_count']} booths")

        return jsonify({
            'job_id': job_id,
            'status': 'completed',
            'booth_count': jobs[job_id]['booth_count'],
            'message': f'Successfully processed DWG file. Found {jobs[job_id]["booth_count"]} booths.'
        }), 200

    except Exception as e:
        error_msg = str(e)
        print(f"Error processing file: {error_msg}")

        # Provide helpful error messages
        if 'No booths' in error_msg or 'No valid booths' in error_msg:
            error_msg = (
                'No booths found in the file. Please check:\n'
                '1. Does the file contain closed polyline rectangles for booths?\n'
                '2. Are booth dimensions between 50-5000 sq ft?\n'
                '3. Try uploading a sample DXF file to test the application.'
            )
        elif 'ODAFileConverter' in error_msg or 'No such file' in error_msg:
            error_msg = (
                'DWG conversion failed. The ODA File Converter is not installed.\n\n'
                'Solution:\n'
                '1. Use a DXF file instead (convert in AutoCAD first), OR\n'
                '2. Install ODA File Converter from:\n'
                '   https://www.opendesign.com/guestfiles/oda_file_converter\n'
                '3. Add it to your system PATH'
            )
        elif 'readfile' in error_msg or 'DXF' in error_msg:
            error_msg = (
                'File format error. Please ensure you are uploading a valid DWG or DXF file.\n'
                'Try converting your DWG to DXF in AutoCAD and uploading the DXF file.'
            )

        return jsonify({'error': error_msg}), 500

@app.route('/api/floorplan/<job_id>')
def get_floorplan(job_id):
    """Retrieve processed GeoJSON for a specific job"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    return jsonify(jobs[job_id]['geojson']), 200

@app.route('/api/booth/<job_id>/<booth_id>')
def get_booth_details(job_id, booth_id):
    """Get detailed information for a specific booth"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    geojson = jobs[job_id]['geojson']

    # Find booth in features
    booth = None
    for feature in geojson.get('features', []):
        if feature['properties'].get('booth_id') == booth_id:
            booth = feature
            break

    if not booth:
        return jsonify({'error': 'Booth not found'}), 404

    # Calculate nearby amenities
    amenities = find_nearby_amenities(booth, geojson.get('features', []))

    booth['properties']['nearby_amenities'] = amenities

    return jsonify(booth), 200

@app.route('/api/search/<job_id>', methods=['GET'])
def search_booths(job_id):
    """Search booths by ID or properties"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    query = request.args.get('q', '').lower()
    category = request.args.get('category', '').lower()

    geojson = jobs[job_id]['geojson']
    results = []

    for feature in geojson.get('features', []):
        props = feature['properties']
        booth_id = props.get('booth_id', '').lower()
        feat_category = props.get('category', '').lower()

        match = False
        if query and query in booth_id:
            match = True
        if category and feat_category == category:
            match = True
        if not query and not category:
            match = True

        if match:
            results.append(feature)

    return jsonify({
        'type': 'FeatureCollection',
        'features': results,
        'count': len(results)
    }), 200

@app.route('/api/route/<job_id>', methods=['POST'])
def calculate_path(job_id):
    """Calculate route between two booths"""
    if job_id not in jobs:
        return jsonify({'error': 'Job not found'}), 404

    data = request.get_json()
    from_booth = data.get('from')
    to_booth = data.get('to')

    if not from_booth or not to_booth:
        return jsonify({'error': 'from and to booth IDs required'}), 400

    geojson = jobs[job_id]['geojson']

    # Find both booths
    from_feature = None
    to_feature = None

    for feature in geojson.get('features', []):
        booth_id = feature['properties'].get('booth_id')
        if booth_id == from_booth:
            from_feature = feature
        if booth_id == to_booth:
            to_feature = feature

    if not from_feature or not to_feature:
        return jsonify({'error': 'One or both booths not found'}), 404

    # Calculate route (simplified for POC - direct line between centroids)
    route = calculate_route(from_feature, to_feature)

    return jsonify(route), 200

@app.route('/api/health')
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'ok',
        'message': 'Exhibition Floorplan API is running',
        'version': '1.0.0',
        'processed_jobs': len(jobs)
    }), 200

if __name__ == '__main__':
    print("=" * 60)
    print("Exhibition Floorplan Interactive Mapping Application")
    print("=" * 60)
    print("Starting Flask development server...")
    print("Access the application at: http://localhost:5000")
    print("=" * 60)
    app.run(debug=True, port=5000, use_reloader=False)
