#!/bin/bash

# Script to build and push Docker images for meobeo-ai-api
# Supports both development and production environments

# Registry information
REGISTRY="harbor.epoints.vn/ai"
REPO_NAME="meobeo-ai-api"
DEV_REPO_NAME="meobeo-ai-api-dev"
TAG="latest"

# Redis DB configuration
PROD_REDIS_DB="0"
DEV_REDIS_DB="5"

# Helper function to show usage
show_usage() {
  echo "Usage: $0 [options]"
  echo "Options:"
  echo "  -e, --environment ENVIRONMENT   Environment to build for (dev, prod, all). Default: all"
  echo "  -t, --tag TAG                   Tag for the Docker image. Default: latest"
  echo "  -h, --help                      Show this help message"
}

# Parse command line arguments
while [[ "$#" -gt 0 ]]; do
  case $1 in
    -e|--environment) ENV="$2"; shift ;;
    -t|--tag) TAG="$2"; shift ;;
    -h|--help) show_usage; exit 0 ;;
    *) echo "Unknown parameter: $1"; show_usage; exit 1 ;;
  esac
  shift
done

# Default to building all environments if not specified
if [ -z "$ENV" ]; then
  ENV="all"
fi

# Validate environment argument
if [[ "$ENV" != "dev" && "$ENV" != "prod" && "$ENV" != "all" ]]; then
  echo "Invalid environment: $ENV. Must be 'dev', 'prod', or 'all'"
  show_usage
  exit 1
fi

echo "====== MeoBeo AI API Docker Build & Push Script ======"
echo "Building for environment(s): $ENV"
echo "Using tag: $TAG"
echo "===================================================="

# Function to build and push an image
build_and_push() {
  local env=$1
  local env_value=$2
  local repo_name=$3
  local redis_db=$4
  local full_image_name="$REGISTRY/$repo_name:$TAG"

  echo "Building $env image"
  echo "Image name: $full_image_name"
  echo "Redis DB: $redis_db"
  
  # Build the Docker image with appropriate environment variables based on docker-compose
  docker build --platform linux/amd64 \
    --build-arg ENV="$env_value" \
    --build-arg TZ="Asia/Ho_Chi_Minh" \
    --build-arg REDIS_DB="$redis_db" \
    -t "$full_image_name" .
  
  if [ $? -ne 0 ]; then
    echo "Error building $env image"
    return 1
  fi
  
  echo "Successfully built $env image: $full_image_name"
  
  # Push the Docker image
  echo "Pushing $env image to registry..."
  docker push "$full_image_name"
  
  if [ $? -ne 0 ]; then
    echo "Error pushing $env image"
    return 1
  fi
  
  echo "Successfully pushed $env image: $full_image_name"
  return 0
}

# Build and push development image if requested
if [[ "$ENV" == "dev" || "$ENV" == "all" ]]; then
  build_and_push "development" "development" "$DEV_REPO_NAME" "$DEV_REDIS_DB"
  if [ $? -ne 0 ]; then
    echo "Development build/push failed"
    exit 1
  fi
fi

# Build and push production image if requested
if [[ "$ENV" == "prod" || "$ENV" == "all" ]]; then
  build_and_push "production" "production" "$REPO_NAME" "$PROD_REDIS_DB"
  if [ $? -ne 0 ]; then
    echo "Production build/push failed"
    exit 1
  fi
fi

echo "===================================================="
echo "All requested builds completed successfully!"
echo "===================================================="