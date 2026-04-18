#!/bin/bash

sudo apt update
sudo apt install python3 python3-pip python3-venv git -y

mkdir Data\ Engineering\ Projects
cd Data\ Engineering\ Projects

git clone https://github.com/jaspertot/1_weather_pipeline.git
cd 1_weather_pipeline

python3 -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

cat > .env << 'EOF'
OPEN_WEATHER_MAP_API_KEY=...
AWS_ACCESS_KEY_ID=...
AWS_SECRET_ACCESS_KEY=...
AWS_REGION=...
S3_BUCKET_NAME=...
SUPABASE_PROJECT_URL=...
SUPABASE_PUBLIC_KEY=...
EOF

ln -s "/home/ubuntu/Data Engineering Projects/1_weather_pipeline" /home/ubuntu/weather_pipeline

export AIRFLOW_HOME=/home/ubuntu/weather_pipeline/orchestration
echo 'export AIRFLOW_HOME=/home/ubuntu/weather_pipeline/orchestration' >> ~/.bashrc
source ~/.bashrc

cat > /home/ubuntu/weather_pipeline/orchestration/start_airflow_ec2.sh << 'EOF'

#!/bin/bash
export AIRFLOW_HOME=/home/ubuntu/weather_pipeline/orchestration
export PATH=/home/ubuntu/weather_pipeline/.venv/bin:$PATH
cd /home/ubuntu/weather_pipeline
source .venv/bin/activate
exec airflow standalone

EOF

chmod +x /home/ubuntu/weather_pipeline/orchestration/start_airflow_ec2.sh

sudo cat > /etc/systemd/system/airflow.service << 'EOF'
[Unit]
Description=Airflow Standalone
After=network.target

[Service]
User=ubuntu
WorkingDirectory=/home/ubuntu/weather_pipeline
Environment="AIRFLOW_HOME=/home/ubuntu/weather_pipeline/orchestration"
ExecStart=/bin/bash /home/ubuntu/weather_pipeline/orchestration/start_airflow_ec2.sh
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable airflow
sudo systemctl start airflow
sudo systemctl status airflow