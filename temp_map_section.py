# Clean map selection implementation
with col1:
    st.subheader("🗺️ Select Your Area")
    
    # Add search functionality
    col_search, col_layer = st.columns([2, 1])
    with col_search:
        location_search = st.text_input("🔍 Search for locations:", placeholder="e.g., Costa Rica, Amazon Rainforest, Great Barrier Reef", key="location_search")
    with col_layer:
        layer_type = st.radio("🗺️ Map Style:", ["Light Map", "Satellite"], horizontal=True, key="map_layer_selector")
    
    st.info("💡 Search for a location above, then use the drawing tools to select your analysis area")
    
    # Handle location search and set map center
    map_center = [40.0, -100.0]  # Default center (USA)
    map_zoom = 4  # Default zoom
    
    if location_search:
        try:
            from geopy.geocoders import Nominatim
            geolocator = Nominatim(user_agent="EcosystemValuationEngine")
            location = geolocator.geocode(location_search)
            if location:
                map_center = [location.latitude, location.longitude]
                map_zoom = 10  # Zoom closer to found location
                st.success(f"📍 Found: {location.address}")
            else:
                st.warning(f"❌ Location '{location_search}' not found. Try different search terms.")
        except Exception as e:
            st.error("⚠️ Search service temporarily unavailable. Please try again.")
    
    # Create interactive map based on selected layer
    if layer_type == "Satellite":
        m = folium.Map(
            location=map_center, 
            zoom_start=map_zoom,
            tiles='https://mt1.google.com/vt/lyrs=s&x={x}&y={y}&z={z}',
            attr='&copy; Google'
        )
    else:  # Light Map
        m = folium.Map(
            location=map_center, 
            zoom_start=map_zoom,
            tiles='https://cartodb-basemaps-{s}.global.ssl.fastly.net/light_all/{z}/{x}/{y}.png',
            attr='&copy; CARTO'
        )
    
    # Add search result marker if location found
    if location_search and 'location' in locals() and location:
        folium.Marker(
            [location.latitude, location.longitude],
            popup=f"📍 {location.address}",
            tooltip=f"Searched: {location_search}",
            icon=folium.Icon(color='red', icon='search')
        ).add_to(m)
    
    # Add existing selection if available
    if st.session_state.selected_area and st.session_state.area_coordinates:
        coords = st.session_state.area_coordinates
        folium.Polygon(
            locations=[(coord[1], coord[0]) for coord in coords],
            color='green',
            weight=3,
            fillColor='green',
            fillOpacity=0.2,
            popup="Selected Area"
        ).add_to(m)

    # Add drawing tools
    from folium.plugins import Draw
    draw = Draw(
        draw_options={
            'polyline': False,
            'polygon': True,
            'circle': False,
            'rectangle': True,
            'marker': False,
            'circlemarker': False,
        },
        edit_options={
            'remove': True,
            'edit': False
        }
    )
    draw.add_to(m)
    
    # Display map with drawing capability
    map_data = st_folium(
        m, 
        width=700, 
        height=400,
        returned_objects=["all_drawings"],
        key="area_map"
    )
    
    # Process map interactions
    if map_data['all_drawings'] and len(map_data['all_drawings']) > 0:
        latest_drawing = map_data['all_drawings'][-1]
        
        if latest_drawing['geometry']['type'] in ['Polygon', 'Rectangle']:
            coordinates = latest_drawing['geometry']['coordinates'][0]
            
            # Check if this is a new selection
            current_coords = st.session_state.get('area_coordinates', [])
            is_new_selection = (not current_coords or coordinates != current_coords)
            
            if is_new_selection:
                # Save the new selection
                st.session_state.selected_area = {
                    'type': latest_drawing['geometry']['type'],
                    'coordinates': coordinates
                }
                st.session_state.area_coordinates = coordinates
                st.session_state.analysis_results = None
                
                # Calculate and show area
                area_coords = np.array(coordinates)
                if len(area_coords) > 2:
                    area_km2 = abs(np.sum((area_coords[:-1, 0] * area_coords[1:, 1]) - (area_coords[1:, 0] * area_coords[:-1, 1]))) * 111.32 * 111.32 / 2
                    area_ha = area_km2 * 100
                    st.success(f"Area selected: {area_ha:.1f} hectares")
                st.rerun()
        else:
            st.warning("Please draw a polygon or rectangle area")
    
    # Display coordinates of selected area
    if st.session_state.get('selected_area') and st.session_state.get('area_coordinates'):
        st.markdown("### 📍 Selected Area Coordinates")
        coords = st.session_state.area_coordinates
        
        # Calculate bounding box
        lats = [coord[1] for coord in coords[:-1]]  # Exclude last duplicate point
        lons = [coord[0] for coord in coords[:-1]]
        
        col_bounds1, col_bounds2 = st.columns(2)
        with col_bounds1:
            st.markdown(f'<p style="font-size:16px; margin:2px 0;"><strong>Min Latitude:</strong> {min(lats):.6f}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:16px; margin:2px 0;"><strong>Min Longitude:</strong> {min(lons):.6f}</p>', unsafe_allow_html=True)
        with col_bounds2:
            st.markdown(f'<p style="font-size:16px; margin:2px 0;"><strong>Max Latitude:</strong> {max(lats):.6f}</p>', unsafe_allow_html=True)
            st.markdown(f'<p style="font-size:16px; margin:2px 0;"><strong>Max Longitude:</strong> {max(lons):.6f}</p>', unsafe_allow_html=True)
        
        # Show all coordinates in expandable section
        with st.expander("All Coordinates"):
            for i, coord in enumerate(coords[:-1]):  # Exclude last duplicate
                st.write(f"Point {i+1}: {coord[1]:.6f}°N, {coord[0]:.6f}°E")