from kafka import KafkaProducer
import time

brokers, topic = 'localhost:9092', 'TEST_REQUEST'

def start():
    cnt = 0
    while True:
        print(" --- produce ---")
        time.sleep(1)
        cnt = cnt + 1
        val = "benson_{}".format(cnt)
        val.encode('utf-8')
        producer.send(topic, key=b'benson', value=val)
        producer.flush()
 
 
if __name__ == '__main__':
    producer = KafkaProducer(bootstrap_servers=brokers)
    start()
    producer.close()
