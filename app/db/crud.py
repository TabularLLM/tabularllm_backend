from typing import Literal, Union
from sqlalchemy.orm import Session
from app.db.models.models import AnalysisInsight, ChatMessages 
from sqlalchemy.exc import SQLAlchemyError
from datetime import datetime, timezone

async def add_new_insight(db: Session, file_id: str, file_analysis: str, insight_name: str, previous_response_id: str = None):
    try:
        # Create a new AnalysisInsight object
        new_insight = AnalysisInsight(
            file_id=file_id,
            file_analysis=file_analysis,
            insight_name=insight_name,
            previous_response_id=previous_response_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)  # Set the current UTC time
        )

        # Add and commit the new entry
        db.add(new_insight)
        db.commit()
        db.refresh(new_insight)

        return({
            "status": "success",
            "message": "Insight added successfully",
            "insight_id": new_insight.id
        })
    
    except SQLAlchemyError as e:
        db.rollback()  # Roll back transaction in case of an error
        raise e


async def get_insight(db: Session, insight_id: int):
    insight = db.query(AnalysisInsight).filter(AnalysisInsight.id == insight_id).first()
    
    return insight
    
async def update_previous_response_id(db: Session, insight_id: int, previous_response_id: str):
    try:
        # Use setattr to dynamically update the specified column
        insight = db.query(AnalysisInsight).filter(AnalysisInsight.id == insight_id).first()

        if not insight:
            raise f"No insight found with ID {insight_id}."

        insight.previous_response_id = previous_response_id

        db.commit()
        db.refresh(insight)

    except SQLAlchemyError as e:
        db.rollback()  # Roll back if there’s an error
        raise e

async def update_insight_name(db: Session, insight_id: int, new_insight_name: str):
    try:
        # Use setattr to dynamically update the specified column
        insight = db.query(AnalysisInsight).filter(AnalysisInsight.id == insight_id).first()

        if not insight:
            raise f"No insight found with ID {insight_id}."

        insight.insight_name = new_insight_name

        db.commit()
        db.refresh(insight)

    except SQLAlchemyError as e:
        db.rollback()  # Roll back if there’s an error
        raise e

async def delete_insight(db: Session, insight_id: int):
    try:
        # Use setattr to dynamically update the specified column
        insight = db.query(AnalysisInsight).filter(AnalysisInsight.id == insight_id).first()

        if not insight:
            raise f"No insight found with ID {insight_id}."

        db.delete(insight)
        db.commit()

    except SQLAlchemyError as e:
        db.rollback()  # Roll back if there’s an error
        raise e


async def add_new_message(db: Session, message: str, type: Literal["output", "input"], insight_id: int):
    try:
        new_message = ChatMessages(
            message=message,
            type=type,
            insight_id=insight_id,
            created_at=datetime.now(timezone.utc).replace(tzinfo=None)
        )

        db.add(new_message)
        db.commit()
        db.refresh(new_message)

    except SQLAlchemyError as e:
        db.rollback()  # Roll back if there’s an error
        raise e
