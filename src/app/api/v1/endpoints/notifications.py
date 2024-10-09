from typing import Annotated, Any

from fastapi import APIRouter, Depends
from starlette import status

from app import schemas
from app.dependencies.notifications import CommonParams, get_common_params, get_notification_in
from app.models import Notification
from app.schemas import Paginated

router = APIRouter()


@router.get("", response_model=Paginated[schemas.Notification])
async def get_notifications(
        params: Annotated[CommonParams, Depends(get_common_params)],
        paging: schemas.PaginationParams = Depends(),
        sorting: schemas.SortingParams = Depends(),
) -> dict[str, Any]:
    result = await Notification.get_by_params(params, paging, sorting)

    return {
        "page": paging.page,
        "per_page": paging.per_page,
        "total": len(result),
        "results": result,
    }


@router.post("", response_model=schemas.Notification, status_code=status.HTTP_201_CREATED)
async def create_notification(notification_in: Annotated[Notification, Depends(get_notification_in)]) -> Notification:
    return await Notification.create(notification_in)
