from abc import ABCMeta, abstractmethod
import os
import re
import subprocess
from turtle import back
from typing import Dict, List, Set, Type
import dotenv
from pathlib import Path
from pprint import pprint
from pydantic import BaseModel, computed_field
from yaml import load, Loader
import argparse

dotenv.load_dotenv()


class ComposeInterface(metaclass=ABCMeta):
    @abstractmethod
    def create(self, compose: "ComposeInfo"):
        raise NotImplementedError
    
    @abstractmethod
    def start(self, compose: "ComposeInfo"):
        raise NotImplementedError
    
    @abstractmethod
    def exists(self, compose: "ComposeInfo") -> bool:
        raise NotImplementedError
    
    @abstractmethod
    def running(self, compose: "ComposeInfo") -> bool:
        raise NotImplementedError
    
    def up(self, compose: "ComposeInfo"):
        if not self.exists(compose):
            self.create(compose)
        elif not self.running(compose):
            self.start(compose)
        
    @abstractmethod
    def down(self, compose: "ComposeInfo"):
        raise NotImplementedError

    def update(self, compose: "ComposeInfo"):
        self.rm(compose)
        self.pull(compose)
        self.create(compose)

    @abstractmethod
    def rm(self, compose: "ComposeInfo"):
        raise NotImplementedError

    @abstractmethod
    def pull(self, compose: "ComposeInfo"):
        """Pulls images used in compose"""
        raise NotImplementedError


def create_pod_args(compose: "ComposeInfo") -> List[str]:
    return ["--name", compose.name, "--publish", *compose.ports]


def run_service_args(service_name: str, compose: "ComposeInfo") -> List[str]:
    service = compose.services[service_name]
    env_args = (
        [f"-e {k}={format_env_var(v)}" for k, v in service.environment.items()]
        if service.environment
        else []
    )
    res = ["-d", "--pod", compose.name, "--name", service_name, *env_args]

    if service.security_opt:
        res.extend(["--security-opt", *service.security_opt])

    res.append(
        service.image if service.image else service_name,
    )
    return res


def build_service_args(service_name: str, compose: "ComposeInfo") -> List[str]:
    service = compose.services[service_name]

    return [
        "-t",
        service_name,
        service.build.context,
    ]


class PodmanStdoutCompose(ComposeInterface):
    def create(self, compose: "ComposeInfo"):
        print(*["podman", "pod", "create", *create_pod_args(compose)])
        for service_name, service in compose.services.items():
            if service.image:
                print(
                    *[
                        "podman",
                        "run",
                        *run_service_args(service_name, compose),
                    ]
                )
            elif service.build:
                print(
                    *[
                        "podman",
                        "build",
                        *build_service_args(service_name, compose),
                    ]
                )
                print(
                    *[
                        "podman",
                        "run",
                        *run_service_args(service_name, compose),
                    ]
                )
            else:
                raise Exception("Service must have either image or build")

    def down(self, compose: "ComposeInfo"):
        print(*["podman", "pod", "stop", compose.name])

    def rm(self, compose: "ComposeInfo"):
        self.down(compose)
        print(*["podman", "pod", "rm", compose.name])

    def pull(self, compose: "ComposeInfo"):
        for image in compose.images:
            print(*["podman", "pull", image])
            
    def exists(self, compose: "ComposeInfo") -> bool:
        return False
    
    def running(self, compose: "ComposeInfo") -> bool:
        return False
    
    def start(self, compose: "ComposeInfo"):
        return print(*["podman", "pod", "start", compose.name])
            
class PodmanCompose(ComposeInterface):
    def create(self, compose: "ComposeInfo"):
        subprocess.run(["podman", "pod", "create", *create_pod_args(compose)])
        for service_name, service in compose.services.items():
            if service.image:
                subprocess.run(
                    ["podman", "run", *run_service_args(service_name, compose)]
                )
            elif service.build:
                subprocess.run(
                    ["podman", "build", *build_service_args(service_name, compose)]
                )
                subprocess.run(
                    ["podman", "run", *run_service_args(service_name, compose)]
                )
            else:
                raise Exception("Service must have either image or build")

    def down(self, compose: "ComposeInfo"):
        subprocess.run(["podman", "pod", "stop", compose.name])

    def rm(self, compose: "ComposeInfo"):
        self.down(compose)
        subprocess.run(["podman", "pod", "rm", compose.name])

    def pull(self, compose: "ComposeInfo"):
        for image in compose.images:
            subprocess.run(["podman", "pull", image])
            
    def exists(self, compose: "ComposeInfo") -> bool:
        return subprocess.run(["podman", "pod", "exists", compose.name]).returncode == 0
    
    def running(self, compose: "ComposeInfo") -> bool:
        return False


class ServiceBuildInfo(BaseModel):
    context: str


class ServiceInfo(BaseModel):
    image: str | None = None
    build: ServiceBuildInfo | None = None
    depends_on: List[str] | None = None
    environment: dict[str, str | bool] | None = None
    ports: List[str] | None = None
    restart: str | None = None
    security_opt: List[str] | None = None


class ComposeInfo(BaseModel):
    name: str
    services: dict[str, ServiceInfo]
    volumes: dict[str, str | None]

    @computed_field
    @property
    def ports(self) -> List[str]:
        ports = []
        for service in self.services.values():
            if service.ports:
                ports.extend(service.ports)
        return ports

    @computed_field
    @property
    def images(self) -> Set[str]:
        images = set()
        for service in self.services.values():
            if service.image:
                images.add(service.image)
        return images


format_env_pattern = r"\${(\w+)}"


def format_env_var(value: str | bool) -> str:
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return re.sub(
            format_env_pattern, lambda match: os.environ[match.group(1)], value
        )
    else:
        raise ValueError(f"Unsupported type {type(value)}")





def parse_compose_file(file: str | Path) -> ComposeInfo:
    compose_data = load(open(file), Loader=Loader)
    compose_info = ComposeInfo(**compose_data)
    return compose_info

backend_map: Dict[str, Type[ComposeInterface]] = {
    "p": PodmanCompose,
    "podman": PodmanCompose,
    "sp": PodmanStdoutCompose,
    "ps": PodmanStdoutCompose,
    "stdoutPodman": PodmanStdoutCompose,
}

def main():
    parser = argparse.ArgumentParser(description="Manage a compose project")
    parser.add_argument(
        "-f",
        "--file",
        dest="file",
        help="Specify an alternate compose file (default: docker-compose.yml)",
        default="docker-compose.preprod.yml",
    )
    parser.add_argument(
        "-b",
        "--backend",
        dest="backend",
        help="Container backend to use",
        choices=["ps", "sp", "stdoutPodman", "p", "podman"],
        default="podman",
    )

    subparsers = parser.add_subparsers(required=True, dest="command")
    
    subparsers.add_parser("update", help="Update pod with latest images")
    subparsers.add_parser("create", help="Start pod")
    subparsers.add_parser("up", help="Start pod")
    subparsers.add_parser("is-up", help="Check if pod is up")
    subparsers.add_parser("down", help="Stop pod")
    subparsers.add_parser("rm", help="Remove pod")

    args = parser.parse_args()

    compose_info = parse_compose_file(args.file)
    
    compose_backend = backend_map[args.backend]()

    match args.command:
        case "update":
            compose_backend.update(compose_info)
        case "create":
            compose_backend.create(compose_info)
        case "up":
            compose_backend.up(compose_info)
        case "is-up":
            print(compose_backend.running(compose_info))
        case "down":
            compose_backend.down(compose_info)
        case "rm":
            compose_backend.rm(compose_info)
        case _:
            print("unknown command")


if __name__ == "__main__":
    main()
