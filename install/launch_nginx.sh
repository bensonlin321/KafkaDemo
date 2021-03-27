echo "127.0.0.1 self.test.com" >> /etc/hosts
echo "127.0.0.1 kafka_1" >> /etc/hosts
echo "127.0.0.1 Redis" >> /etc/hosts
service nginx start
service php7.2-fpm start
service redis-server start
redis-server --daemonize yes
