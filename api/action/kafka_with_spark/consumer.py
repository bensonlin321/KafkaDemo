from kafka import KafkaConsumer

brokers, topic = 'localhost:9092', 'TEST_REQUEST'

if __name__ == '__main__':
    consumer = KafkaConsumer(topic, group_id='test-consumer-group', bootstrap_servers=[brokers])
    for msg in consumer:
        print("key=%s, value=%s" % (msg.key, msg.value))
