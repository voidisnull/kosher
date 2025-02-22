import os
from pathlib import Path
from typing import Optional, Any, List

from docker.errors import DockerException

from .container import EnvironmentManager


class NodeEnvironmentManager(EnvironmentManager):
    """Environment manager for Node.js projects using Docker."""

    def __init__(
            self,
            base_dir: str = "~/.kosher/environments",
            container_dir: str = "/app",
    ):
        super().__init__(base_dir, container_dir)
        self.lang = "node"

    def create_environment(
            self,
            name: str,
            version: str,
            requirements: Optional[str] = None,
            **kwargs: Any
    ) -> bool | None:
        """Create a new Node.js environment with specified version and requirements."""
        if not name or not version:
            raise ValueError("Environment name/version is required")

        image_name = f"{self.image_prefix}/{self.lang}-{name}:{version}"
        dockerfile_path = Path(f"{self.lang}-{name}.Dockerfile")

        try:
            # Check if image with the same name and version already exists
            try:
                self.client.images.get(image_name)
                self.console.print(f"[red]Error: Environment '{name}' with version '{version}' already exists.[/red]")
                return False
            except DockerException:
                pass

            # Create Node.js-specific Dockerfile
            dockerfile_content = self._generate_dockerfile(version, requirements)
            dockerfile_path.write_text("\n".join(dockerfile_content))

            # Build the Docker image
            self.console.print(f"[cyan]Building Node.js environment: {name}:{version}[/cyan]")
            self.client.images.build(
                path=".",
                dockerfile=str(dockerfile_path),
                tag=image_name,
                rm=True
            )

            # Save the built image locally
            if self.save_image(image_name, name, version):
                self.console.print(f"[green]Created Node.js environment '{name}' with version {version}[/green]")
                return True
            else:
                self.console.print("[red]Failed to save the image locally.[/red]")
                return False

        except DockerException as e:
            self.console.print(f"[red]Error building image: {str(e)}[/red]")
            return False
        finally:
            dockerfile_path.unlink(missing_ok=True)

    def _generate_dockerfile(self, version: str, requirements: Optional[str]) -> List[str]:
        """Generate Dockerfile contents for Node.js environment."""
        dockerfile_content = [
            f"FROM node:{version}-alpine",
            f"WORKDIR {self.container_dir}",
            "RUN npm install -g npm@latest"
        ]

        if requirements:
            if not os.path.exists(requirements):
                raise FileNotFoundError(f"package.json not found: {requirements}")
            dockerfile_content.extend([
                f"COPY {requirements} .",
                "RUN npm install"
            ])

        return dockerfile_content

    def build_source(self, name: str, version: str, **kwargs: Any) -> bool:
        """Build Node.js source code inside the environment."""
        image_name = f"{self.image_prefix}/{self.lang}-{name}:{version}"
        source_dir = os.path.abspath(kwargs.get("source_dir", "."))

        try:
            self.console.print(f"[cyan]Building Node.js project in {name}:{version}[/cyan]")
            container = self.client.containers.run(
                image_name,
                command=["npm", "run", "build"],
                volumes={
                    source_dir: {
                        'bind': self.container_dir,
                        'mode': 'rw'
                    }
                },
                remove=True,
                stream=True
            )

            for log in container:
                if log:
                    self.console.print(log.decode().strip())

            self.console.print(f"[green]Successfully built Node.js project in '{name}:{version}'[/green]")
            return True

        except DockerException as e:
            self.console.print(f"[red]Error building Node.js source: {str(e)}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return False

    def run_code(self, name: str, version: str, code_path: str, **kwargs: Any) -> bool:
        """Run a Node.js script inside the environment container."""
        image_name = f"{self.image_prefix}/{self.lang}-{name}:{version}"
        source_dir = os.path.abspath(os.path.dirname(code_path))
        script_name = os.path.basename(code_path)

        try:
            self.console.print(f"[cyan]Running {script_name} in {name}:{version}[/cyan]")
            container = self.client.containers.run(
                image_name,
                command=["node", f"{self.container_dir}/{script_name}"],
                volumes={
                    source_dir: {
                        'bind': self.container_dir,
                        'mode': 'rw'
                    }
                },
                remove=True,
                stream=True
            )

            for log in container:
                if log:
                    self.console.print(log.decode().strip())

            self.console.print(f"[green]Successfully ran {script_name}[/green]")
            return True

        except DockerException as e:
            self.console.print(f"[red]Error running Node.js script: {str(e)}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return False
