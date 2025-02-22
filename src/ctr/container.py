import os
import sys
import shutil
import argparse
import subprocess
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional, Dict, List, Any

class EnvironmentManager(ABC):
    """Base class for environment management with Docker."""
    
    def __init__(
        self,
        base_dir: str = "~/.kosher/environments",
        container_dir: str = "/app",
    ):
        self.base_dir = os.path.expanduser(base_dir)
        self.container_dir = container_dir
        self.image_prefix = "kosher"
        os.makedirs(self.base_dir, exist_ok=True)

    def get_image_path(self, name: str, version: str) -> str:
        """Get the path where the image tar should be stored."""
        return os.path.join(self.base_dir, f"{name}-{version}.tar")

    def save_image(self, image_name: str, name: str, version: str) -> bool:
        """Save Docker image as tar file in environments directory."""
        image_path = self.get_image_path(name, version)
        try:
            subprocess.run(
                ["docker", "save", "-o", image_path, image_name],
                check=True,
                capture_output=True,
                text=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error saving image: {e.stderr}")
            return False

    def load_image(self, name: str, version: str) -> Optional[str]:
        """Load Docker image from tar file and return image name."""
        image_path = self.get_image_path(name, version)
        if not os.path.exists(image_path):
            return None
        
        try:
            subprocess.run(
                ["docker", "load", "-i", image_path],
                check=True,
                capture_output=True,
                text=True
            )
            return f"{self.image_prefix}/{name}:{version}"
        except subprocess.CalledProcessError as e:
            print(f"Error loading image: {e.stderr}")
            return None

    @abstractmethod
    def create_environment(
        self,
        name: str,
        version: str,
        requirements: Optional[str] = None,
        **kwargs: Any
    ) -> bool:
        """Create a new environment. To be implemented by each language."""
        pass

    def activate_environment(self, name: str) -> bool:
        """Activate and enter an environment."""
        if not name:
            raise ValueError("Environment name is required")
        
        # Find the environment file
        env_files = [f for f in os.listdir(self.base_dir) 
                    if f.startswith(f"{name}-") and f.endswith('.tar')]
        
        if not env_files:
            print(f"Error: Environment '{name}' does not exist")
            return False
        
        # Get version from filename
        version = env_files[0][len(name)+1:-4]
        image_name = f"{self.image_prefix}/{name}:{version}"
        
        # Load the image
        if not self.load_image(name, version):
            return False
        
        try:
            # Run the container
            subprocess.run(
                [
                    "docker", "run", "-it", "--rm",
                    "-v", f"{os.getcwd()}:{self.container_dir}",
                    image_name,
                    "/bin/bash"
                ],
                check=True
            )
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error activating environment: {e}")
            return False
        except KeyboardInterrupt:
            print("\nEnvironment activation interrupted.")
            return False
        finally:
            # Clean up
            subprocess.run(["docker", "rmi", image_name], check=False)

    def list_environments(self) -> List[Dict[str, str]]:
        """List all available environments."""
        environments = []
        for file in os.listdir(self.base_dir):
            if file.endswith('.tar'):
                name, version = file[:-4].rsplit('-', 1)
                environments.append({
                    'name': name,
                    'version': version,
                    'file': file
                })
        return environments

    def delete_environment(self, name: str) -> bool:
        """Delete an environment."""
        if not name:
            raise ValueError("Environment name is required")
        
        env_files = [f for f in os.listdir(self.base_dir) 
                    if f.startswith(f"{name}-") and f.endswith('.tar')]
        
        if not env_files:
            print(f"Error: Environment '{name}' does not exist")
            return False
        
        try:
            os.remove(os.path.join(self.base_dir, env_files[0]))
            print(f"Deleted environment '{name}'")
            return True
        except OSError as e:
            print(f"Error deleting environment: {e}")
            return False
