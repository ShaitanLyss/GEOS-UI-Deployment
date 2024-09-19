import os
import subprocess
import sys

env = []
with open(".env", "r") as f:
    for line in f:
        line = line.strip()
        if line:
            if line[0] != "#":
                env.append(line)


# args = parser.parse_args()

# if not args.command:
#     parser.print_help()
#     exit(1)

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
# print(*sys.argv[1:])
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
        *(["--backend", "pp"] if "--backend" not in sys.argv else []),
        *sys.argv[1:],
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
            # print(line.split(" "))
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
