from typing import Dict, Any, List
from datetime import datetime, timedelta
from ortools.constraint_solver import routing_enums_pb2, pywrapcp

class RouteOptimizer:
    """Vehicle routing optimizer using OR-Tools."""
    
    def __init__(self, data: Dict[str, Any], num_vehicles, goal):
        """
        Initialize the optimizer with input data.
        
        Args:
            data: Dictionary containing sources_to_targets, sources, targets, etc.
            num_vehicles: The number of vehicles to use.
            goal: The optimization objective, e.g., "time" or "distance".
        """
        self.data = data
        self.distance_matrix = []
        self.time_matrix = []
        self.goal = goal
        self.num_locations = len(data['sources'])
        self.num_vehicles = num_vehicles
        
        self.urgency_levels = {i: source.get('urgency', 'medium') 
                               for i, source in enumerate(data['targets'])}
        
        self.vehicle_starts = list(range(self.num_locations - self.num_vehicles, self.num_locations))
        self.vehicle_ends = []  # Will be set in _parse_matrices
        self.matrix_size = 0    # Will be set in _parse_matrices
        
        self._parse_matrices()
    
    def _parse_matrices(self):
        """Parse the sources_to_targets data into distance and time matrices."""
        # Add virtual end depots to allow vehicles to end anywhere
        self.matrix_size = self.num_locations + self.num_vehicles
        
        self.distance_matrix = [[0] * self.matrix_size for _ in range(self.matrix_size)]
        self.time_matrix = [[0] * self.matrix_size for _ in range(self.matrix_size)]
        
        sources_to_targets = self.data['sources_to_targets']
        for source_routes in sources_to_targets:
            for route in source_routes:
                from_idx = route['from_index']
                to_idx = route['to_index']
                self.distance_matrix[from_idx][to_idx] = route.get('distance', 0)
                self.time_matrix[from_idx][to_idx] = route.get('time', 0)
        
        virtual_end_depots = list(range(self.num_locations, self.matrix_size))
        for i in range(self.num_locations):
            for virtual_depot in virtual_end_depots:
                self.distance_matrix[i][virtual_depot] = 0
                self.time_matrix[i][virtual_depot] = 0

        self.vehicle_ends = virtual_end_depots
        print(f"Matrix size set to: {self.matrix_size}x{self.matrix_size}")
        print(f"Vehicle starts: {self.vehicle_starts}, Vehicle ends: {self.vehicle_ends}")

    def _distance_callback(self, from_index: int, to_index: int) -> int:
        """Returns the distance between two nodes, scaled for the solver."""
        return int(self.distance_matrix[from_index][to_index] * 100)
    
    def _time_callback(self, from_index: int, to_index: int) -> int:
        """Returns the travel time between two nodes."""
        return int(self.time_matrix[from_index][to_index])
    
    def get_urgency_level(self, location_index: int) -> str:
        """Returns the urgency level for a given location index."""
        return self.urgency_levels.get(location_index, 'medium')
    
    def solve(self, time_limit_seconds=10):
        """
        Solve the Vehicle Routing Problem.
        
        Args:
            time_limit_seconds: The maximum time to let the solver run.

        Returns:
            A list of vehicle route dictionaries or an error dictionary.
        """
        manager = pywrapcp.RoutingIndexManager(
            self.matrix_size, self.num_vehicles, self.vehicle_starts, self.vehicle_ends
        )
        routing = pywrapcp.RoutingModel(manager)
        
        def transit_callback(from_index, to_index):
            from_node = manager.IndexToNode(from_index)
            to_node = manager.IndexToNode(to_index)
            return self._time_callback(from_node, to_node) if self.goal == "time" else self._distance_callback(from_node, to_node)

        transit_callback_index = routing.RegisterTransitCallback(transit_callback)
        routing.SetArcCostEvaluatorOfAllVehicles(transit_callback_index)

        # --- URGENCY PENALTY LOGIC REINSTATED ---
        def weighted_position_callback(from_index, to_index):
            """Penalizes visiting low-priority stops earlier in a route."""
            to_node = manager.IndexToNode(to_index)
            if to_node < self.num_locations:
                urgency = self.get_urgency_level(to_node)
                if urgency == "high": return 1
                if urgency == "medium": return 2
                return 3 # Low urgency increments position counter faster
            return 1 # Default for virtual depots

        position_callback_index = routing.RegisterTransitCallback(weighted_position_callback)

        dimension_name = 'Time' if self.goal == "time" else 'Distance'
        routing.AddDimension(
            transit_callback_index, 0, 10000, True, dimension_name
        )

        position_dimension_name = 'Position'
        routing.AddDimension(
            position_callback_index, 0, 30, True, position_dimension_name
        )
        position_dimension = routing.GetDimensionOrDie(position_dimension_name)

        for loc_id in range(self.num_locations):
            if loc_id in self.vehicle_starts:
                continue
            index = manager.NodeToIndex(loc_id)
            urgency = self.get_urgency_level(loc_id)
            if urgency == "high":
                # High penalty if not visited in position 1 (first stop)
                position_dimension.SetCumulVarSoftUpperBound(index, 1, 50000)
            elif urgency == "medium":
                # Medium penalty if not visited by position 2
                position_dimension.SetCumulVarSoftUpperBound(index, 2, 10000)
        # --- END OF URGENCY LOGIC ---

        search_parameters = pywrapcp.DefaultRoutingSearchParameters()
        search_parameters.first_solution_strategy = (
            routing_enums_pb2.FirstSolutionStrategy.PATH_CHEAPEST_ARC)
        search_parameters.local_search_metaheuristic = (
            routing_enums_pb2.LocalSearchMetaheuristic.GUIDED_LOCAL_SEARCH)
        search_parameters.time_limit.FromSeconds(time_limit_seconds)
        # search_parameters.log_search = True
        
        print(f"Solving VRP (time limit: {time_limit_seconds}s)...")
        solution = routing.SolveWithParameters(search_parameters)
        
        if solution:
            print("Solver found a solution.")
            return self._format_solution(manager, routing, solution)
        else:
            status_map = {0: "NOT_SOLVED", 1: "SUCCESS", 2: "FAIL", 3: "FAIL_TIMEOUT", 4: "INVALID"}
            error_msg = f"No solution found. Status: {status_map.get(routing.status(), 'UNKNOWN')}"
            print(error_msg)
            return {"error": error_msg}
    
    def _format_solution(self, manager, routing, solution) -> List[Dict[str, Any]]:
        """Formats the raw solver solution into a more usable structure."""
        vehicle_routes = []
        for vehicle_id in range(self.num_vehicles):
            index = routing.Start(vehicle_id)
            route_nodes = []
            while not routing.IsEnd(index):
                node_index = manager.IndexToNode(index)
                if node_index < self.num_locations: # Exclude virtual depots
                    route_nodes.append(node_index)
                index = solution.Value(routing.NextVar(index))
            
            # --- ETA CALCULATION LOGIC CORRECTED ---
            route_time = 0
            route_distance = 0
            etas = []
            # Start from the first segment to calculate ETA for the second stop onwards
            for i in range(len(route_nodes) - 1):
                from_node = route_nodes[i]
                to_node = route_nodes[i+1]
                
                # Use the original time and distance from our matrices
                route_time += self.time_matrix[from_node][to_node]
                route_distance += self.distance_matrix[from_node][to_node]
                
                # Append the ETA for the destination of this segment
                etas.append(datetime.now() + timedelta(seconds=route_time))

            vehicle_routes.append({
                "vehicle_id": vehicle_id, 
                "stops": route_nodes,
                "etas": etas
            })
        
        return vehicle_routes

