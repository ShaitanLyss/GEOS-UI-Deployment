# GraphGEOS

GraphGEOS is an attempt at creating a graph based configuration system for [GEOS](https://github.com/GEOS-DEV/GEOS). The goal is to significantly improve the experience of all GEOS users.

It has been developed by the Makutu team.

## Prerequisites

To use GraphGEOS, you need to have the following prerequisites installed:

- [Podman](https://podman.io/)
- [Podman Compose](https://github.com/containers/podman-compose) 

Please make sure you have these dependencies installed before proceeding.

## Getting started

To get started, you need to clone this repository:

```bash
git clone https://github.com/ShaitanLyss/GEOS-UI-Deployment
```

Then, you need to create a `.env` file based on the `.env.example` file in the root of the repository. This file will contain the environment variables used by the deployment system.

    
Finally, you can start the deployment system by running the following command in the root of the repository:
    
```bash
python3 geos-ui.py up
```

## Usage

### Starting the deployment system

To start the deployment system, run the following command:

```bash
python3 geos-ui.py up
```

### Stopping the deployment system

To stop the deployment system, run the following command:

```bash
python3 geos-ui.py down
```

### Updating the deployment system

To update the deployment system, run the following command:

```bash
python3 geos-ui.py update
```

