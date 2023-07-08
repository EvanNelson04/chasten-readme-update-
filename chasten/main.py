"""Chasten checks the AST of a Python program."""

from pathlib import Path
from typing import List

import typer
from pyastgrep import search as pyastgrepsearch  # type: ignore
from rich.console import Console
from trogon import Trogon  # type: ignore
from typer.main import get_group

# create a Typer object to support the command-line interface
cli = typer.Typer()


def confirm_valid_file(file: Path) -> bool:
    """Confirm that the provided file is a valid path that is a file."""
    # determine if the file is not None and if it is a file
    if file is not None:
        # the file is valid
        if file.is_file():
            return True
    # the file was either none or not valid
    return False


def confirm_valid_directory(directory: Path) -> bool:
    """Confirm that the provided directory is a valid path that is a directory."""
    # determine if the file is not None and if it is a file
    if directory is not None:
        # the file is valid
        if directory.is_dir():
            return True
    # the directory was either none or not valid
    return False


def human_readable_boolean(answer: bool) -> str:
    """Produce a human-readable Yes or No for a boolean value of True or False."""
    # the provided answer is true
    if answer:
        return "Yes"
    # the provided answer is false
    return "No"


def get_default_directory_list() -> List[Path]:
    """Return the default directory list that is the current working directory by itself."""
    default_directory_list = [Path(".")]
    return default_directory_list


@cli.command()
def tui(ctx: typer.Context):
    """Interatively define command-line arguments through a terminal user interface."""
    Trogon(get_group(cli), click_context=ctx).run()


@cli.command()
def search(
    directory: List[Path] = typer.Option(
        get_default_directory_list(),
        "--directory",
        "-d",
        help="One or more directories with Python code",
    )
) -> None:
    """Analyze the AST of all of the Python files found through recursive traversal of directories."""
    # create a console for rich text output
    console = Console()
    # add extra space after the command to run the program
    console.print()
    # collect all of the directories that are invalid
    invalid_directories = []
    for current_directory in directory:
        if not confirm_valid_directory(current_directory):
            invalid_directories.append(current_directory)
    # create the list of valid directories by removing the invalid ones
    valid_directories = list(set(directory) - set(invalid_directories))
    console.print(valid_directories)
    # search for the XML contents of an AST that match the provided
    # XPATH query using the search_python_file in search module of pyastgrep
    match_generator = pyastgrepsearch.search_python_files(
        paths=valid_directories,
        expression='.//FunctionDef[@name="classify"]/body//If[ancestor::If and not(parent::orelse)]',
    )
    # display debugging information about the contents of the match generator
    console.print(match_generator)
    for search_output in match_generator:
        console.print(search_output)
