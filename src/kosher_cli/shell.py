import argparse
import sys

from rich.console import Console

from kosher_cli.ctr.container import EnvironmentManager
from kosher_cli.ctr.node import NodeEnvironmentManager
from kosher_cli.ctr.python import PythonEnvironmentManager
from kosher_cli.ctr.ruby import RubyEnvironmentManager

DEFAULT_VERSIONS = {
    "python": "3.10",
    "node": "20",
    "ruby": "3.3"
}


class ShellPrompt:
    """Shell prompt for Kosher - Language Environment Manager."""

    def __init__(self):
        self._console = Console()
        self._parser = argparse.ArgumentParser(
            description="Kosher - Language Environment Manager"
        )
        self._setup_arguments()

    def _setup_arguments(self):
        self._parser.add_argument(
            "command",
            choices=["create", "activate", "list", "delete", "run", "build"],
            help="Command to execute"
        )
        self._parser.add_argument(
            "name",
            nargs="?",
            help="Environment name"
        )
        self._parser.add_argument(
            "-l", "--lang",
            choices=["python", "node", "ruby"],
            default="python",
            help="Environment type (default: python)"
        )
        self._parser.add_argument(
            "-v", "--version",
            help="Language version (e.g., '3.12' for Python, '20' for Node, '3.3' for Ruby)"
        )
        self._parser.add_argument(
            "-r", "--requirements",
            help="Path to requirements file (requirements.txt for Python, package.json for Node, Gemfile for Ruby)"
        )
        self._parser.add_argument(
            "-c", "--code",
            help="Path to code file to run inside the environment"
        )
        self._parser.add_argument(
            "-s", "--source_dir",
            help="Path to source code directory for build command"
        )
        self._parser.add_argument(
            "-o", "--output_dir",
            help="Path to output directory for build artifacts"
        )

    @staticmethod
    def _get_environment_manager(lang: str) -> EnvironmentManager:
        """Return the appropriate environment manager based on language."""
        managers = {
            "python": PythonEnvironmentManager,
            "node": NodeEnvironmentManager,
            "ruby": RubyEnvironmentManager
        }
        if lang not in managers:
            raise ValueError(f"Unsupported environment type: {lang}")
        return managers[lang]()

    def execute(self):
        """Parse arguments and execute the command."""
        args = self._parser.parse_args()

        try:
            manager = self._get_environment_manager(args.lang)
            version = args.version or DEFAULT_VERSIONS.get(args.lang)

            match args.command:
                case "create":
                    manager.create_environment(args.name, version, args.requirements)
                case "activate":
                    manager.activate_environment(args.name, args.lang)
                case "list":
                    environments = manager.list_environments()
                    if environments:
                        self._console.print("[green]Available environments:[/green]")
                        for env in environments:
                            self._console.print(
                                f"- {manager.image_prefix}/{env['lang']}-{env['name']}:{env['version']}"
                            )
                    else:
                        self._console.print(
                            "[yellow]No environments found. Create one using the 'create' command.[/yellow]"
                        )
                case "delete":
                    manager.delete_environment(args.name, args.lang)
                case "run":
                    if not args.code:
                        self._console.print("[red]Error: --code (-c) argument is required for 'run' command[/red]")
                        sys.exit(1)
                    manager.run_code(args.name, version, args.code)
                case "build":
                    if not args.source_dir:
                        self._console.print("[red]Error: --source_dir (-s) is required for 'build' command[/red]")
                        sys.exit(1)
                    manager.build_source(
                        name=args.name,
                        version=version,
                        source_dir=args.source_dir,
                        output_dir=args.output_dir or "./dist"
                    )
                case _:
                    self._console.print(f"[red]Unknown command: {args.command}[/red]")
                    sys.exit(1)

        except ValueError as ve:
            self._console.print(f"[red]Invalid input: {ve}[/red]")
            sys.exit(1)
        except Exception as e:
            self._console.print(f"[red]Error: {e}[/red]")
            sys.exit(1)
