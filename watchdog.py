import os
import json
import logging
from datetime import datetime, timedelta
from dotenv import load_dotenv
import paho.mqtt.client as mqtt
import threading
import time
import subprocess

# 設置重啟docker時間
how_minutes = 10

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
lock = threading.Lock()

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

# 定義檢查更新時間的函數
def check_block_url_times():
    while True:
        time.sleep(180)  # 每3分鐘檢查一次
        with lock:
            current_time = datetime.utcnow()
            how_minutes_ago = current_time - timedelta(minutes=how_minutes)
            # 檢查是否所有 tag 的時間戳都過期
            all_outdated = all(datetime.fromisoformat(timestamp) < how_minutes_ago for timestamp in block_url_dic.values())

            if all_outdated and block_url_dic:
                print(f"ERROR: All tags have not been updated in over {how_minutes} minutes")
                # 嘗試重啟 IOTA_GATEWAY_Docker
                restart_docker_container('my-iota-app-container')

# 定義重啟 Docker 容器的函數
def restart_docker_container(container_name):
    try:
        subprocess.run(['docker', 'restart', container_name], check=True)
        logging.info("Successfully restarted Docker container: %s", container_name)
    except subprocess.CalledProcessError as e:
        logging.error("Failed to restart Docker container: %s", container_name)
        logging.error("Error: %s", e)                                

# 初始化並啟動檢查更新時間的線程
thread = threading.Thread(target=check_block_url_times)
thread.daemon = True
thread.start()

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