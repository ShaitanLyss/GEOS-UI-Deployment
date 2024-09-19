<<<<<<< HEAD
import subprocess
from dotenv import load_dotenv
import os
import re
import argparse

load_dotenv()


def get_pre_envsubst_yaml(dir: str = "kubernetes") -> str:
    """
    Combine all yaml files describing kubernetes ressources into one file
    """

    # Get all files in the directory
    files = os.listdir(dir)

    # Filter out non-yaml files
    files = [f for f in files if f.endswith(".yaml")]

    # Read all files and combine them into one string
    yaml_a = []
    for f in files:
        with open(os.path.join(dir, f)) as file:
            yaml_a.append(file.read())

    return "\n---\n".join(yaml_a)


def envsubst_yaml(yaml_str: str) -> str:
    """
    Replace all environment variables in a yaml string
    """

    # Find all environment variables in the yaml string
    env_vars = re.findall(r"\$\{([A-Za-z0-9_]+)\}", yaml_str)

    # Replace all environment variables with their values
    for var in env_vars:
        if False and var == "CA_CONTENT":
            with open("/etc/ssl/certs/ca-bundle.crt") as f:
                value = f.read()
        else:
            value = os.getenv(var, "")
        yaml_str = yaml_str.replace(f"${{{var}}}", f'"{value}"')

    return yaml_str


def play_kube(yaml_str: str, down: bool = False) -> None:
    subprocess.run(
        "podman play kube --replace {} -".format("--down" if down else ""),
        shell=True,
        input=yaml_str.encode(),
    )


def main():

    # use argparse to setup commands like up or down
    parser = argparse.ArgumentParser(description="Kubernetes deployment")
    parser.add_argument_group("up", "Deploy the application")
    parser.add_argument_group("down", "Remove the application")

    
    parser.add_argument(
        "command", help="Command to run", choices=["up", "down"], default="up"
    )
    yaml_str = get_pre_envsubst_yaml()
    yaml_str = envsubst_yaml(yaml_str)
    args = parser.parse_args()
    print(yaml_str)
    command = args.command
    
    subprocess.run("podman unshare chown -R 0:0 /var/tmp/j1100389/share/containers-4 /run/user/1100389/containers-4".split())
    if command == "up":
        print("Deploying application")
        play_kube(yaml_str)
    elif command == "down":
        print("Removing application")
        play_kube(yaml_str, down=True)
        def port_pids(port) -> str:
            return f"$(lsof -i :{port} -t)"
        ports_to_kill = list(map(str, [8000, 5432, 3000, 9200]))
        print(f"Killing processes bound to ports {' '.join(ports_to_kill)}...")
        pids_to_kill_getter = " ".join(map(port_pids, ports_to_kill))
        pids_to_kill = (
            subprocess.check_output(f"echo {pids_to_kill_getter}", shell=True)
            .decode("utf-8")
            .strip()
        )
        if pids_to_kill:
            print("Following processes will be killed :", pids_to_kill)
            subprocess.run(["ps", "-o", "user,pid,cmd", "p", pids_to_kill])
            if not input("Continue (y/n)").lower().startswith("y"):
                print("Cancelling.")
                exit()
            subprocess.run(["kill", *pids_to_kill.split()])
    subprocess.run("podman unshare chown -R 0:0 /var/tmp/j1100389/share/containers-4 /run/user/1100389/containers-4".split())


if __name__ == "__main__":
    main()
=======
import subprocess
from dotenv import load_dotenv
import os
import re
import argparse

load_dotenv()


def get_pre_envsubst_yaml(dir: str = "kubernetes") -> str:
    """
    Combine all yaml files describing kubernetes ressources into one file
    """

    # Get all files in the directory
    files = os.listdir(dir)

    # Filter out non-yaml files
    files = [f for f in files if f.endswith(".yaml")]

    # Read all files and combine them into one string
    yaml_a = []
    for f in files:
        with open(os.path.join(dir, f)) as file:
            yaml_a.append(file.read())

    return "\n---\n".join(yaml_a)


def envsubst_yaml(yaml_str: str) -> str:
    """
    Replace all environment variables in a yaml string
    """

    # Find all environment variables in the yaml string
    env_vars = re.findall(r"\$\{([A-Za-z0-9_]+)\}", yaml_str)

    # Replace all environment variables with their values
    for var in env_vars:
        if False and var == "CA_CONTENT":
            with open("/etc/ssl/certs/ca-bundle.crt") as f:
                value = f.read()
        else:
            value = os.getenv(var, "")
        yaml_str = yaml_str.replace(f"${{{var}}}", f'"{value}"')

    return yaml_str


def play_kube(yaml_str: str, down: bool = False) -> None:
    subprocess.run(
        "podman play kube --replace {} -".format("--down" if down else ""),
        shell=True,
        input=yaml_str.encode(),
    )


def main():

    # use argparse to setup commands like up or down
    parser = argparse.ArgumentParser(description="Kubernetes deployment")
    parser.add_argument_group("up", "Deploy the application")
    parser.add_argument_group("down", "Remove the application")

    
    parser.add_argument(
        "command", help="Command to run", choices=["up", "down"], default="up"
    )
    yaml_str = get_pre_envsubst_yaml()
    yaml_str = envsubst_yaml(yaml_str)
    args = parser.parse_args()
    print(yaml_str)
    command = args.command

    if command == "up":
        print("Deploying application")
        play_kube(yaml_str)
    elif command == "down":
        print("Removing application")
        play_kube(yaml_str, down=True)


if __name__ == "__main__":
    main()
>>>>>>> 8b6542b0fdef69723867cea0c7fde46ff3a22390
