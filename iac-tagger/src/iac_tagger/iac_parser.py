from abc import ABC, abstractmethod
from pathlib import Path
from typing import Dict, Optional, Any
import subprocess
import hashlib
import hcl2
import re
import json

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
    
    def generate_resource_hash(self,resource_content, iac_tagger_prefix="iac_tagger"):
        """
        Generate a consistent hash for Kubernetes/Terraform resources by ignoring specified tags/labels.
        
        Args:
            resource_content (str or dict): Resource content in HCL/K8s manifest (as a string) or a parsed dictionary.
            iac_tagger_prefix (str): The configurable prefix to identify and remove the tagger (default: "iac_tagger").
        
        Returns:
            str: A SHA256 hash of the cleaned resource content.
        """
        def clean_tags_and_labels(content, prefix):
            # Regex to match labels/tags with the specified prefix
            tagger_pattern = rf'["\']{prefix}["\']\s*:\s*["\'][^"\']+["\'],?'
            
            # Remove matching labels or tags
            content = re.sub(tagger_pattern, '', content)
            
            # Remove empty tag/label containers
            content = re.sub(r'["\'](tags|labels)["\']\s*:\s*{\s*}', '', content)
            content = re.sub(r'["\'](tags|labels)["\']\s*:\s*\[\s*\]', '', content)
            
            # Clean up artifacts (e.g., trailing commas or redundant spaces)
            content = re.sub(r',\s*}', '}', content)
            content = re.sub(r'\s+', '', content)
            content = re.sub(r',+', ',', content)
            
            return content

        if isinstance(resource_content, str):
            # Handle HCL or Kubernetes manifest as string
            # Remove "merge()" calls for Terraform
            cleaned_content = re.sub(
                r'tags\s*=\s*merge\([^)]+\)', 
                'tags = {}', 
                resource_content
            )
            
            # Remove standard tags in HCL (e.g., `tags = {}`)
            cleaned_content = re.sub(
                r'tags\s*=\s*{[^}]+}', 
                'tags = {}', 
                cleaned_content
            )
            
            # Apply the cleaning logic for tags/labels
            cleaned_content = clean_tags_and_labels(cleaned_content, iac_tagger_prefix)
            
            # Generate hash
            return hashlib.sha256(cleaned_content.encode()).hexdigest()
        
        elif isinstance(resource_content, dict):
            # Handle already parsed dictionary content (e.g., for Kubernetes manifests)
            json_content = json.dumps(resource_content, sort_keys=True, separators=(',', ':'))
            
            # Apply the cleaning logic for tags/labels
            cleaned_content = clean_tags_and_labels(json_content, iac_tagger_prefix)
            
            # Generate hash
            return hashlib.sha256(cleaned_content.encode()).hexdigest()
        
        else:
            raise TypeError("Resource content must be either a string or a dictionary.")

class TerraformParser(IaCParser):
    TAG_KEY = "iac_tagger"
    
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