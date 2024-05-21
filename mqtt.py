import os
import json
import logging
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# 設置日誌級別
logging.basicConfig(level=logging.INFO)

load_dotenv()

mqtt_broker_url = os.getenv('MQTT_BROKER_URL')
mqtt_broker_port = int(os.getenv('MQTT_BROKER_PORT'))
mqtt_topic = os.getenv('MQTT_TOPIC')
mqtt_username = os.getenv('MQTT_USERNAME')
mqtt_password = os.getenv('MQTT_PASSWORD')

# MQTT 回調函數
def on_message(client, userdata, message):
    try:
        # 將字節串消息解碼為字符串
        message_str = message.payload.decode('utf-8')
        print(f"Received message from topic {message.topic}: {message_str}")

        # 解析 JSON 數據
        data = json.loads(message_str)

    except json.JSONDecodeError:
        logging.error("Received message is not a valid JSON: %s", message_str)
    except Exception as e:
        logging.error("Error in on_message: %s", e)
        

    
# MQTT 客戶端類別改名為 MQTT_Client
MQTT_Client = mqtt.Client

# 設定 MQTT 客戶端並連接到服務器
mqtt_client = MQTT_Client(mqtt.CallbackAPIVersion.VERSION2)
mqtt_client.username_pw_set(mqtt_username, password=mqtt_password)  # 設定用戶名和密碼
mqtt_client.on_message = on_message
try:
    mqtt_client.connect(mqtt_broker_url, mqtt_broker_port)
except Exception as e:
    print("Error connecting to MQTT broker: %s", e)
    logging.error("Error connecting to MQTT broker: %s", e)

# 開始監聽指定的 MQTT 主題
mqtt_client.subscribe(mqtt_topic)
mqtt_client.loop_start()

# 程式將持續運行，直到手動停止
try:
    while True:
        # 可以在這裡添加一些代碼來執行其他任務，如果需要的話
        pass
except KeyboardInterrupt:
    print("程式被手動中斷")
    mqtt_client.loop_stop()
