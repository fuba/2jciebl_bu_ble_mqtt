# 2jciebl_bu_ble_mqtt
A tool for sending measurement data from 2JCIE-BL to MQTT (for use in HomeAssistant, etc.)

## つかいかた
すべてを行う前に 2JCIE-BL の Beacon Mode を設定してください。ただし、[OMRON のサンプル手順](https://github.com/omron-devhub/2jciebl-bu-ble-raspberrypi/blob/master/README_ja.md) にある `0x04 General Broadcaster 2` は常時アドバタイズするため、電池運用には向きません。

### 2JCIE-BL の省電力設定

このツールでは、同じ `EP` データ形式を間欠送信する `0x05 Limited Broadcaster 2` を推奨します。各フィールドの仕様は [2JCIE-BL01 Communication Interface Manual](https://omronmicrodevices.github.io/products/2jcie-bl01/communication_if_manual.html) を参照してください。スマートフォンの BLE Scanner などで次の Characteristic に値を書き込みます。

- Measurement interval: `0C4C3011-7700-46F4-AA96D5E974E32A54`
- ADV setting: `0C4C3042-7700-46F4-AA96D5E974E32A54`

10 分ごとに計測し、各周期のうち 10 秒だけ送信する例です。

```
Measurement interval (0x3011): 5802
ADV setting          (0x3042): 0808a0000a004e020500
```

`0x3042` の 10 バイトは、順に ADV 間隔（1285 ms）、未使用の ADV_NONCON_IND 間隔、送信期間（10 秒）、休止期間（590 秒）、Beacon Mode（`0x05`）、Tx Power（0 dBm）です。複数バイトの数値は little-endian です。書き込み後は電池を抜き差しして power cycle してください。

別の周期にしたい場合は、付属のユーティリティで値を生成できます。

```
$ python3 util/generate_bl_settings.py --measurement-interval 600 --cycle 600
```

受信側は常時起動しておいてください。Limited Broadcaster は休止期間中に見えなくなるのが正常です。このツールはデフォルトで passive scan を使い、送信窓で届いた `EP` パケットを受信します。

電池寿命は設置環境、電波状況、計測周期、送信出力、電池によって変わります。[メーカー公称値](https://omronfs.omron.com/en_US/ecb/products/pdf/CDSC-010B.pdf) は「5 分計測・1 日 1 回接続」で約 6 か月なので、1 年は保証できません。1 年を狙う場合は 10～15 分以上の計測周期から実測評価してください。

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
