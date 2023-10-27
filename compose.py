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
subparses.add_parser("rm", help="Remove containers")

args = parser.parse_args()

if not args.command:
    parser.print_help()
    exit(1)

print("# Setting up\n")
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
print("Removing previous compose container if exists...")
subprocess.run(
    [
        "podman",
        "rm",
        "-i",
        container_name,
    ],
)
print("Done.")

print("\n# Running compose container\n")
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


with open(pipe_path, "r") as f:
    while True:
        try:
            stdout, stderr = my_compose.communicate()
            if stdout.decode.strip():
                pass
                # print(stdout.decode())
            if stderr.decode.strip():
                pass
                # print(stderr.decode())
        except Exception as e:
            pass
        
        line = f.readline().strip()
        if line == "end":
            break
        
        if line:
            print(line)
            print(line.split(" "))
            subprocess.run(line.split(" "))
            print()

print("\n# Cleaning up")
print("Removing compose container...")
subprocess.run(
    [
        "podman",
        "rm",
        container_name,
    ]
)
print("Done.")
print("Removing pipe...")
os.remove(pipe_path)
print("Done.")
