from fastapi import Request, status
from fastapi.responses import ORJSONResponse


class RequiredRequestIdMiddleware:
    """Middleware for rejecting requests without X-Request-Id header

    Required to guarantee request ID transmission when telemetry is enabled
    """

    async def __call__(self, request: Request, call_next, *args, **kwargs):
        response = await call_next(request)
        print(f"{request.headers=}")
        request_id = request.headers.get("X-Request-Id")
        if not request_id:
            return ORJSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"detail": "X-Request-Id is required"},
            )
        return response


required_request_id = RequiredRequestIdMiddleware()
