import sys
from pyspark import SparkContext
from pyspark.streaming import StreamingContext
from pyspark.streaming.kafka import KafkaUtils

brokers, topic = 'localhost:9092', 'TEST_REQUEST'

if __name__ == "__main__":
    sc = SparkContext(appName="PythonStreamingDirectKafkaWordCount")
    ssc = StreamingContext(sc, 5)

    kvs = KafkaUtils.createDirectStream(ssc, [topic], {"metadata.broker.list": brokers})
    lines = kvs.map(lambda x: x[1])
    #lines.count().map(lambda x:'number of data in this batch: %s' % x).pprint()

    counts = lines.flatMap(lambda line: line.split(" "))
    counts.pprint()

    ssc.start()
    ssc.awaitTermination()
