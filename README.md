# 2jciebl_bu_ble_mqtt
A tool for sending measurement data from 2JCIE-BL to MQTT (for use in HomeAssistant, etc.)

## つかいかた
すべてを行う前に [OMRON](https://github.com/omron-devhub/2jciebl-bu-ble-raspberrypi/blob/master/README_ja.md) のドキュメントを読んで環境センサの設定をしておいてください。

デバイスのアドレスは以下の方法とかで調べてください。
```
sudo hciconfig hci0 down
sudo hciconfig hci0 up
sudo hcitool lescan
```

### 試しに実行
```
$ sudo apt -y install python3-paho-mqtt python3-bluez
$ python3 2jciebl_bu_ble_mqtt.py \
  -a 00:00:00:00:00:00,00:00:00:00:00:00 \
  -H localhost -p 1833 -u you -P password
```

`-a` オプションにカンマ区切りで複数のアドレスが指定できます。

### systemd conf のインストール

```
$ ./install.sh
```

インストール中に MQTT の ID, パスワードを聞かれるので入力すると `~/.2jciebl_bu_ble_mqtt` に保存されます。

### util/generate_ha_conf.py
`-a` オプションに与えるカンマ区切りのアドレスから Home Assistant 用の設定 yaml 断片を出力するだけのユーティリティです。2JCIE-BL 用のものしか用意していません。

## 注意
- Raspberry Pi 5 + Raspberry Pi OS + 2JCIE-BL でしか動作確認してないです。
  - 2JCIE-BU は持ってないのでよくわからないです
- このコードはだいたい chatgpt が書いてます。
