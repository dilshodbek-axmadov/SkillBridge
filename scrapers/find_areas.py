"""
Helper script to find correct area IDs for Uzbekistan
"""
import requests
from .config import HH_API_BASE_URL, USER_AGENT, HH_HOST

def get_areas():
    """Fetch all areas from hh.uz API"""
    url = f"{HH_API_BASE_URL}/areas"
    headers = {
        'User-Agent': USER_AGENT,
        'HH-User-Agent': USER_AGENT,
    }
    params = {'host': HH_HOST}
    
    response = requests.get(url, headers=headers, params=params)
    return response.json()

def find_uzbekistan_areas(areas, parent_name=""):
    """Recursively search for Uzbekistan-related areas"""
    uzbek_areas = []
    
    for area in areas:
        name = area.get('name', '')
        area_id = area.get('id', '')
        
        # Check if this is Uzbekistan or Uzbek city
        if any(keyword in name.lower() for keyword in ['узбекистан', 'uzbekistan', 'ташкент', 'tashkent', 'самарканд', 'бухара']):
            uzbek_areas.append({
                'id': area_id,
                'name': name,
                'parent': parent_name
            })
            print(f"Found: ID={area_id}, Name={name}, Parent={parent_name}")
        
        # Recursively check sub-areas
        if 'areas' in area and area['areas']:
            uzbek_areas.extend(find_uzbekistan_areas(area['areas'], name))
    
    return uzbek_areas

if __name__ == '__main__':
    print("Fetching areas from hh.uz API...\n")
    areas = get_areas()
    
    print("Searching for Uzbekistan-related areas...\n")
    uzbek_areas = find_uzbekistan_areas(areas)
    
    print("\n" + "="*60)
    print("UZBEKISTAN AREAS FOUND:")
    print("="*60)
    for area in uzbek_areas:
        print(f"ID: {area['id']:<10} Name: {area['name']:<30} Parent: {area['parent']}")