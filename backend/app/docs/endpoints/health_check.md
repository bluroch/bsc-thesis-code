## Perform a Health Check

Endpoint to perform a healthcheck on. This endpoint can primarily be used Docker
to ensure a robust container orchestration and management is in place. Other
services which rely on proper functioning of the API service will not deploy if this
endpoint returns any other HTTP status code except 200 (OK).
