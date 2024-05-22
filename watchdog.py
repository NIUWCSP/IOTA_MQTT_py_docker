import os
import json
import logging
from datetime import datetime
from dotenv import load_dotenv
import paho.mqtt.client as mqtt

# 設置日誌級別
logging.basicConfig(level=logging.INFO)

# 加載環境變量
load_dotenv()

# 獲取環境變量
mqtt_broker_url = os.getenv('MQTT_BROKER_URL')
mqtt_broker_port = int(os.getenv('MQTT_BROKER_PORT'))
mqtt_topic = os.getenv('MQTT_TOPIC')
mqtt_username = os.getenv('MQTT_USERNAME')
mqtt_password = os.getenv('MQTT_PASSWORD')

# 創建BLOCK_URL空的dictionary
block_url_dic = dict()

# 定義 MQTT 回調函數
def on_message(client, userdata, message):
    try:
        # 將字節串消息解碼為字符串
        message_str = message.payload.decode('utf-8')
        #print(f"Received message from topic {message.topic}: {message_str}")

        # 從主題名稱中提取 'tag' 和 'key'
        parts = message.topic.split('/')
        if len(parts) < 3:
            logging.warning(f"Invalid topic structure: {message.topic}")
            return
        tag, key = parts[1], parts[2]
        #print(f"tag:{tag},key:{key}")

        # 如果 'key' 包含 'BLOCK_URL'，則保存消息
        if 'BLOCK_URL' in key:
            try:
                message_content = json.loads(message_str)
                #print(f"Received message from topic {message.topic}: {message_str}")
            except json.JSONDecodeError:
                message_content = message_str
                print(f"Received message from topic {message.topic}: {message_str}")
                
            # 添加 tag 和當前時間到消息
            current_time = datetime.utcnow().isoformat()            
            block_url_dic[tag] = current_time
            
            print(f"block_url_dic: {block_url_dic}")
            
            
    except Exception as e:
        logging.error("Error in on_message: %s", e)

# 初始化 MQTT 客戶端
mqtt_client = mqtt.Client()
mqtt_client.username_pw_set(mqtt_username, mqtt_password)
mqtt_client.on_message = on_message

# 連接到 MQTT Broker
try:
    mqtt_client.connect(mqtt_broker_url, mqtt_broker_port)
except Exception as e:
    logging.error("Error connecting to MQTT broker: %s", e)
    exit(1)

# 訂閱指定的 MQTT 主題
mqtt_client.subscribe(mqtt_topic)
mqtt_client.loop_start()

# 程式持續運行，直到手動停止
try:
    while True:
        pass
except KeyboardInterrupt:
    print("程式被手動中斷")
    mqtt_client.loop_stop()