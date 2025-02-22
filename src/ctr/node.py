import os
from pathlib import Path
from typing import Optional, Any, List
from docker.errors import DockerException

from container import EnvironmentManager


class NodeEnvironmentManager(EnvironmentManager):
    """Environment manager for Node.js projects using Docker."""

    def create_environment(
            self,
            name: str,
            version: str,
            requirements: Optional[str] = None,
            **kwargs: Any
    ) -> bool:
        """Create a new Node.js environment with specified version and requirements."""
        if not name or not version:
            raise ValueError("Environment name/version is required")

        image_name = f"{self.image_prefix}/{name}:{version}"
        dockerfile_path = Path(f"{name}.Dockerfile")

        try:
            # Create Node-specific Dockerfile
            dockerfile_content = self._generate_dockerfile(version, requirements)
            dockerfile_path.write_text("\n".join(dockerfile_content))

            # Build the Docker image
            self.console.print(f"[cyan]Building Node.js environment: {name}:{version}[/cyan]")
            build_output = self.client.images.build(
                path=".",
                dockerfile=str(dockerfile_path),
                tag=image_name,
                rm=True
            )

            # Save the built image
            if self.save_image(image_name, name, version):
                self.console.print(f"[green]Created Node environment '{name}' with version {version}[/green]")
                return True
            return False

        except DockerException as e:
            self.console.print(f"[red]Error building image: {str(e)}[/red]")
            return False
        finally:
            # Cleanup
            dockerfile_path.unlink(missing_ok=True)
            try:
                self.client.images.remove(image_name, force=True)
            except DockerException:
                pass

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
        image_name = f"{self.image_prefix}/{name}:{version}"
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

            # Stream build logs
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