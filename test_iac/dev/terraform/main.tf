provider "aws" {
  region = "us-west-2"
}

resource "aws_instance" "web" {
  ami           = "ami-0c55b159cbfafe1f0"
  instance_type = "t2.micro"

  tags = {
    Name = "dev-web-server"
    Environment = "dev"
  }
}

resource "aws_s3_bucket" "data" {
  bucket = "my-dev-data-bucket"

  tags = {
    Environment = "dev"
  }
} 