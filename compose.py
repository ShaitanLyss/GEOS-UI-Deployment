import os
import subprocess
import argparse

parser = argparse.ArgumentParser(description="Run geos-ui-compose")
subparses = parser.add_subparsers(dest="command", required=True)
subparses.add_parser("up", help="Deploy containers")
subparses.add_parser("down", help="Remove containers")
subparses.add_parser("update", help="Update containers")

args = parser.parse_args()

pipe_path = os.path.expanduser("~/geos-ui-compose.pipe")
container_name = "geos-ui-compose"
print("Creating pipe...")
try:
    os.mkfifo(pipe_path)
    print("Pipe created")
except FileExistsError:
    print("Pipe already exists")
except OSError as e:
    print("Error creating pipe: {}".format(e))
subprocess.run(
    [
        "podman",
        "pull",
        "docker.io/moonlyss/geos-ui-compose:latest",
    ]
)
subprocess.run(
    [
        "podman",
        "rm",
        container_name,
    ]
)

subprocess.run(
    [
        "podman",
        "run",
        "-d",
        "--name",
        container_name,
        "-v",
        "{}:/tmp/geos-ui-compose.pipe".format(pipe_path),
        "docker.io/moonlyss/geos-ui-compose:latest",
        "python",
        "my-podman-compose.py",
        args.command,
    ]
)


with open(pipe_path, "r") as f:
    print("Pipe opened")
    while True:
        line = f.readline()
        if line == "end":
            break

subprocess.run(
    [
        "podman",
        "rm",
        container_name,
    ]
)

print("Removing pipe...")
os.remove(pipe_path)
print("Pipe removed")
