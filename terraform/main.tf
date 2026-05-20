# 1. Define the Cloud Provider
provider "aws" {
  region = "eu-north-1" # Change this if your AWS console is in a different region!
}

# 2. Fetch the latest Ubuntu 24.04 LTS Image dynamically
data "aws_ami" "ubuntu" {
  most_recent = true
  owners      = ["099720109477"] # Canonical's official AWS account ID

  filter {
    name   = "name"
    values = ["ubuntu/images/hvm-ssd-gp3/ubuntu-noble-24.04-amd64-server-*"]
  }
}

# 3. Create the DevSecOps Firewall (Security Group)
resource "aws_security_group" "iam_api_sg" {
  name        = "iam-api-production-sg"
  description = "Allow HTTP, HTTPS, and SSH traffic"

  # SSH for your terminal access
  ingress {
    from_port   = 22
    to_port     = 22
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"] 
  }

  # HTTP for Let's Encrypt challenges
  ingress {
    from_port   = 80
    to_port     = 80
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # HTTPS for secure API traffic
  ingress {
    from_port   = 443
    to_port     = 443
    protocol    = "tcp"
    cidr_blocks = ["0.0.0.0/0"]
  }

  # Allow the server to download updates and Docker images
  egress {
    from_port   = 0
    to_port     = 0
    protocol    = "-1"
    cidr_blocks = ["0.0.0.0/0"]
  }
}

# 4. Provision the EC2 Instance
resource "aws_instance" "iam_production_server" {
  ami           = data.aws_ami.ubuntu.id
  instance_type = "t3.micro"
  
  # IMPORTANT: Replace this with the exact name of your .pem key in AWS!
  key_name      = "iam-v2" 

  # Attach the firewall we created above
  vpc_security_group_ids = [aws_security_group.iam_api_sg.id]

  # Name the server in the AWS Console
  tags = {
    Name = "IAM-API-Production-Node"
    Environment = "Production"
  }
}

# 5. Output the new Public IP to your terminal automatically
output "server_public_ip" {
  value       = aws_instance.iam_production_server.public_ip
  description = "The public IP address of your new server. Paste this into DuckDNS!"
}
