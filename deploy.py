import subprocess
from dotenv import load_dotenv
import os
import re

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
        value = os.getenv(var, "")
        yaml_str = yaml_str.replace(f"${{{var}}}", f'"{value}"')
    
    return yaml_str


def play_kube(yaml_str: str) -> None:
    subprocess.run("podman play kube --replace -", shell=True, input=yaml_str.encode())
    
def main():
    yaml_str = get_pre_envsubst_yaml()
    yaml_str = envsubst_yaml(yaml_str)
    print(yaml_str)
    play_kube(yaml_str)
    

if __name__ == "__main__":
    main()    
    