from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any
import subprocess
import hashlib
import hcl2

class IaCParser(ABC):
    """Base abstract class for IaC parsers"""
    
    @abstractmethod
    def add_tracking_tag(self, file_path: Path, resource_id: str) -> bool:
        """Add tracking tag to resource if needed"""
        pass
    
    @abstractmethod
    def get_resources(self, file_path: Path) -> Dict[str, dict]:
        """Get all resources from the IaC file"""
        pass
    
    def get_last_commit(self, file_path: Path) -> str:
        """Get the last git commit that modified this file"""
        try:
            result = subprocess.run(
                ['git', 'log', '-n', '1', '--pretty=format:%H', str(file_path)],
                capture_output=True,
                text=True
            )
            return result.stdout.strip()
        except subprocess.CalledProcessError:
            return "no_git_history"
    
    def generate_resource_hash(self, content: str) -> str:
        """Generate a hash of the resource content"""
        return hashlib.sha256(content.encode()).hexdigest()[:8] 

class TerraformParser(IaCParser):
    TAG_KEY = "git_commit"
    
    def get_resources(self, file_path: Path) -> Dict[str, dict]:
        with open(file_path, 'r') as f:
            tf_dict = hcl2.load(f)
            
        resources = {}
        for block_type, blocks in tf_dict.items():
            if block_type == "resource":
                for resource in blocks:
                    for resource_type, resource_configs in resource.items():
                        for resource_name, config in resource_configs.items():
                            resource_id = f"{resource_type}.{resource_name}"
                            resources[resource_id] = config
        return resources
    
    def add_tracking_tag(self, file_path: Path, resource_id: str) -> bool:
        resources = self.get_resources(file_path)
        if resource_id not in resources:
            return False
            
        resource = resources[resource_id]
        current_hash = self.generate_resource_hash(str(resource))
        commit_hash = self.get_last_commit(file_path)
        
        # Check if tag already exists and is current
        if "tags" in resource:
            existing_tag = resource["tags"].get(self.TAG_KEY)
            if existing_tag == f"{resource_id}:{current_hash}:{commit_hash}":
                return False
                
        # Update the file with new tag
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Add or update tag
        new_tag = f'{resource_id}:{current_hash}:{commit_hash}'
        # Implementation of actual file modification would go here
        # This is a simplified version - you'd need proper HCL modification logic
        
        return True 