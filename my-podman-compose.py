from abc import ABCMeta, abstractmethod
import os
import re
import subprocess
from typing import Any, Dict, List, Set, Type
import dotenv
from pathlib import Path
from pprint import pprint
from pydantic import BaseModel, computed_field
from yaml import load, Loader
import argparse
from ordered_set import OrderedSet

dotenv.load_dotenv()

pipe_path = "/tmp/geos-ui-compose.pipe"


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


def container_name(service_name: str, compose: "ComposeInfo") -> str:
    return f"{compose.name}_{service_name}"


def create_pod_args(compose: "ComposeInfo") -> List[str]:
    return ["--name", compose.name, *[f"--publish {p}" for p in compose.ports]]


def run_service_args(service_name: str, compose: "ComposeInfo") -> List[str]:
    service = compose.services[service_name]
    env_args = (
        [f"-e {k}={format_env_var(v, compose)}" for k, v in service.environment.items()]
        if service.environment
        else []
    )
    res = [
        "-d",
        "--pod",
        compose.name,
        "--name",
        container_name(service_name, compose),
        "--network-alias",
        service_name,
        *env_args,
    ]

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
        container_name(service_name, compose),
        service.build.context,
    ]


class PodmanStdoutCompose(ComposeInterface):
    def create(self, compose: "ComposeInfo"):
        print(*["podman", "pod", "create", *create_pod_args(compose)])
        for service_name in compose.service_order:
            service = compose.services[service_name]
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


class PodmanPipeCompose(ComposeInterface):
    def create(self, compose: "ComposeInfo"):
        with open(pipe_path, "w") as f:
            f.write(f"podman pod create {' '.join(create_pod_args(compose))}\n")
            for service_name in compose.service_order:
                service = compose.services[service_name]
                if service.image:
                    f.write(
                        f"podman run {' '.join(run_service_args(service_name, compose))}\n"
                    )
                elif service.build:
                    f.write(
                        " ".join(
                            ["podman", "run", *run_service_args(service_name, compose)]
                        )
                    )
                    f.write(
                        " ".join(
                            [
                                "podman",
                                "build",
                                *build_service_args(service_name, compose),
                            ]
                        )
                    )
                else:
                    raise Exception("Service must have either image or build")

    def down(self, compose: "ComposeInfo"):
        with open(pipe_path, "w") as f:
            f.write(f"podman pod stop {compose.name}\n")

    def rm(self, compose: "ComposeInfo"):
        self.down(compose)
        with open(pipe_path, "w") as f:
            f.write(f"podman pod rm {compose.name}\n")

    def pull(self, compose: "ComposeInfo"):
        with open(pipe_path, "w") as f:
            for image in compose.images:
                f.write(f"podman pull {image}\n")

    def exists(self, compose: "ComposeInfo") -> bool:
        return False

    def running(self, compose: "ComposeInfo") -> bool:
        return False

    def start(self, compose: "ComposeInfo"):
        with open(pipe_path, "w") as f:
            f.write(f"podman pod start {compose.name}\n")


class PodmanCompose(ComposeInterface):
    def create(self, compose: "ComposeInfo"):
        subprocess.run(["podman", "pod", "create", *create_pod_args(compose)])
        subprocess.run(["podman", "volume"])

        for service_name in compose.service_order:
            service = compose.services[service_name]
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

    def start(self, compose: "ComposeInfo"):
        subprocess.run(["podman", "pod", "start", compose.name])


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

    def model_post_init(self, __context: Any) -> None:
        if self.security_opt:
            self.security_opt = [opt.replace(":", "=") for opt in self.security_opt]


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

    @computed_field
    @property
    def service_order(self) -> List[str]:
        load_order: OrderedSet[str] = OrderedSet()  # type: ignore

        def get_graph() -> dict[str, list[str]]:
            graph = {}
            for service_name, service in self.services.items():
                graph[service_name] = service.depends_on or []
            return graph

        def tree_dfs_postfix(tree: dict[str, list[str]], root: str) -> list[str]:
            res = []
            for child in tree[root]:
                if child not in load_order:
                    res.extend(tree_dfs_postfix(tree, child))
            res.append(root)
            load_order.add(root)
            return res

        graph = get_graph()

        for service_name in self.services:
            tree_dfs_postfix(graph, service_name)
        return load_order.items


format_env_pattern = r"\${(\w+)}"
service_env_pattern = r"SERVICE_(\w+)"

def format_env_var(value: str | bool, compose: "ComposeInfo") -> str:
    def get_env_var(key: str) -> str: 
        match = re.match(service_env_pattern, key)
        if match:
            return container_name(match.group(1), compose)
        else:
            return os.environ[key]
        
    if isinstance(value, bool):
        return "true" if value else "false"
    elif isinstance(value, str):
        return re.sub(
            format_env_pattern, lambda match: get_env_var(match.group(1)), value
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
    "pp": PodmanPipeCompose,
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
        choices=backend_map.keys(),
        default="podman",
    )

    subparsers = parser.add_subparsers(required=True, dest="command")

    subparsers.add_parser("load_order", help="Print service load order")
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
        case "load_order":
            print(compose_info.service_order)
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

    try:
        with open(pipe_path, "w") as f:
            f.write("end\n")
    except FileNotFoundError:
        pass


if __name__ == "__main__":
    main()
