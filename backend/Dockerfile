FROM --platform=linux/amd64 python:3.11-alpine

# Setup environment variables
ENV APP_PORT 8000

# Copy code and install dependencies
COPY requirements.txt /opt/app/requirements.txt
WORKDIR /opt/app
RUN pip install --no-cache-dir --upgrade -r requirements.txt
COPY ./gagm-base/dist /opt/gagm-base/
RUN pip install --force-reinstall /opt/gagm-base/gagm_base-0.0.1-py3-none-any.whl
COPY ./app /opt/app/

# Copy start script
COPY start.sh /opt/app/start.sh
RUN chmod +x /opt/app/start.sh
# COPY ./models/dist /opt/app/models

# Mount volume for ./models
# TODO: remove this if the wheel file task is done
# VOLUME ./app/models /opt/app/models

# Expose the backend port and setup healthcheck
EXPOSE ${APP_PORT}
RUN apk --no-cache add curl
HEALTHCHECK --interval=1m --timeout=10s --start-period=10s --retries=3 CMD curl --fail http://localhost:${APP_PORT}/healthcheck || exit 1

# CMD ["/opt/app/start.sh"]
ENTRYPOINT ["/opt/app/start.sh"]
