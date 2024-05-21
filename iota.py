import os
import json
import logging
from dotenv import load_dotenv
from iota_sdk import Client as IOTA_Client, hex_to_utf8, utf8_to_hex
import paho.mqtt.client as mqtt

# 設置日誌級別
logging.basicConfig(level=logging.INFO)

load_dotenv()

node_url = os.getenv('NODE_URL')
mqtt_broker_url = os.getenv('MQTT_BROKER_URL')
mqtt_broker_port = int(os.getenv('MQTT_BROKER_PORT'))
mqtt_topic = os.getenv('MQTT_TOPIC')
mqtt_username = os.getenv('MQTT_USERNAME')
mqtt_password = os.getenv('MQTT_PASSWORD')

# 創建 IOTA 客戶端實例
iota_client = IOTA_Client(nodes=[node_url])

# 確保十六進制字符串有正確的前綴
def prefix_hex(hex_string):
    if not hex_string.startswith('0x'):
        return '0x' + hex_string
    return hex_string

# 儲存接收到的 MQTT 消息
received_messages = {}

# MQTT 回調函數
def on_message(client, userdata, message):
    try:
        # 將字節串消息解碼為字符串
        message_str = message.payload.decode('utf-8')
        print(f"Received message from topic {message.topic}: {message_str}")

        # 從主題名稱中提取 'tag'
        tag = message.topic.split('/')[1]
        # 從主題名稱提取鍵值對的key
        key = message.topic.split('/')[2]

        # 如果 'tag' 包含 'STATE' 或 'SENSOR'，則保存消息
        if 'STATE' in message.topic or 'SENSOR' in message.topic:
            # 嘗試解析 JSON 數據，如果失敗則將整個消息作為字符串處理
            try:
                message_content = json.loads(message_str)
            except json.JSONDecodeError:
                message_content = message_str

            # 將消息儲存到 received_messages 字典中
            received_messages[key] = message_content
            print(f'\nreceived_messages:\n{received_messages}')
            
            # 如果 'tag' 包含 'STATE' 與 'SENSOR'，則傳送到tangle
            if 'STATE' in received_messages and 'SENSOR' in received_messages:
                # 將 'tag' 和 'message' 字段的內容轉換為 JSON 字符串並轉換為十六進制
                tag_hex = prefix_hex(utf8_to_hex(tag))
                message_json = json.dumps(received_messages)
                message_hex = prefix_hex(utf8_to_hex(message_json))
                
                # 將數據打包成區塊並上傳到 Tangle
                blockIdAndBlock = iota_client.build_and_post_block(
                    secret_manager=None, tag=tag_hex, data=message_hex)
    
                block_id = blockIdAndBlock[0]
                block = blockIdAndBlock[1]
    
                # 回傳打包資訊
                print(f"Block ID: {block_id}")
                print(f"Block: {block}")
    
                # 查看上傳資料
                print(f'\nOr see the message with the testnet explorer: {os.environ["EXPLORER_URL"]}/block/{block_id}')
    
                # 將網址以 MQTT 傳送
                iota_url_mqtt_topic = mqtt_topic.split('/')[0]+'/'+tag+'/BLOCK_URL'
                print(f'\nMQTT send\n{iota_url_mqtt_topic}: {os.environ["EXPLORER_URL"]}/block/{block_id}')
                mqtt_client.publish(iota_url_mqtt_topic, f'{os.environ["EXPLORER_URL"]}/block/{block_id}')
                
                # 清空 received_messages 字典以便於下一次打包
                received_messages.clear()
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
