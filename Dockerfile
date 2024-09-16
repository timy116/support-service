FROM python:3.10

# python envs
ENV PYTHONFAULTHANDLER=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONWARNINGS=ignore \
    PYTHONHASHSEED=random \
    PIP_NO_CACHE_DIR=off \
    PIP_DISABLE_PIP_VERSION_CHECK=on \
    PIP_DEFAULT_TIMEOUT=100 \
    STATIC_DIR=app/static

RUN apt-get update \
    && apt-get install -y gettext libgettextpo-dev tesseract-ocr \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /code

COPY src/requirements/requirements.txt /code/requirements/

RUN pip install -r requirements/requirements.txt

ADD . .
RUN chown -R root:root .
USER root

CMD ["python", "."]
