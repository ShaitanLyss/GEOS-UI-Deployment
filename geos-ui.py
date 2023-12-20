import os
import argparse


def compose(command: str):
    os.system(f"podman-compose {command}")


""" Script for managing geos deployment using podman compose
Commands are :
update
up
down
logs
"""


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "command", help="Command to run", choices=["update", "up", "down", "logs"]
    )
    args = parser.parse_args()
    command = args.command
    if command == "update":
        print("Updating geos-ui-compose image...")
        compose("pull")
        compose("down")
        compose("up -d")
        print("Done.")
    elif command == "up":
        print("Starting geos-ui-compose container...")
        compose("up -d")
        print("Done.")
    elif command == "down":
        print("Stopping geos-ui-compose container...")
        compose("down")
        print("Done.")
    elif command == "logs":
        print("Showing geos-ui-compose logs...")
        compose("logs -f")
        print("Done.")
