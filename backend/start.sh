#!/bin/sh

#find /opt/app/models -name "*.whl" -exec pip install {} \;

exec uvicorn main:app --host 0.0.0.0 --port $APP_PORT --workers $WORKERS
