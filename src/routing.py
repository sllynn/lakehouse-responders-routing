import json
from typing import List, Dict, Any
import valhalla
from lakebase_responders_entities import Emergency, Vehicle, UrgencyLevel

class RoutingService:
    """Handles interactions with the Valhalla routing engine to get matrices."""

    COSTING = "auto"
    UNITS = "kilometers"

    def __init__(self, config_path: str):
        """
        Initializes the Valhalla Actor.

        Args:
            config_path: Path to the valhalla.json configuration file.
        """
        print("Initializing Valhalla routing actor...")
        self.actor = valhalla.Actor(config_path)
        print(self.actor.status())

    def _make_locations(self, entities: List) -> List[dict]:
        """Creates the location format required by Valhalla."""
        return [{"lat": e.lat, "lon": e.lon, "type": "break"} for e in entities]

    def get_matrix(self, emergencies: List[Emergency], vehicles: List[Vehicle]) -> Dict[str, Any]:
        """
        Builds and executes a many-to-many matrix request to Valhalla.

        Args:
            emergencies: A list of Emergency objects.
            vehicles: A list of Vehicle objects.

        Returns:
            The matrix result from Valhalla.
        """
        all_entities = emergencies + vehicles
        locations = self._make_locations(all_entities)

        matrix_query = {
            "sources": locations,
            "targets": locations,
            "costing": self.COSTING,
            "directions_options": {"units": self.UNITS},
            "shape_format": "geojson"
        }

        print(f"\nRequesting a {len(locations)}x{len(locations)} matrix from Valhalla...")
        matrix_result = self.actor.matrix(matrix_query)
        print("Matrix received successfully.")

        # Annotate the targets in the result with urgency levels
        for target, entity in zip(matrix_result["targets"], all_entities):
            if isinstance(entity, Emergency):
                target["urgency"] = entity.urgency.name
            else:
                # Assign a default urgency for vehicle locations
                target["urgency"] = UrgencyLevel.medium.name
        
        return matrix_result