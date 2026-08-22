from app.database.core import SessionLocal, init_db
from app.database import repositories, models
import logging

logger = logging.getLogger(__name__)

def seed_data():
    init_db()
    db = SessionLocal()
    try:
        user = repositories.get_user_by_username(db, "demo_user")
        if user:
            logger.info("Demo user already exists, skipping seed.")
            return

        user = repositories.create_user(db, "demo_user")
        
        mission = repositories.create_mission(
            db, 
            user.id, 
            "Book Seminar Hall", 
            "Friday ko seminar hall chahiye. Try to get it for 4000. 5000 se upar mat jaana. Projector mandatory hai."
        )
        
        # Hard Private Constraint (Never reveal max budget)
        repositories.create_constraint(
            db, mission.id, "price", "<=", "5000", 
            models.VisibilityEnum.PRIVATE, models.ConstraintTypeEnum.HARD
        )
        
        # Soft Private Constraint (Target price)
        repositories.create_constraint(
            db, mission.id, "target_price", "<=", "4000", 
            models.VisibilityEnum.PRIVATE, models.ConstraintTypeEnum.SOFT
        )
        
        # Hard Shared Constraint (Must have projector)
        repositories.create_constraint(
            db, mission.id, "amenities", "contains", "projector", 
            models.VisibilityEnum.SHARED, models.ConstraintTypeEnum.HARD
        )

        repositories.log_audit_event(db, "MISSION_CREATED", f"Mission {mission.id} seeded.")
        logger.info("Seed data inserted successfully.")
    finally:
        db.close()

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    seed_data()
