"""Pytest test suite for the main module."""

import os
from pathlib import Path
from unittest.mock import patch

import pytest
from hypothesis import HealthCheck, given, settings, strategies
from typer.testing import CliRunner

from chasten import main

runner = CliRunner()


CONFIGURATION_FILE_DEFAULT_CONTENTS = """
# chasten configuration
# automatically created
chasten:
  # point to a checks file
  checks-file:
    - checks.yml
"""

CHECKS_FILE_DEFAULT_CONTENTS = """
checks:
  - name: "class-definition"
    code: "CDF"
    id: "C001"
    pattern: './/ClassDef'
  - name: "all-function-definition"
    code: "AFD"
    id: "F001"
    pattern: './/FunctionDef'
  - name: "non-test-function-definition"
    code: "NTF"
    id: "F002"
    pattern: './/FunctionDef[not(contains(@name, "test_"))]'
  - name: "single-nested-if"
    code: "SNI"
    id: "CL001"
    pattern: './/FunctionDef/body//If'
  - name: "double-nested-if"
    code: "DNI"
    id: "CL002"
    pattern: './/FunctionDef/body//If[ancestor::If and not(parent::orelse)]'
"""

CHECKS_FILE_DEFAULT_CONTENTS_GOTCHA = """
checks:
  - name: "class-definition"
    code: "CDF"
    id: "C001"
    pattern: './/ClassDef'
    count:
      min: 1
      max: null
  - name: "all-function-definition"
    code: "AFD"
    id: "F001"
    pattern: './/FunctionDef'
  - name: "non-test-function-definition"
    code: "NTF"
    id: "F002"
    pattern: './/FunctionDef[not(contains(@name, "test_"))]'
  - name: "single-nested-if"
    code: "SNI"
    id: "CL001"
    pattern: './/FunctionDef/body//If'
  - name: "double-nested-if"
    code: "DNI"
    id: "CL002"
    pattern: './/FunctionDef/body//If[ancestor::If and not(parent::orelse)]'
"""


@pytest.fixture
def cwd():
    """Define a test fixture for the current working directory."""
    return os.getcwd()


def test_cli_analyze_correct_arguments_nothing_to_analyze_not_looking(tmpdir):
    """Confirm that using the command-line interface does not crash: analyze command with correct arguments."""
    # create some temporary directories;
    # note that there is no code inside of this directory
    # and thus chasten does not actually have any
    # Python source code that it can analyze
    test_one = tmpdir.mkdir("test_one")
    # call the analyze command
    project_name = "testing"
    # create a reference to the internal
    # .chasten directory that supports testing
    configuration_directory = test_one / Path(".chasten")
    configuration_directory_path = Path(configuration_directory)
    configuration_directory_path.mkdir()
    configuration_file = configuration_directory_path / "config.yml"
    configuration_file.touch()
    configuration_file.write_text(CONFIGURATION_FILE_DEFAULT_CONTENTS)
    checks_file = configuration_directory_path / "checks.yml"
    checks_file.touch()
    checks_file.write_text(CHECKS_FILE_DEFAULT_CONTENTS)
    # filesystem.create_configuration_directory(configuration_directory_path, force=True)
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            project_name,
            "--search-path",
            test_one,
            "--config",
            configuration_directory,
            "--verbose",
        ],
    )
    assert result.exit_code == 0


def test_cli_analyze_correct_arguments_analyze_chasten_codebase(cwd):
    """Confirm that using the command-line interface does not crash: analyze command with correct arguments."""
    # call the analyze command
    project_name = "testing"
    # create a reference to the internal
    # .chasten directory that supports testing
    configuration_directory = cwd / Path(".chasten")
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            "--search-path",
            cwd,
            project_name,
            "--config",
            configuration_directory,
            "--verbose",
        ],
    )
    assert result.exit_code == 0


def test_cli_analyze_incorrect_arguments_no_project(cwd, tmpdir):
    """Confirm that using the command-line interface does not crash: analyze command incorrect arguments."""
    # create some temporary directories
    test_one = tmpdir.mkdir("test_one")
    # create a reference to the internal
    # .chasten directory that supports testing
    configuration_directory = cwd / Path(".chasten")
    # call the analyze command
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            "--search-path",
            test_one,
            "--config",
            configuration_directory,
            "--verbose",
        ],
    )
    # crashes because the command-line arguments are wrong
    assert result.exit_code != 0
    assert "Missing argument" in result.output


def test_cli_analyze_incorrect_arguments_wrong_config(tmpdir):
    """Confirm that using the command-line interface does return non-zero: analyze command incorrect arguments."""
    # create some temporary directories
    test_one = tmpdir.mkdir("test_one")
    project_name = "test"
    # create a configuration directory
    # that does not currently exist
    wrong_config_dir = "config"
    # call the analyze command
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            project_name,
            "--search-path",
            test_one,
            "--config",
            wrong_config_dir,
            "--verbose",
        ],
    )
    assert result.exit_code == 1
    assert "Cannot perform analysis due to configuration" in result.output


def test_cli_analyze_incorrect_arguments_wrong_source_directory(tmpdir):
    """Confirm that using the command-line interface does return non-zero: analyze command incorrect arguments."""
    # create some temporary directories
    _ = tmpdir.mkdir("test_one")
    test_one_incorrect_name = "test_oneFF"
    project_name = "test"
    # create a configuration directory
    # that does not currently exist
    wrong_config_dir = "config"
    # call the analyze command
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            project_name,
            "--search-path",
            test_one_incorrect_name,
            "--config",
            wrong_config_dir,
            "--verbose",
        ],
    )
    # running the program with an invalid --search-path
    # should not work and thus a zero exit code is wrong
    assert result.exit_code != 0
    # note the error code of 2 indicates that it was
    # an error arising from the fact that typer could
    # not validate that test_oneFF is a existing directory
    assert result.exit_code == 2  # noqa
    assert "Usage:" in result.output


def test_cli_analyze_incorrect_arguments_correct_config(tmpdir):
    """Confirm that using the command-line interface does return non-zero due to no config files: analyze command correct arguments."""
    # create some temporary directories
    test_one = tmpdir.mkdir("test_one")
    project_name = "test"
    # create a configuration directory
    # that does currently exist
    correct_config_dir = tmpdir.mkdir("config")
    # call the analyze command
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            project_name,
            "--search-path",
            test_one,
            "--config",
            correct_config_dir,
            "--verbose",
        ],
    )
    assert result.exit_code == 1
    assert "Cannot perform analysis due to configuration" in result.output


@patch("chasten.configuration.user_config_dir")
def test_cli_configure_create_config_when_does_not_exist(
    mock_user_config_dir, tmp_path
):
    """Confirm that using the command-line interface does create .config directory when it does not exist."""
    # monkeypatch the platformdirs user_config_dir to always return
    # the tmpdir test fixture that is controlled by Pytest; the
    # directory inside of that will be ".chasten" by default
    mock_user_config_dir.return_value = str(tmp_path / ".chasten")
    # call the configure command
    result = runner.invoke(
        main.cli,
        [
            "configure",
            "create",
            "--verbose",
        ],
    )
    assert result.exit_code == 0


@patch("chasten.configuration.user_config_dir")
def test_cli_configure_cannot_create_config_when_does_exist(
    mock_user_config_dir, tmp_path
):
    """Confirm that using the command-line interface does create .config directory when it does exist."""
    # monkeypatch the platformdirs user_config_dir to always return
    # the tmpdir test fixture that is controlled by Pytest; the
    # directory inside of that will be ".chasten" by default
    mock_user_config_dir.return_value = str(tmp_path / ".chasten")
    config_directory = Path(tmp_path / ".chasten")
    config_directory.mkdir()
    assert config_directory.exists()
    # call the configure command
    result = runner.invoke(
        main.cli,
        [
            "configure",
            "create",
            "--verbose",
        ],
    )
    assert result.exit_code == 1


@given(directory=strategies.builds(Path))
@settings(deadline=None, suppress_health_check=[HealthCheck.function_scoped_fixture])
@pytest.mark.fuzz
def test_fuzz_cli_analyze_single_directory(cwd, directory):
    """Confirm that the function does not crash when called through the command-line interface."""
    project_name = "testing"
    # create a reference to the internal
    # .chasten directory that supports testing
    configuration_directory = cwd / Path(".chasten")
    result = runner.invoke(
        main.cli,
        [
            "analyze",
            project_name,
            "--config",
            configuration_directory,
            "--search-path",
            str(directory),
        ],
    )
    assert result.exit_code == 0
