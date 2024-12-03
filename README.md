# IAC Tagger

A tool for automatically tagging Infrastructure as Code (IaC) resources with Git commit information.

## Overview

IAC Tagger helps track the relationship between infrastructure resources and their defining code by automatically adding Git commit information as tags. Currently supports:
- Terraform resources
- Kubernetes manifests

## Installation

```
pip install iac-tagger
```

## Usage

```
# Tag all IaC resources in the current directory
iac-tagger .

# Tag resources in a specific directory
iac-tagger path/to/iac/files

# Specify custom tag key (default is 'GitCommit')
iac-tagger . --tag-key CustomGitTag
```

## How It Works

The tool:
1. Scans the specified directory for IaC files (`.tf`, `.yaml`, `.yml`)
2. Calculates a hash of each resource's configuration
3. Retrieves the latest Git commit information
4. Adds or updates tags in the format: `resource_id:config_hash:commit_hash`

## Supported Resources

### Terraform
- AWS resources
- Azure resources
- GCP resources

Example of a tagged Terraform resource:
```
resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name      = "web-server"
    git-commit = "aws_instance.web:a1b2c3:d4e5f6"
  }
}
```

### Kubernetes
- All resource types that support labels/annotations

Example of a tagged Kubernetes resource:
```
apiVersion: v1
kind: Pod
metadata:
  name: nginx
  labels:
    app: nginx
    git-commit: "pod/nginx:a1b2c3:d4e5f6"
```

## Requirements

- Python 3.7+
- Git repository
- Required Python packages:
  - setuptools
  - pyyaml
  - hcl2

## Development Setup

1. Clone the repository:
```
git clone https://github.com/yourusername/iac-tagger.git
cd iac-tagger
```

2. Create a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install development dependencies:
```
pip install -e ".[dev]"
```

## Troubleshooting

### Common Issues

1. **Git Repository Not Found**
   - Ensure you're running the tool within a Git repository
   - Check that `.git` directory exists

2. **Permission Denied**
   - Verify write permissions on IaC files
   - Run with appropriate permissions

3. **Parser Errors**
   - Ensure valid HCL syntax for Terraform files
   - Verify YAML formatting for Kubernetes manifests

## CI/CD Status

[![Build Status](https://github.com/yourusername/iac-tagger/workflows/CI/badge.svg)](https://github.com/yourusername/iac-tagger/actions)
[![Coverage Status](https://coveralls.io/repos/github/yourusername/iac-tagger/badge.svg?branch=main)](https://coveralls.io/github/yourusername/iac-tagger?branch=main)
[![PyPI version](https://badge.fury.io/py/iac-tagger.svg)](https://badge.fury.io/py/iac-tagger)

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the LICENSE file for details.

