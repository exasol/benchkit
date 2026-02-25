#!/bin/bash

set -e

# Update system
apt-get update && apt-get upgrade -y

# Install Docker
apt-get install -y docker.io docker-compose
systemctl start docker
systemctl enable docker
usermod -aG docker ubuntu

# Install Python and development tools
apt-get install -y python3.10 python3-pip python3-venv build-essential git curl wget unzip zip

# Install storage tools (used by benchmark system classes for disk management)
apt-get install -y mdadm nvme-cli parted

# Install AWS CLI
curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip"
unzip awscliv2.zip
./aws/install
rm -rf aws awscliv2.zip

# Performance tuning
echo 'performance' > /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor 2>/dev/null || true

# Increase file descriptor limits
cat >> /etc/security/limits.conf << EOF
ubuntu soft nofile 65536
ubuntu hard nofile 65536
EOF

# Setup swap file (optional, only if needed)
if [ ! -f /swapfile ]; then
    fallocate -l 4G /swapfile
    chmod 600 /swapfile
    mkswap /swapfile
    swapon /swapfile
    echo '/swapfile none swap sw 0 0' >> /etc/fstab
fi

# Log completion
echo "$(date): User data script completed" >> /var/log/user-data.log
