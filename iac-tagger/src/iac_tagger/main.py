import argparse
from pathlib import Path
from typing import Dict, Type, List, Iterator, Optional
from iac_tagger.iac_parser import IaCParser
from iac_tagger.terraform_parser import TerraformParser
from iac_tagger.kubernetes_parser import KubernetesParser

class IaCTagger:
    def __init__(self):
        self.parsers: Dict[str, Type[IaCParser]] = {
            '.tf': TerraformParser(),
            '.yaml': KubernetesParser(),
            '.yml': KubernetesParser(),
        }
        
    def process_file(self, file_path: str) -> bool:
        path = Path(file_path)
        if not path.exists():
            raise FileNotFoundError(f"File {file_path} not found")
            
        parser = self._get_parser(path)
        if not parser:
            raise ValueError(f"No parser found for file type: {path.suffix}")
            
        resources = parser.get_resources(path)
        modified = False
        
        for resource_id in resources:
            if parser.add_tracking_tag(path, resource_id):
                modified = True
                
        return modified
    
    def _get_parser(self, file_path: Path) -> Optional[IaCParser]:
        for suffix, parser in self.parsers.items():
            if str(file_path).endswith(suffix):
                return parser
        return None
    
    def get_supported_extensions(self) -> List[str]:
        """Return list of supported file extensions"""
        return list(self.parsers.keys())
    
    def process_directory(self, directory_path: str, recursive: bool = False) -> Dict[str, bool]:
        """
        Process all supported files in a directory
        Returns dict of {filepath: was_modified}
        """
        path = Path(directory_path)
        if not path.is_dir():
            raise NotADirectoryError(f"{directory_path} is not a directory")
            
        results = {}
        
        # Get all files with supported extensions
        pattern = "**/*" if recursive else "*"
        for ext in self.get_supported_extensions():
            for file_path in path.glob(f"{pattern}{ext}"):
                try:
                    results[str(file_path)] = self.process_file(str(file_path))
                except Exception as e:
                    results[str(file_path)] = f"Error: {str(e)}"
                    
        return results

def main():
    parser = argparse.ArgumentParser(
        description="Add git commit tracking tags/labels to IaC files"
    )
    
    # Create mutually exclusive group for files vs directory
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "-f", "--files",
        nargs="+",
        help="Path to IaC file(s) to process"
    )
    input_group.add_argument(
        "-d", "--directory",
        help="Process all supported files in directory"
    )
    
    # Additional options
    parser.add_argument(
        "-r", "--recursive",
        action="store_true",
        help="Recursively process directories (only with -d option)"
    )
    parser.add_argument(
        "-v", "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Show what would be processed without making changes"
    )
    
    args = parser.parse_args()
    tagger = IaCTagger()
    
    try:
        if args.directory:
            if args.dry_run:
                # Just show what files would be processed
                path = Path(args.directory)
                pattern = "**/*" if args.recursive else "*"
                print(f"Would process the following files in {args.directory}:")
                for ext in tagger.get_supported_extensions():
                    for file_path in path.glob(f"{pattern}{ext}"):
                        print(f"  {file_path}")
                return
                
            results = tagger.process_directory(args.directory, args.recursive)
            for file_path, result in results.items():
                if args.verbose or isinstance(result, str):  # Always show errors
                    if isinstance(result, bool):
                        status = "modified" if result else "unchanged"
                    else:
                        status = result  # This is an error message
                    print(f"File {file_path}: {status}")
                    
        else:  # Processing individual files
            if args.dry_run:
                print("Would process the following files:")
                for file_path in args.files:
                    print(f"  {file_path}")
                return
                
            for file_path in args.files:
                try:
                    modified = tagger.process_file(file_path)
                    if args.verbose:
                        status = "modified" if modified else "unchanged"
                        print(f"File {file_path}: {status}")
                except Exception as e:
                    print(f"Error processing {file_path}: {e}")
                    
    except Exception as e:
        print(f"Error: {e}")
        parser.print_help()
        exit(1)

if __name__ == "__main__":
    main() 