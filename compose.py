import os
import subprocess

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
        "run",
        "-d",
        "--name",
        container_name,
        "-v",
        "{}:/tmp/geos-ui-compose.pipe".format(pipe_path),
        "docker.io/moonlyss/geos-ui-compose:latest",
    ]
)


with open("pipe_path", "r") as f:
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
