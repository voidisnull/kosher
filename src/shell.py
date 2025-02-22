import argparse
import sys

from ctr.container import EnvironmentManager
from ctr.node import NodeEnvironmentManager
from ctr.python import PythonEnvironmentManager
from ctr.ruby import RubyEnvironmentManager
from rich.console import Console

DEFAULT_VERSIONS = {
    "python": "3.10",
    "node": "20",
    "ruby": "3.3"
}


class ShellPrompt:
    """Shell prompt for Kosher - Language Environment Manager."""

    def __init__(self):
        self.console = Console()
        self.parser = argparse.ArgumentParser(
            description="Kosher - Language Environment Manager"
        )
        self._setup_arguments()

    def _setup_arguments(self):
        self.parser.add_argument(
            "command",
            choices=["create", "activate", "list", "delete", "run", "build"],
            help="Command to execute"
        )
        self.parser.add_argument(
            "name",
            nargs="?",
            help="Environment name"
        )
        self.parser.add_argument(
            "-t", "--type",
            choices=["python", "node", "ruby"],
            default="python",
            help="Environment type (default: python)"
        )
        self.parser.add_argument(
            "-v", "--version",
            help="Language version (e.g., '3.9' for Python, '16' for Node, '3.1' for Ruby)"
        )
        self.parser.add_argument(
            "-r", "--requirements",
            help="Path to requirements file (requirements.txt for Python, package.json for Node, Gemfile for Ruby)"
        )
        self.parser.add_argument(
            "-c", "--code",
            help="Path to code file to run inside the environment"
        )
        self.parser.add_argument(
            "-s", "--source_dir",
            help="Path to source code directory for build command"
        )
        self.parser.add_argument(
            "-o", "--output_dir",
            help="Path to output directory for build artifacts"
        )

    @staticmethod
    def get_environment_manager(env_type: str) -> EnvironmentManager:
        """Return the appropriate environment manager based on type."""
        managers = {
            "python": PythonEnvironmentManager,
            "node": NodeEnvironmentManager,
            "ruby": RubyEnvironmentManager
        }
        if env_type not in managers:
            raise ValueError(f"Unsupported environment type: {env_type}")
        return managers[env_type]()

    def execute(self):
        """Parse arguments and execute the command."""
        args = self.parser.parse_args()

        try:
            manager = self.get_environment_manager(args.type)

            match args.command:
                case "create":
                    version = args.version or DEFAULT_VERSIONS.get(args.type)
                    manager.create_environment(args.name, version, args.requirements)
                case "activate":
                    manager.activate_environment(args.name)
                case "list":
                    environments = manager.list_environments()
                    if environments:
                        self.console.print("[green]Available environments:[/green]")
                        for env in environments:
                            self.console.print(f"- {manager.image_prefix}/{env['name']}:{env['version']}")
                    else:
                        self.console.print(
                            "[yellow]No environments found. Create one using the 'create' command.[/yellow]")
                case "delete":
                    manager.delete_environment(args.name)
                case "run":
                    if not args.code:
                        self.console.print("[red]Error: --code (-c) argument is required for 'run' command[/red]")
                        sys.exit(1)
                    manager.run_code(args.name, args.version, args.code)
                case "build":
                    if not args.source_dir:
                        self.console.print("[red]Error: --source_dir (-s) is required for 'build' command[/red]")
                        sys.exit(1)
                    manager.build_source(
                        name=args.name,
                        version=args.version or "",
                        source_dir=args.source_dir,
                        output_dir=args.output_dir or "./dist"
                    )
                case _:
                    self.console.print(f"[red]Unknown command: {args.command}[/red]")
                    sys.exit(1)

        except Exception as e:
            self.console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
