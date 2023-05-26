# Variables
DOCKER_IMAGE_NAME = statuspage-bot
DOCKER_CONTAINER_NAME = statuspage-bot

# Build the Docker image
build:
	docker build -t $(DOCKER_IMAGE_NAME) .

# Run the Docker container
run:
	docker run -d --name $(DOCKER_CONTAINER_NAME) $(DOCKER_IMAGE_NAME)

debug: 
	docker run --name $(DOCKER_CONTAINER_NAME) $(DOCKER_IMAGE_NAME)

# Stop and remove the Docker container
stop:
	docker stop $(DOCKER_CONTAINER_NAME)
	docker rm $(DOCKER_CONTAINER_NAME)

# Remove the Docker image
clean:
	docker rmi $(DOCKER_IMAGE_NAME)

# Default target
.DEFAULT_GOAL := build
