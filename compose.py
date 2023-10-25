import os
import subprocess
import argparse

env = []
with open(".env", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            if line[0] != "#":
                env.append(line)

parser = argparse.ArgumentParser(description="Run geos-ui-compose")
# parser.add_argument("-u", "--update-image",dest="updt_img", action="store_true", help="Update compose image")
subparses = parser.add_subparsers(dest="command")
subparses.add_parser("up", help="Deploy containers")
subparses.add_parser("down", help="Remove containers")
subparses.add_parser("update", help="Update containers")

args = parser.parse_args()

if not args.command:
    parser.print_help()
    exit(1)

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
    
print("Pulling latest compose image...")
subprocess.run(
    [
        "podman",
        "pull",
        "docker.io/moonlyss/geos-ui-compose:latest",
    ]
)
print("Done.")
print("Removing prevvious compose container if exists...")
subprocess.run(
    [
        "podman",
        "rm",
        container_name,
    ],
)
print("Done.")

my_compose = subprocess.Popen(
    [
        "podman",
        "run",
        "-d",
        "--name",
        container_name,
        "-v",
        f"{pipe_path}:/tmp/geos-ui-compose.pipe",
        *[f"-e {e}" for e in env],  # env,
        "docker.io/moonlyss/geos-ui-compose:latest",
        "python",
        "my-podman-compose.py",
        "--backend",
        "pp",
        args.command,
    ],
    stdout=subprocess.PIPE,
    stderr=subprocess.PIPE,
)
stdout, stderr = my_compose.communicate()
print(stdout.decode())
print(stderr.decode())

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
