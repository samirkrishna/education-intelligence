
from sqlalchemy import inspect, text
from app.database.connection import engine

new_columns = {
    "academic_cycle": "VARCHAR(30)",
    "applicant_type": "VARCHAR(50)",
    "deadline": "VARCHAR(50)",
    "amount": "VARCHAR(100)",
    "change_type": "VARCHAR(50) DEFAULT 'NEW_INFORMATION'",
    "verification_status": "VARCHAR(30) DEFAULT 'UNVERIFIED'"
}

inspector = inspect(engine)

existing_columns = {
    column["name"]
    for column in inspector.get_columns("education_updates")
}

with engine.begin() as connection:
    for column_name, column_type in new_columns.items():

        if column_name not in existing_columns:
            connection.execute(
                text(
                    f"ALTER TABLE education_updates "
                    f"ADD COLUMN {column_name} {column_type}"
                )
            )

            print(f"Added column: {column_name}")
        else:
            print(f"Already exists: {column_name}")

print("EducationUpdate schema migration completed.")
