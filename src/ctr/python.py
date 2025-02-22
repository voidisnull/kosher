import os
import subprocess
from pathlib import Path
from typing import Optional, Any

from container import EnvironmentManager


class PythonEnvironmentManager(EnvironmentManager):
    def create_environment(
            self,
            name: str,
            version: str,
            requirements: Optional[str] = None,
            **kwargs: Any
    ) -> bool:
        if not name or not version:
            raise ValueError("Environment name/version is required")

        image_name = f"{self.image_prefix}/{name}:{version}"

        # Create Python-specific Dockerfile
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

        dockerfile_path = Path(f"{name}.Dockerfile")
        dockerfile_path.write_text("\n".join(dockerfile_content))

        try:
            subprocess.run(
                ["docker", "build", "-t", image_name, "-f", str(dockerfile_path), "."],
                check=True,
                capture_output=True,
                text=True
            )

            if self.save_image(image_name, name, version):
                print(f"Created Python environment '{name}' with version {version}")
                return True
            return False

        except subprocess.CalledProcessError as e:
            print(f"Error building image: {e.stderr}")
            return False
        finally:
            dockerfile_path.unlink(missing_ok=True)
            subprocess.run(["docker", "rmi", image_name], check=False)

    def build_source(self, name: str, version: str, **kwargs: Any) -> bool:
        image_name = f"{self.image_prefix}/{name}:{version}"
        source_dir = os.path.abspath(kwargs.get("source_dir", "."))
        output_dir = os.path.join(source_dir, "dist")

        if not os.path.isdir(source_dir):
            print(f"Error: Source directory '{source_dir}' does not exist.")
            return False

        try:
            # Run PyInstaller inside the Docker container
            subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{source_dir}:{self.container_dir}",
                    image_name, "sh", "-c",
                    f"pip install pyinstaller && pyinstaller --onefile {self.container_dir}/main.py --distpath {self.container_dir}/dist"
                ],
                check=True,
                capture_output=True,
                text=True
            )

            # Check if the build was successful
            built_executable = os.path.join(output_dir, "main")
            if os.path.exists(built_executable):
                print(f"Successfully built production executable at: {built_executable}")
                return True
            else:
                print("Build failed. Executable not found.")
                return False

        except subprocess.CalledProcessError as e:
            print(f"Error during build: {e.stderr}")
            return False

        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
