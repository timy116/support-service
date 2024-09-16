SUPPORT_SERVICE_NAME = support-service
REDIS_NAME = redis

build-support-service:
	docker-compose build --no-cache ${SUPPORT_SERVICE_NAME}

up-support-service:
	docker-compose up -d ${SUPPORT_SERVICE_NAME}

up-redis:
	docker-compose up -d ${REDIS_NAME}
