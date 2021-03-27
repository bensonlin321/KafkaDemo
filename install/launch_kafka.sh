# start kafka
echo "start kafka"
export KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"
export JAVA_HOME=/usr/lib/jdk1.8.0_211
export PATH=$PATH:$JAVA_HOME/bin
sleep 5
echo "run zookeeper"
nohup /opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties > /dev/null 2>&1 &
sleep 8
echo "run kafka server"
nohup /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties > /dev/null 2>&1 &
