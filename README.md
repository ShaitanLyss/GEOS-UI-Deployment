# GEOS UI Deployment

This repository manages the deployment of the GEOS UI project.

## Pre-requisites
- Docker

## Deployment
1. Clone this repository
2. Copy the `.env.example` file to `.env` and fill in the values
3. Run `docker compose -f ./docker-compose.preprod.yml up --build` to start the deployment

The first time it will take a long time to build the images. Subsequent deployments will be faster.

## Accessing the application
The application will be available at http://localhost.

## Customizing the application
You can set settings like language or night mode by hovering the upper right area of the screen.
