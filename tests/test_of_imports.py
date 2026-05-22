import pathlib
import sys
import importlib.util


def test_import_all_modules() -> None:
    """
    Import all .py files in the "src" folder or subdirectories in "src".

    The purpose of this function is that Pytest can catch
    any ImportError, SyntaxError or RuntimeError.
    """

    # Ensure src is importable.
    working_directory = pathlib.Path(__file__).parent.parent
    src_folder = working_directory / "src"
    sys.path.insert(0, str(src_folder))

    # Check each .py file in "src".
    for file in src_folder.rglob("*.py"):
        # Make a unique module name based on relative path
        relative_path = file.relative_to(src_folder)
        module_name = "_".join(relative_path.parts).replace(".py", "")

        try:
            spec = importlib.util.spec_from_file_location(module_name, file)
            module = importlib.util.module_from_spec(spec)  # type: ignore
            spec.loader.exec_module(module)  # type: ignore
        except Exception as e:
            raise AssertionError(f"Failed to import {file}") from e

    return None
