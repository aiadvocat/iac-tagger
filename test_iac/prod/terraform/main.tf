provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.large"

  tags = {
    Name = "prod-web-server"
    Environment = "prod"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-prod-data-bucket"

  tags = {
    Environment = "prod"
  }
} 