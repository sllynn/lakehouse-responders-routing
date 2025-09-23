from typing import List, Tuple, Dict, Any
from sqlmodel import create_engine, Session, select, delete, SQLModel
from lakebase_responders_entities import Emergency, Vehicle, Plan

class DataManager:
    """Handles all database operations for the emergency response simulation."""

    def __init__(self, db_url: str):
        """
        Initializes the DataManager with a database connection URL.

        Args:
            db_url: The connection string for the database.
        """
        self.engine = create_engine(db_url)
        SQLModel.metadata.create_all(self.engine)
        self.session = Session(self.engine)

    def get_entities(self) -> Tuple[List[Emergency], List[Vehicle]]:
        """
        Fetches all current emergencies and vehicles from the database.

        Returns:
            A tuple containing a list of Emergency objects and a list of Vehicle objects.
        """
        print("Fetching emergencies and vehicles from the database...")
        emergencies = self.session.exec(select(Emergency)).all()
        vehicles = self.session.exec(select(Vehicle)).all()
        print(f"Found {len(emergencies)} emergencies and {len(vehicles)} vehicles.")
        return emergencies, vehicles

    def update_state_in_transaction(
        self,
        plans_to_save: List[Plan],
        completed_emergency_ids: List[int],
        vehicle_updates: List[Dict[str, Any]]
    ):
        """
        Updates the database state in a single atomic transaction.

        Args:
            plans_to_save: A list of new Plan objects to be saved.
            completed_emergency_ids: A list of IDs for emergencies that have been resolved.
            vehicle_updates: A list of dictionaries with vehicle ID, new lon, and new lat.
        """
        print("\nUpdating simulation state within a single database transaction...")
        try:
            # Stage 1: Delete all old plans.
            self.session.exec(delete(Plan))
            print("  - Staged: Deletion of old plans.")

            # Stage 2: Add all new plans to the session.
            self.session.add_all(plans_to_save)
            print(f"  - Staged: {len(plans_to_save)} new plans to be saved.")

            # Stage 3: Delete completed emergencies.
            if completed_emergency_ids:
                statement = delete(Emergency).where(Emergency.id.in_(completed_emergency_ids))
                self.session.exec(statement)
                print(f"  - Staged: {len(completed_emergency_ids)} emergencies to be removed.")
            
            # **CRITICAL FIX**: Explicitly update vehicle locations within the transaction.
            if vehicle_updates:
                print(f"  - Staging updates for {len(vehicle_updates)} vehicles...")
                for update in vehicle_updates:
                    # Fetch the vehicle by its ID within the current session
                    vehicle_to_update = self.session.get(Vehicle, update["id"])
                    if vehicle_to_update:
                        vehicle_to_update.lon = update["lon"]
                        vehicle_to_update.lat = update["lat"]

            # Commit Stage: All staged changes are written to the DB at once.
            self.session.commit()
            print("Transaction successful. All changes have been committed.")

        except Exception as e:
            print(f"ERROR: Database transaction failed. Rolling back all changes. Details: {e}")
            self.session.rollback()
            raise

    def close(self):
        """Closes the database session and disposes of the engine."""
        print("Closing database connection.")
        self.session.close()
        self.engine.dispose()

