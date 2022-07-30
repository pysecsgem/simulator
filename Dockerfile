# define base image
FROM python:3.9-alpine

# expose ports
EXPOSE 4000
EXPOSE 5000

# setup working directory
WORKDIR /srv/secssim

# install required system packages
RUN apk update && apk add alpine-sdk libffi-dev

# install poetry
RUN pip install --no-cache-dir poetry

# copy local data
COPY pyproject.toml .
COPY poetry.lock .
COPY secsgem_simulator ./secsgem_simulator

# install the local python package
RUN poetry install

# remove unneeded packages
RUN apk del alpine-sdk

# the launch command
CMD poetry run secssim run_server --host 0.0.0.0
