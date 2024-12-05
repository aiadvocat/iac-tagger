import hcl2
from pathlib import Path
from typing import Dict, Any
from .iac_parser import IaCParser
import re

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
        
        # Find the resource block and add/update the tag
        resource_pattern = fr'resource\s+"{resource_id.split(".")[0]}"\s+"{resource_id.split(".")[1]}"'
        resource_match = re.search(resource_pattern, content)
        
        if resource_match:
            # Find the closing brace of the resource block
            start_pos = resource_match.start()
            brace_count = 0
            end_pos = start_pos
            
            for i in range(start_pos, len(content)):
                if content[i] == '{':
                    brace_count += 1
                elif content[i] == '}':
                    brace_count -= 1
                    if brace_count == 0:
                        end_pos = i
                        break
            
            resource_block = content[start_pos:end_pos]
            
            # Check if tags block exists
            if 'tags' in resource_block:
                # Update existing tags block
                modified_block = re.sub(
                    r'(tags\s*=\s*{[^}]*)"?' + self.TAG_KEY + r'"?\s*=\s*"[^"]*"',
                    f'\\1{self.TAG_KEY} = "{new_tag}"',
                    resource_block
                )
                if modified_block == resource_block:  # If tag wasn't found, add it
                    modified_block = re.sub(
                        r'(tags\s*=\s*{[^}]*)}',
                        f'\\1  {self.TAG_KEY} = "{new_tag}"\n  }}',
                        resource_block
                    )
            else:
                # Add new tags block
                modified_block = resource_block.rstrip('}') + '\n  tags = {\n    ' + f'{self.TAG_KEY} = "{new_tag}"\n  }}\n}}'
            
            # Write the modified content back to file
            new_content = content[:start_pos] + modified_block + content[end_pos:]
            with open(file_path, 'w') as f:
                f.write(new_content)
        
        return True 