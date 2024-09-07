#!/bin/bash
echo `pwd`

# 変数設定
SERVICE_NAME="2jciebl_bu_ble_mqtt"
BINARY_PATH="/usr/local/bin/$SERVICE_NAME.py"
WORK_DIR=`pwd`
ORIGINAL_PATH="$WORK_DIR/$SERVICE_NAME.py"
SERVICE_FILE="/etc/systemd/system/$SERVICE_NAME.service"
ENV_FILE="$HOME/.$SERVICE_NAME.env"
CURRENT_USER=`whoami`

# 1. ユーザー名とパスワードの入力
read -p "Enter MQTT username: " USER
read -sp "Enter MQTT password: " PASSWORD
echo

# 2. 環境ファイルの作成
echo "Creating environment file..."
sudo tee $ENV_FILE > /dev/null <<EOL
MQTT_USERNAME=$USER
MQTT_PASSWORD=$PASSWORD
EOL


read -p "Enter 2JCIE-BL Adresses (comma separated): " ADDRESSES

# 環境ファイルのパーミッション設定
sudo chmod 600 $ENV_FILE
sudo chown root:root $ENV_FILE

# 3. python file を /usr/local/bin にコピー
echo "Copying binary to /usr/local/bin..."
sudo cp $ORIGINAL_PATH $BINARY_PATH
if [ $? -ne 0 ]; then
    echo "Failed to copy binary to $BINARY_PATH."
    exit 1
fi

# 4. systemd サービスファイルの作成
echo "Creating systemd service file..."
sudo tee $SERVICE_FILE > /dev/null <<EOL
[Unit]
Description=$SERVICE_NAME Service
After=network.target

[Service]
EnvironmentFile=$ENV_FILE
ExecStart=python3 $BINARY_PATH -a $ADDRESSES
WorkingDirectory=$WORK_DIR
Restart=always
RestartSec=5
StandardOutput=journal
StandardError=journal
User=root

[Install]
WantedBy=multi-user.target
EOL

# 6. サービスの有効化と起動
echo "Reloading systemd daemon..."
sudo systemctl daemon-reload

echo "Enabling $SERVICE_NAME service..."
sudo systemctl enable $SERVICE_NAME.service

echo "Starting $SERVICE_NAME service..."
sudo systemctl start $SERVICE_NAME.service

# 7. サービスの状態確認
sudo systemctl status $SERVICE_NAME.service

echo "Installation complete."
