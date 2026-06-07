from fastapi import APIRouter, Depends, Response, status
from sqlalchemy.orm import Session

from app.database import get_db
from app.schemas import EventCreate, EventResponse
from app.services.events import ingest_event

router = APIRouter(tags=["events"])


@router.post(
    "/events",
    response_model=EventResponse,
    summary="Ingest a payment lifecycle event",
)
def create_event(
    payload: EventCreate, response: Response, db: Session = Depends(get_db)
) -> EventResponse:
    result = ingest_event(db, payload)
    response.status_code = (
        status.HTTP_200_OK if result.duplicate else status.HTTP_201_CREATED
    )
    return result
