import os
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List, Any

from docker import from_env as docker_from_env
from docker.errors import DockerException
from rich.console import Console


class EnvironmentManager(ABC):
    """Base class for environment management with Docker."""

    def __init__(
            self,
            base_dir: str = "~/.kosher/environments",
            container_dir: str = "/app",
    ):
        self.base_dir = Path(os.path.expanduser(base_dir))
        self.container_dir = container_dir
        self.image_prefix = "kosher"
        self.client = docker_from_env()
        self.console = Console()
        self.base_dir.mkdir(parents=True, exist_ok=True)

    def get_image_path(self, name: str, version: str) -> Path:
        """Get the path where the image tar should be stored."""
        return self.base_dir / f"{name}-{version}.tar"

    def save_image(self, image_name: str, name: str, version: str) -> bool:
        """Save Docker image as tar file in environments directory."""
        image_path = self.get_image_path(name, version)
        try:
            image = self.client.images.get(image_name)
            with open(image_path, 'wb') as f:
                for chunk in image.save():
                    f.write(chunk)
            self.console.print(f"[green]Successfully saved image: {image_name}[/green]")
            return True
        except DockerException as e:
            self.console.print(f"[red]Error saving image: {str(e)}[/red]")
            return False

    def load_image(self, name: str, version: str) -> Optional[str]:
        """Load Docker image from tar file and return image name."""
        image_path = self.get_image_path(name, version)
        if not image_path.exists():
            self.console.print(f"[yellow]Image file not found: {image_path}[/yellow]")
            return None

        try:
            with open(image_path, 'rb') as f:
                self.client.images.load(f.read())
            image_name = f"{self.image_prefix}/{name}:{version}"
            self.console.print(f"[green]Successfully loaded image: {image_name}[/green]")
            return image_name
        except DockerException as e:
            self.console.print(f"[red]Error loading image: {str(e)}[/red]")
            return None

    @abstractmethod
    def create_environment(
            self,
            name: str,
            version: str,
            requirements: Optional[str] = None,
            **kwargs: Any
    ) -> bool | None:
        """Create a new environment."""
        pass

    @abstractmethod
    def build_source(self, name: str, version: str, **kwargs: Any) -> bool:
        """Build source code inside the environment."""
        pass

    @abstractmethod
    def run_code(self, name: str, version: str, code_path: str, **kwargs: Any) -> bool:
        """Run code inside the environment container."""
        pass

    def activate_environment(self, name: str) -> bool | None:
        """Activate and enter an environment."""
        if not name:
            raise ValueError("Environment name is required")

        # Find the environment file
        env_files = list(self.base_dir.glob(f"{name}-*.tar"))
        if not env_files:
            self.console.print(f"[red]Error: Environment '{name}' does not exist[/red]")
            return False

        # Get version from filename
        version = env_files[0].stem.split('-')[-1]
        image_name = f"{self.image_prefix}/{name}:{version}"

        # Force check for local image only
        try:
            self.client.images.get(image_name)
            self.console.print(f"[green]Using local image: {image_name}[/green]")
        except DockerException:
            self.console.print(f"[red]Local image '{image_name}' not found. Pulling is disabled. Aborting.[/red]")
            return False

        try:
            self.console.print(f"[cyan]Starting environment: {name}[/cyan]")

            # Start container without command to keep it running
            container = self.client.containers.run(
                image_name,
                command="tail -f /dev/null",  # Keeps the container alive
                volumes={
                    os.getcwd(): {
                        'bind': self.container_dir,
                        'mode': 'rw'
                    }
                },
                detach=True,
                tty=True,
                stdin_open=True,
                remove=True
            )

            # Check if /bin/bash exists
            exec_result = container.exec_run("test -x /bin/bash", demux=True)
            shell = "/bin/bash" if exec_result.exit_code == 0 else "/bin/sh"

            if shell == "/bin/sh":
                self.console.print("[yellow]/bin/bash not found, using /bin/sh[/yellow]")

            # Attach to the container interactively
            subprocess.run(["docker", "exec", "-it", container.id, shell])

            return True

        except DockerException as e:
            self.console.print(f"[red]Error activating environment: {str(e)}[/red]")
            return False
        except KeyboardInterrupt:
            self.console.print("\n[yellow]Environment activation interrupted[/yellow]")
            return False
        finally:
            # Clean up after activation
            try:
                self.client.images.remove(image_name)
                self.console.print("[dim]Cleaned up environment resources[/dim]")
            except DockerException:
                pass

    def list_environments(self) -> List[Dict[str, str]]:
        """List all available environments."""
        environments = []
        for file in self.base_dir.glob('*.tar'):
            name, version = file.stem.rsplit('-', 1)
            environments.append({
                'name': name,
                'version': version,
                'file': file.name
            })

        if environments:
            self.console.print("[green]Found the following environments:[/green]")
            for env in environments:
                self.console.print(f"  [cyan]{env['name']}[/cyan] (version: {env['version']})")
        else:
            self.console.print("[yellow]No environments found[/yellow]")

        return environments

    def delete_environment(self, name: str) -> bool:
        """Delete an environment."""
        if not name:
            raise ValueError("Environment name is required")

        env_files = list(self.base_dir.glob(f"{name}-*.tar"))
        if not env_files:
            self.console.print(f"[red]Error: Environment '{name}' does not exist[/red]")
            return False

        try:
            env_files[0].unlink()
            self.console.print(f"[green]Successfully deleted environment '{name}'[/green]")
            return True
        except OSError as e:
            self.console.print(f"[red]Error deleting environment: {e}[/red]")
            return False
