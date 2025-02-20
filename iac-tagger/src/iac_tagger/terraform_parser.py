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
    def parse_and_split_merge_input(self,input_string):
        """
        Parses a Terraform merge input string and splits it into base_tags and dynamic_tags.

        Args:
            input_string (str): Terraform-style merge input.

        Returns:
            tuple: Two Python dictionaries, base_tags and dynamic_tags.
        """
        # Use regex to identify the two blocks inside the merge
        matches = re.findall(r"merge\((\{.*?\}),\s*(\{.*?\})\)", input_string, re.DOTALL)
        if not matches:
            raise ValueError("Input string does not match the expected Terraform merge pattern.")
        
        # Extract base_tags and dynamic_tags from the matches
        base_tags_str, dynamic_tags_str = matches[0]
        
        # Convert Terraform-style dictionaries into Python dictionaries
        def terraform_to_python_dict(terraform_dict):
            terraform_dict = terraform_dict.replace("${local.resource_prefix.value}", "resource_prefix_value")
            terraform_dict = terraform_dict.replace("=", ":")
            terraform_dict = terraform_dict.replace("\"", "'")
            return eval(terraform_dict)
        
        base_tags = terraform_to_python_dict(base_tags_str)
        dynamic_tags = terraform_to_python_dict(dynamic_tags_str)
        
        return base_tags, dynamic_tags

    def update_tags(self, resource_block, new_tag):
        if 'tags' in resource_block:
            # Check if it's a merge format
            if 'merge(' in resource_block:
                # Match and extract the base and dynamic tag dictionaries
                match = re.search(r'tags\s*=\s*merge\((.*?),\s*(\{.*?\})\)', resource_block, re.DOTALL)
                if match:
                    base_tags = match.group(1).strip()
                    dynamic_tags = match.group(2).strip()

                    # Update or add the TAG_KEY in the dynamic tags
                    if self.TAG_KEY in dynamic_tags:
                        # Update existing TAG_KEY
                        modified_dynamic_tags = re.sub(
                            rf'"?{self.TAG_KEY}"?\s*=\s*"[^"]*"',
                            f'{self.TAG_KEY} = "{new_tag}"',
                            dynamic_tags
                        )
                    else:
                        # Add new TAG_KEY without modifying existing structure
                        modified_dynamic_tags = re.sub(
                            r'(\{)(.*?)(\})',
                            rf'\1\2  {self.TAG_KEY} = "{new_tag}"\n  \3',
                            dynamic_tags,
                            flags=re.DOTALL
                        )

                    # Rebuild the merge block without altering existing formatting
                    modified_block = re.sub(
                        r'tags\s*=\s*merge\((.*?),\s*(\{.*?\})\)',
                        f'tags = merge({base_tags}, {modified_dynamic_tags})',
                        resource_block,
                        flags=re.DOTALL
                    )

                    return modified_block
            else:
                # Handle plain tags = { ... } format
                # Ensure proper indentation for new tags
                modified_block = re.sub(
                    rf'(tags\s*=\s*\{{[^}}]*)"?{self.TAG_KEY}"?\s*=\s*"[^"]*"',
                    f'\\1{self.TAG_KEY} = "{new_tag}"',
                    resource_block
                )
                if modified_block == resource_block:  # If tag wasn't found, add it
                    modified_block = re.sub(
                        r'(tags\s*=\s*\{[^\}]*)}',
                        rf'\1  {self.TAG_KEY} = "{new_tag}"\n  }}',
                        resource_block,
                        flags=re.DOTALL
                    )
                return modified_block
        else:
            # Add new tags block
            modified_block = resource_block.rstrip('}') + '\n  tags = {\n    ' + f'{self.TAG_KEY} = "{new_tag}"\n  }}\n'             
            return modified_block
        return resource_block

    def add_tracking_tag(self, file_path: Path, resource_id: str) -> bool:
        resources = self.get_resources(file_path)
        if resource_id not in resources:
            return False
            
        resource = resources[resource_id]
        current_hash = self.generate_resource_hash(str(resource), self.TAG_KEY)
        commit_hash = self.get_last_commit(file_path)

        
        # Check if tag already exists and is current
        if "tags" in resource:

            if isinstance(resource["tags"], str):
                base_tags, dynamic_tags = self.parse_and_split_merge_input(resource["tags"])
                existing_tag = base_tags.get(self.TAG_KEY)
            else:
                existing_tag = resource["tags"].get(self.TAG_KEY)
            if existing_tag == f"{resource_id}:{current_hash}:{commit_hash}":
                return False
                
        # Update the file with new tag
        with open(file_path, 'r') as f:
            content = f.read()
            
        # Add or update tag
        new_tag = f'{resource_id}:{current_hash}:{commit_hash}'
        
        # Find the resource block and add/update the tag
        resource_pattern = fr'resource\s+(?:"|){resource_id.split(".")[0]}(?:"|)\s+"{resource_id.split(".")[1]}"'
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
            
            modified_block = self.update_tags(resource_block, new_tag)
            # Write the modified content back to file
            new_content = content[:start_pos] + modified_block + content[end_pos:]
            with open(file_path, 'w') as f:
                f.write(new_content)
        
        return True 