import os
from pathlib import Path
from typing import Optional, Any, List
from docker.errors import DockerException

from container import EnvironmentManager


class PythonEnvironmentManager(EnvironmentManager):
    """Environment manager for Python projects using Docker."""

    def create_environment(
            self,
            name: str,
            version: str,
            requirements: Optional[str] = None,
            **kwargs: Any
    ) -> bool | None:
        """Create a new Python environment with specified version and requirements."""
        if not name or not version:
            raise ValueError("Environment name/version is required")

        image_name = f"{self.image_prefix}/{name}:{version}"
        dockerfile_path = Path(f"{name}.Dockerfile")

        try:
            # Create Python-specific Dockerfile
            dockerfile_content = self._generate_dockerfile(version, requirements)
            dockerfile_path.write_text("\n".join(dockerfile_content))

            # Build the Docker image
            self.console.print(f"[cyan]Building Python environment: {name}:{version}[/cyan]")
            self.client.images.build(
                path=".",
                dockerfile=str(dockerfile_path),
                tag=image_name,
                rm=True
            )

            # Save the built image
            if self.save_image(image_name, name, version):
                self.console.print(f"[green]Created Python environment '{name}' with version {version}[/green]")
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
        """Generate Dockerfile contents for Python environment."""
        dockerfile_content = [
            f"FROM python:{version}-alpine",
            f"WORKDIR {self.container_dir}",
            "RUN pip install --upgrade pip"
        ]

        if requirements:
            if not os.path.exists(requirements):
                raise FileNotFoundError(f"Requirements file not found: {requirements}")
            dockerfile_content.extend([
                f"COPY {requirements} .",
                f"RUN pip install --no-cache-dir -r {requirements}"
            ])

        return dockerfile_content

    def build_source(self, name: str, version: str, **kwargs: Any) -> bool:
        """Build Python source code into executable using PyInstaller."""
        image_name = f"{self.image_prefix}/{name}:{version}"
        source_dir = os.path.abspath(kwargs.get("source_dir", "."))
        output_dir = os.path.join(source_dir, "dist")

        if not os.path.isdir(source_dir):
            self.console.print(f"[red]Error: Source directory '{source_dir}' does not exist.[/red]")
            return False

        try:
            self.console.print(f"[cyan]Building Python project in {name}:{version}[/cyan]")
            
            # Install PyInstaller and build the executable
            container = self.client.containers.run(
                image_name,
                command=[
                    "sh", "-c",
                    f"pip install pyinstaller && pyinstaller --onefile {self.container_dir}/main.py --distpath {self.container_dir}/dist"
                ],
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

            # Verify build success
            built_executable = Path(output_dir) / "main"
            if built_executable.exists():
                self.console.print(f"[green]Successfully built production executable at: {built_executable}[/green]")
                return True
            else:
                self.console.print("[red]Build failed. Executable not found.[/red]")
                return False

        except DockerException as e:
            self.console.print(f"[red]Error building Python source: {str(e)}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return False

    def run_code(self, name: str, version: str, code_path: str, **kwargs: Any) -> bool:
        """Run a Python script inside the environment container."""
        image_name = f"{self.image_prefix}/{name}:{version}"
        source_dir = os.path.abspath(os.path.dirname(code_path))
        script_name = os.path.basename(code_path)

        try:
            self.console.print(f"[cyan]Running {script_name} in {name}:{version}[/cyan]")
            container = self.client.containers.run(
                image_name,
                command=["python", f"{self.container_dir}/{script_name}"],
                volumes={
                    source_dir: {
                        'bind': self.container_dir,
                        'mode': 'rw'
                    }
                },
                remove=True,
                stream=True
            )

            # Stream execution logs
            for log in container:
                if log:
                    self.console.print(log.decode().strip())

            self.console.print(f"[green]Successfully ran {script_name}[/green]")
            return True

        except DockerException as e:
            self.console.print(f"[red]Error running Python script: {str(e)}[/red]")
            return False
        except Exception as e:
            self.console.print(f"[red]Unexpected error: {str(e)}[/red]")
            return False