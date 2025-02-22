import os
import subprocess
from pathlib import Path
from typing import Optional, Any

from container import EnvironmentManager


class RubyEnvironmentManager(EnvironmentManager):
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

        # Create Ruby-specific Dockerfile
        dockerfile_content = [
            f"FROM ruby:{version}-alpine",
            f"WORKDIR {self.container_dir}",
            "RUN gem install bundler"
        ]

        if requirements:
            if not os.path.exists(requirements):
                raise FileNotFoundError(f"Gemfile not found: {requirements}")
            dockerfile_content.extend([
                f"COPY {requirements} .",
                "RUN bundle install"
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
                print(f"Created Ruby environment '{name}' with version {version}")
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
        output_dir = kwargs.get("output_dir", "dist")

        try:
            # Run the Ruby build inside Docker
            subprocess.run(
                [
                    "docker", "run", "--rm",
                    "-v", f"{os.path.abspath(source_dir)}:{self.container_dir}",
                    "-v", f"{os.path.abspath(output_dir)}:/app/dist",
                    image_name, "sh", "-c",
                    "bundle install && rake build"
                ],
                check=True
            )
            print(f"Successfully built Ruby code in '{name}:{version}'")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error building Ruby source: {e.stderr}")
            return False

        except Exception as e:
            print(f"Unexpected error: {e}")
            return False
