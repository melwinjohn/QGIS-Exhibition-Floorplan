import math
from shapely.geometry import Point, LineString

try:
    import networkx as nx
except ImportError:
    print("Warning: networkx not installed. Run: pip install networkx")


def get_polygon_centroid(feature):
    """Extract centroid from GeoJSON polygon feature"""
    try:
        coords = feature['geometry']['coordinates'][0]
        # Calculate centroid manually
        x = sum(c[0] for c in coords) / len(coords)
        y = sum(c[1] for c in coords) / len(coords)
        return (x, y)
    except:
        return None


def calculate_distance(point1, point2):
    """Calculate Euclidean distance between two points"""
    try:
        dx = point1[0] - point2[0]
        dy = point1[1] - point2[1]
        return math.sqrt(dx*dx + dy*dy)
    except:
        return float('inf')


def find_nearby_amenities(booth_feature, all_features, max_distance=200):
    """
    Find amenities (other booths) within max_distance of a booth

    Returns:
        List of nearby booths with distances
    """
    try:
        booth_centroid = get_polygon_centroid(booth_feature)
        if not booth_centroid:
            return []

        nearby = []

        for feature in all_features:
            if feature['properties'].get('booth_id') == booth_feature['properties'].get('booth_id'):
                continue  # Skip the booth itself

            other_centroid = get_polygon_centroid(feature)
            if not other_centroid:
                continue

            distance = calculate_distance(booth_centroid, other_centroid)

            if distance <= max_distance:
                nearby.append({
                    'booth_id': feature['properties'].get('booth_id'),
                    'distance': round(distance, 2),
                    'occupancy_percentage': feature['properties'].get('occupancy_percentage'),
                    'coordinates': other_centroid
                })

        # Sort by distance
        nearby.sort(key=lambda x: x['distance'])
        return nearby[:10]  # Return top 10 closest booths

    except Exception as e:
        print(f"Error finding nearby amenities: {e}")
        return []


def calculate_route(from_feature, to_feature):
    """
    Calculate route between two booths

    For POC: Simplified routing using straight line between centroids
    with distance calculation
    """
    try:
        from_centroid = get_polygon_centroid(from_feature)
        to_centroid = get_polygon_centroid(to_feature)

        if not from_centroid or not to_centroid:
            return {
                'error': 'Could not calculate route',
                'geometry': None,
                'directions': [],
                'total_distance': 0
            }

        # Calculate distance
        total_distance = calculate_distance(from_centroid, to_centroid)

        # Create simple route (straight line for POC)
        route_geometry = {
            'type': 'LineString',
            'coordinates': [from_centroid, to_centroid]
        }

        # Generate simple directions
        directions = [
            {
                'instruction': f"Start at booth {from_feature['properties'].get('booth_id')}",
                'distance': 0
            },
            {
                'instruction': f"Travel {round(total_distance, 1)} units",
                'distance': round(total_distance / 2, 1)
            },
            {
                'instruction': f"Arrive at booth {to_feature['properties'].get('booth_id')}",
                'distance': total_distance
            }
        ]

        return {
            'type': 'Feature',
            'geometry': route_geometry,
            'properties': {
                'from_booth': from_feature['properties'].get('booth_id'),
                'to_booth': to_feature['properties'].get('booth_id'),
                'total_distance': round(total_distance, 2),
                'directions': directions
            }
        }

    except Exception as e:
        print(f"Error calculating route: {e}")
        return {
            'error': str(e),
            'geometry': None,
            'directions': [],
            'total_distance': 0
        }


def cluster_booths_by_occupancy(features):
    """
    Group booths by occupancy level for visualization

    Returns:
        Dict mapping occupancy level to list of booths
    """
    try:
        clusters = {
            'low': [],      # 0-60%
            'medium': [],   # 60-80%
            'high': []      # 80-100%
        }

        for feature in features:
            occ_pct = feature['properties'].get('occupancy_percentage', 0)

            if occ_pct < 60:
                clusters['low'].append(feature)
            elif occ_pct < 80:
                clusters['medium'].append(feature)
            else:
                clusters['high'].append(feature)

        return clusters

    except Exception as e:
        print(f"Error clustering booths: {e}")
        return {'low': [], 'medium': [], 'high': []}


def calculate_booth_capacity_summary(features):
    """
    Calculate overall capacity statistics for floorplan

    Returns:
        Dict with capacity stats
    """
    try:
        if not features:
            return {
                'total_booths': 0,
                'total_max_capacity': 0,
                'total_current_occupancy': 0,
                'overall_occupancy_percentage': 0
            }

        total_max = 0
        total_current = 0

        for feature in features:
            props = feature['properties']
            total_max += props.get('max_occupancy', 0)
            total_current += props.get('current_occupancy', 0)

        overall_pct = (total_current / total_max * 100) if total_max > 0 else 0

        return {
            'total_booths': len(features),
            'total_max_capacity': total_max,
            'total_current_occupancy': total_current,
            'overall_occupancy_percentage': round(overall_pct, 1)
        }

    except Exception as e:
        print(f"Error calculating capacity summary: {e}")
        return {
            'total_booths': 0,
            'total_max_capacity': 0,
            'total_current_occupancy': 0,
            'overall_occupancy_percentage': 0
        }


def search_booths(features, query, category=None):
    """
    Search booths by ID or properties

    Returns:
        List of matching features
    """
    try:
        results = []
        query_lower = query.lower() if query else ''
        category_lower = category.lower() if category else ''

        for feature in features:
            props = feature['properties']
            booth_id = props.get('booth_id', '').lower()
            booth_category = props.get('category', '').lower()

            match = False

            if query_lower and query_lower in booth_id:
                match = True

            if category_lower and booth_category == category_lower:
                match = True

            if not query_lower and not category_lower:
                match = True

            if match:
                results.append(feature)

        return results

    except Exception as e:
        print(f"Error searching booths: {e}")
        return []
