echo "Wait for kafka server"
sleep 10;
bash /temp/api/action/util/launch_consumer.sh
echo "Wait for consumer..."
sleep 6;
echo "Check Nginx Server and API..."
curl self.test.com/api/action/check

NumOfProcess=`ps aux | grep "consumer.py" | grep -v "grep" | wc -l`
echo $NumOfProcess
if [ "$NumOfProcess" != "2" ] ; then
    echo "fail to launch Consumer !!!"
fi

