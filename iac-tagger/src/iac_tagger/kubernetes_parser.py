import yaml
from pathlib import Path
from typing import Dict, Any
from iac_tagger.iac_parser import IaCParser
from abc import ABC, abstractmethod

class KubernetesParser(IaCParser):
    LABEL_KEY = "iac_tagger"
    
    def get_resources(self, file_path: Path) -> Dict[str, dict]:
        with open(file_path, 'r') as f:
            # Handle multi-document YAML files
            documents = list(yaml.safe_load_all(f))
            
        resources = {}
        for doc in documents:
            if not doc or not isinstance(doc, dict):
                continue
                
            kind = doc.get('kind', '')
            name = doc.get('metadata', {}).get('name', '')
            namespace = doc.get('metadata', {}).get('namespace', 'default')
            
            if kind and name:
                resource_id = f"{kind.lower()}.{namespace}.{name}"
                resources[resource_id] = doc
                
        return resources
    
    def add_tracking_label(self, file_path: Path, resource_id: str) -> bool:
        with open(file_path, 'r') as f:
            documents = list(yaml.safe_load_all(f))
            
        modified = False
        for doc in documents:
            if not doc or not isinstance(doc, dict):
                continue
                
            kind = doc.get('kind', '')
            name = doc.get('metadata', {}).get('name', '')
            namespace = doc.get('metadata', {}).get('namespace', 'default')
            current_resource_id = f"{kind.lower()}.{namespace}.{name}"
            
            if current_resource_id == resource_id:
                current_hash = self.generate_resource_hash(str(doc))
                commit_hash = self.get_last_commit(file_path)
                new_label = f"{resource_id}:{current_hash}:{commit_hash}"
                
                # Initialize metadata and labels if they don't exist
                if 'metadata' not in doc:
                    doc['metadata'] = {}
                if 'labels' not in doc['metadata']:
                    doc['metadata']['labels'] = {}
                
                # Check if label already exists and is current
                existing_label = doc['metadata']['labels'].get(self.LABEL_KEY)
                if existing_label != new_label:
                    doc['metadata']['labels'][self.LABEL_KEY] = new_label
                    modified = True
        
        if modified:
            # Write back to file while preserving formatting
            with open(file_path, 'w') as f:
                yaml.dump_all(documents, f, default_flow_style=False, sort_keys=False)
                
        return modified
    
    def add_tracking_tag(self, file_path: Path, resource_id: str) -> bool:
        """Implement the abstract method but use add_tracking_label instead"""
        return self.add_tracking_label(file_path, resource_id) 