wget https://github.com/frekele/oracle-java/releases/download/8u211-b12/jdk-8u211-linux-x64.tar.gz
tar -zxvf jdk-8u211-linux-x64.tar.gz
wget https://archive.apache.org/dist/kafka/2.0.0/kafka_2.12-2.0.0.tgz
tar -zxvf kafka_2.12-2.0.0.tgz

tar xf /temp/install/ssl.tar.gz -C /opt;
cp -R /temp/install/jdk1.8.0_211 /usr/lib/jdk1.8.0_211
ln -s /usr/lib/jdk1.8.0_211/bin/java /etc/alternatives/java
export JAVA_HOME=/usr/lib/jdk1.8.0_211
export PATH=$PATH:$JAVA_HOME/bin

mkdir /opt/librdkafka
cd /opt/librdkafka
wget https://github.com/edenhill/librdkafka/archive/v0.11.5.tar.gz
tar xf v0.11.5.tar.gz
cd librdkafka-0.11.5
./configure
make && make install
ldconfig

apt-get install -y python3-pip
pip3 install confluent-kafka==0.11.5

apt-get install -y net-tools
apt-get install -y python
apt-get install -y python-pip
pip install kafka

# cleanup
ps aux | grep server.properties | awk {'print $2'} | xargs kill -9;
ps aux | grep zkclient | awk {'print $2'} | xargs kill -9;
sleep 5;

cd /opt
rm -rf kafka
rm -rf kafka-logs
rm -rf zookeeper
rm -f kafka*.tgz

cp -R /temp/install/kafka_2.12-2.0.0 /opt/kafka


# stop kafka
ps aux | grep server.properties | awk {'print $2'} | xargs kill -9;
ps aux | grep zkclient | awk {'print $2'} | xargs kill -9;


# start kafka
/temp/install/kafka_command.sh

export KAFKA_HEAP_OPTS="-Xmx256M -Xms128M"
nohup /opt/kafka/bin/zookeeper-server-start.sh /opt/kafka/config/zookeeper.properties > /dev/null 2>&1 &
sleep 5;
nohup /opt/kafka/bin/kafka-server-start.sh /opt/kafka/config/server.properties > /dev/null 2>&1 &
sleep 3;

# wait for broker ready
while true;
do
  zookeeper_ready=`netstat -an | grep LISTEN | grep 2080`;
  if [ ! -z "$zookeeper_ready" ]; then
    break;
  fi
  sleep 1;
done
while true;
do
  kafka_ready=`netstat -an | grep LISTEN | grep 9093`;
  if [ ! -z "$kafka_ready" ]; then
    break;
  fi
  sleep 1;
done

setup_kafka_1=`cat /etc/hosts | grep kafka_1`;
if [ -z "$setup_kafka_1" ]; then
  echo "127.0.0.1 kafka_1" >> /etc/hosts;
fi

# create topic for kafka
/opt/kafka/bin/kafka-topics.sh --zookeeper 127.0.0.1:2080 --create --replication-factor 1 --partitions 2 --topic TEST_REQUEST
sleep 5;
/opt/kafka/bin/kafka-topics.sh --describe --zookeeper 127.0.0.1:2080 TEST_REQUEST



# nginx
apt-get update
apt-get install -y nginx  
apt-get install -y php-fpm
apt-get install -y php7.2-zip  php7.2-mcrypt php7.2-mbstring php7.2-json  php7.2-gmp php7.2-curl php7.2-gd

cp /temp/install/nginx_data/nginx.conf /etc/nginx/conf.d/nginx.conf

service nginx start
service php-fpm start

apt-get install libssl-dev openssl
pip3 install typing
pip3 install confluent_kafka
pip3 install logzero
pip3 install redis
pip3 install requests

apt-get install -y redis-server

service redis-server start
