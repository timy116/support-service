## Table of Contents

- [Introduction](#introduction)
- [Features](#features)
- [Requirements](#requirements)
- [Configure environment variables](#configure-environment-variables)
  - [FastAPI Application](#fastapi-application)
  - [Logging](#logging)
  - [MongoDB](#mongodb)
  - [Redis](#redis)


## Introduction

This project is an internal service for other services to use.
It is a simple service that provides a REST API or some features to other services. 
The service is built using Python(3.11) and [FastAPI](https://github.com/fastapi/fastapi) framework.
It uses the open source [MongoDB](https://www.mongodb.com/) database for storing data.

## Features

- Dockerized service for easy deployment.
- Fully async and non-blocking.
- Uses [FastAPI](https://github.com/fastapi/fastapi) framework for API development.
- Uses [MongoDB](https://www.mongodb.com/) as data store for daily reports and notification messages.
- Uses [Redis](https://redis.io/) for caching.
- Extensible architecture for adding new API endpoints and services.
- Descriptive and well-documented code.
- Auto send notification by [LINE Notify](https://notify-bot.line.me/) when some event is triggered.

## Requirements

Manual installation:
- Python 3.11 or higher
- Pip for dependency management
- Up and running MongoDB instance(local or remote)

Docker installation:
- [Docker](https://github.com/docker/)
- [Docker Compose](https://github.com/docker/compose)

## Configure environment variables

You can see the table of all environment variables below. Those marked with `*` are required and **MUST** be set before
running the application. Rest of them are optional and have default values.

**Note:** To set any of these environment variables below, you **MUST** set them
in your shell or in a `.env` file placed at the root directory (e.g. you can copy `.env.example` to `.env`).

Also note that **ALL** environment variables are **CASE SENSITIVE**.

### FastAPI Application

| Name                 | Description                                |             Default             |        Type        |
|----------------------|:-------------------------------------------|:-------------------------------:|:------------------:|
| `PROJECT_VERSION`    | Project version.                           | Current version of the project. |      `string`      |
| `API_V1_STR`         | API version 1 prefix.                      |              `v1`               |      `string`      |
| `DEBUG`              | Debug mode for development.                |             `True`              |     `boolean`      |
| `UVICORN_HOST`*      | Host address for uvicorn server.           |               `-`               |      `string`      |
| `UVICORN_PORT`*      | Port number for uvicorn server.            |               `-`               |     `integer`      |


### Logging

| Name        | Description                                                                                | Default |   Type   |
|-------------|:-------------------------------------------------------------------------------------------|:-------:|:--------:|
| `LOG_LEVEL` | A logging level from the [logging](https://docs.python.org/3/library/logging.html) module. | `INFO`  | `string` |


#### MongoDB

| Name              | Description             | Default |   Type   |
|-------------------|:------------------------|:-------:|:--------:|
| `MONGODB_URI`     | MongoDB connection URI. |   `-`   | `string` |
| `MONGODB_DB_NAME` | MongoDB database name.  |   `-`   | `string` |


#### Redis

| Name        | Description           | Default |   Type   |
|-------------|:----------------------|:-------:|:--------:|
| `REDIS_URI` | Redis connection URI. |   `-`   | `string` |
