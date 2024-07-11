from pathlib import Path
from typing import List
from pprint import pprint
from loguru import logger


class PythonProject:
    """
    A class to represent a Python project and manage paths relative to the project root.
    
    Attributes:
        markers (list): A list of filenames or directory names that indicate the project root.
        root (Path): The root directory of the project.
    """
    
    markers: list
    root: Path
    root_marker: str

    def __init__(self, markers: list = ['pyproject.toml', 'requirements.txt', '.git']):
        """
        Constructs all the necessary attributes for the PythonProject object.
        
        :param markers: A list of filenames or directory names to look for when identifying the project root.
        """
        self.root_marker = None
        self.markers = markers
        self.root = self.get_root(Path(__file__))
        logger.info(f"Project Root: {self.root}")

    def get_root(self, start_path: Path) -> Path:
        """
        Traverse up from the start_path to find the project root directory based on the presence of markers.
        Set self.root_marker to the first marker found during the search.

        :param start_path: The starting Path object, usually `Path(__file__)`.
        :return: The Path object corresponding to the project root.
        :raises FileNotFoundError: If the project root cannot be found based on the markers.
        """
        current_path = start_path.resolve()
        while current_path != current_path.parent:
            for marker in self.markers:
                if (current_path / marker).exists():
                    self.root_marker = marker
                    logger.info(f"File {self.root_marker} used to identify project root")
                    return current_path
            current_path = current_path.parent
        raise FileNotFoundError(f"Project root not found. None of the markers {self.markers} detected.")

    def get_relative_path(self, target_path: str) -> Path:
        """
        Get a path relative to the project root.
        
        :param target_path: The relative path from the project root.
        :return: The absolute Path object of the target path.
        """
        target = self.root / target_path
        if not target.exists():
            logger.warning(f"{target} does not exist in project")
        return target

    def is_path_in_project(self, path: str) -> bool:
        """
        Check if a path (file or directory) exists within the project structure.
        
        :param path: The relative path from the project root.
        :return: True if the path exists, False otherwise.
        """
        return (self.root / path).exists()

    def is_file_in_project(self, file_path: str) -> bool:
        """
        Check if a file exists within the project structure.
        
        :param file_path: The relative file path from the project root.
        :return: True if the file exists, False otherwise.
        """
        return (self.root / file_path).is_file()

    def is_directory_in_project(self, dir_path: str) -> bool:
        """
        Check if a directory exists within the project structure.
        
        :param dir_path: The relative directory path from the project root.
        :return: True if the directory exists, False otherwise.
        """
        return (self.root / dir_path).is_dir()
    
    def list_files_in_directory(self, dir_path: str) -> List[str]:
        """
        List all files in a directory within the project structure.
        
        :param dir_path: The relative directory path from the project root.
        :return: A list of filenames in the specified directory.
        """
        directory = self.root / dir_path
        if directory.is_dir():
            return [file.name for file in directory.iterdir() if file.is_file()]
        else:
            logger.warning(f"{directory} is not a valid directory in the project.")
            return []
        
    def list_directories_in_directory(self, dir_path: str) -> List[str]:
        """
        List all directories in a directory within the project structure.
        
        :param dir_path: The relative directory path from the project root.
        :return: A list of directory names in the specified directory.
        """
        directory = self.root / dir_path
        if directory.is_dir():
            return [dir.name for dir in directory.iterdir() if dir.is_dir()]
        else:
            logger.warning(f"{directory} is not a valid directory in the project.")
            return []

if __name__ == "__main__":
    try:
        project = PythonProject()

        src_script_path = project.get_relative_path('src/other/script.py')
        print(f"Script Path: {src_script_path}")
        print(f"Is 'src' a directory in {project.root}? {project.is_directory_in_project('src')}")
        print(f"Is 'main.py' a file in {project.root}? {project.is_file_in_project('main.py')}")
        print(f"Reference relative path in {project.root} - {project.get_relative_path('total_garbage.py')}")
        print(f"Is 'notebooks' a directory in {project.root}? {project.is_directory_in_project('notebooks')}")
        pprint(f"Directories in project root:\n {project.list_directories_in_directory('.')}")
        pprint(f"Files in 'src':\n {project.list_files_in_directory('src')}")


    except FileNotFoundError as e:
        logger.error(e)