import json
from io import StringIO
from typing import List, Tuple, Dict, Any

import geopandas as gpd
from shapely.geometry import LineString, Point
from lakebase_responders_entities import Plan, Vehicle, Emergency


UTM_CRS_EPSG = 25833


class PlanProcessor:
    """
    Processes the solution from the RouteOptimizer to generate database-ready plans
    and calculate vehicle state updates for the next simulation tick.
    """

    def _remove_first_point(self, geom: LineString) -> LineString:
        """Removes the first coordinate from a LineString, effectively trimming the start."""
        if isinstance(geom, LineString) and len(geom.coords) > 2:
            return LineString(geom.coords[1:])
        return geom

    def _get_next_waypoint(self, geom: LineString, distance_resolution: int):
        """Gets the second coordinate of a LineString, representing the next step."""
        if isinstance(geom, LineString) and len(geom.coords) > 1:
            current_location = gpd.GeoSeries([Point(geom.coords[0])], crs=f"EPSG:{UTM_CRS_EPSG}")
            for c in geom.coords[1:]:
                new_location = gpd.GeoSeries([Point(c)], crs=f"EPSG:{UTM_CRS_EPSG}")
                if current_location.distance(new_location).iloc[0] > distance_resolution:
                    return new_location

            return new_location #Point(geom.coords[1])
        # Return an empty point as a safe fallback
        return gpd.GeoSeries([Point()], crs=f"EPSG:{UTM_CRS_EPSG}")

    def _is_emergency_completed(self, vehicle_pos: Point, emergency: Emergency, threshold_meters=50) -> bool:
        """
        Checks if a vehicle is within a given distance of an emergency,
        considering it "completed".
        """
        # A suitable UTM zone for Berlin to get accurate meter-based distances
         
        if not isinstance(vehicle_pos, Point) or vehicle_pos.is_empty:
            return False
            
        v_location = gpd.GeoSeries([vehicle_pos], crs=f"EPSG:{UTM_CRS_EPSG}")
        e_location = gpd.GeoSeries([Point(emergency.lon, emergency.lat)], crs="EPSG:4326").to_crs(f"EPSG:{UTM_CRS_EPSG}")
        
        distance = v_location.distance(e_location).iloc[0]
        
        return distance < threshold_meters / 2

    def process_solution(
        self, 
        solution: List[Dict[str, Any]], 
        vehicles: List[Vehicle], 
        emergencies: List[Emergency], 
        matrix_result: Dict[str, Any],
        distance_resolution: int
    ) -> Tuple[List[Plan], List[int], List[Dict[str, Any]]]:
        """
        Takes the optimizer solution and generates Plan objects, a list of completed emergencies,
        and a list of vehicle location updates.

        Args:
            solution: The list of routes from optimizer.solve().
            vehicles: The list of Vehicle objects from the database.
            emergencies: The list of Emergency objects from the database.
            matrix_result: The raw matrix from Valhalla, used for route shapes.

        Returns:
            A tuple containing (plans_to_save, completed_emergency_ids, vehicle_updates).
        """
        plans_to_save = []
        completed_emergency_ids = []
        vehicle_updates = []
        num_emergencies = len(emergencies)

        for route_info in solution:
            stops = route_info['stops']
            
            vehicle_start_node_idx = stops[0]
            vehicle_list_idx = vehicle_start_node_idx - num_emergencies
            
            if not (0 <= vehicle_list_idx < len(vehicles)):
                print(f"Warning: Invalid vehicle index {vehicle_list_idx}. Skipping route.")
                continue
            
            vehicle = vehicles[vehicle_list_idx]
            
            if len(stops) > 1:
                first_destination_idx = stops[1]
                route_details = matrix_result["sources_to_targets"][vehicle_start_node_idx][first_destination_idx]
                distance_to_next = route_details.get('distance', 0)
                print(f"Vehicle ID {vehicle.id} assigned route. Next stop node {first_destination_idx}, distance: {distance_to_next:.2f} km.")

                route_geojson = json.dumps(route_details["shape"])
                route_gps = gpd.GeoSeries.from_file(StringIO(route_geojson), driver='GeoJSON')
                route_gps.set_crs("EPSG:4326")
                try:
                    route_gps_segmented = route_gps.to_crs(UTM_CRS_EPSG).simplify(distance_resolution / 1000).segmentize(distance_resolution / 10)
                except Exception:
                    route_gps_segmented = route_gps.to_crs(UTM_CRS_EPSG)
                

                next_waypoint_gps = self._get_next_waypoint(route_gps_segmented.iloc[0], distance_resolution)
                next_waypoint_WGS84 = next_waypoint_gps.to_crs("EPSG:4326").iloc[0]

                if next_waypoint_WGS84 and not next_waypoint_WGS84.is_empty:
                    vehicle_updates.append({
                        "id": vehicle.id,
                        "lon": next_waypoint_WGS84.x,
                        "lat": next_waypoint_WGS84.y
                    })
                
                updated_route_gps = route_gps_segmented.apply(self._remove_first_point)

                for i in range(1, len(stops)):
                    from_node_idx, to_node_idx = stops[i-1], stops[i]
                    
                    if to_node_idx >= num_emergencies: continue 

                    emergency = emergencies[to_node_idx]
                    eta = route_info['etas'][i-1]
                    
                    if i == 1 and self._is_emergency_completed(next_waypoint_gps.iloc[0], emergency, distance_resolution):
                        if emergency.id not in completed_emergency_ids:
                            completed_emergency_ids.append(emergency.id)
                        continue
                    
                    route_wkb = (updated_route_gps.to_crs(f"EPSG:4326").to_wkb()[0] if i == 1 
                                 else gpd.GeoSeries.from_file(StringIO(json.dumps(matrix_result["sources_to_targets"][from_node_idx][to_node_idx]["shape"])), driver='GeoJSON').to_wkb()[0])

                    plans_to_save.append(Plan(
                        vehicle_id=vehicle.id, plan_index=i,
                        emergency_id=emergency.id, route=route_wkb, eta=eta
                    ))
            else:
                print(f"Vehicle ID {vehicle.id} has no tasks. Position remains unchanged.")

        return plans_to_save, completed_emergency_ids, vehicle_updates