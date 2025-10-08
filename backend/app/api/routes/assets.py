from fastapi import APIRouter, status
from fastapi.responses import PlainTextResponse

router = APIRouter()

@router.get("")
def farm_data_test():
    return PlainTextResponse("Farm Data", status.HTTP_200_OK)
