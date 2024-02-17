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
        if var == "CA_CONTENT":
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
