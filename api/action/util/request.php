<?php
    global $crt_path;
    global $key_path;
    global $ca_path;

    function _get_partition_id($id){
        $partition_id = $id % 2;
        return $partition_id;
    }

    // Producer
    function _send_to_consumer($send_data, $task){
        require_once __DIR__ . '/../library/kafka-php/autoload.php';
        try {
            $config = \Kafka\ProducerConfig::getInstance();
            $config -> setMetadataRefreshIntervalMs(10000);
            $config -> setMetadataBrokerList('kafka_1:9092,kafka_2:9092,kafka_3:9092');
            $config -> setBrokerVersion('1.0.0');
            $config -> setRequiredAck(1);
            $config -> setIsAsyn(false);
            $config -> setProduceInterval(500);
            $producer = new \Kafka\Producer();
        
            // partition is 2 for this topic
            $total_partitions = 2;

            $id = $send_data['id'];
            $partition_id = _get_partition_id($id);

            $value = json_encode($send_data);
            $result = $producer -> send([
                [
                    'partId' => $partition_id,
                    'topic' => "TEST_REQUEST",
                    'value' => $value,
                    'key' => $task
                ],
            ]);
            return ($result !== false);
	} catch (Exception $e) {
	    return $e->getMessage();
            return false;
        }
    }

    /*
        - sendToConsumerQueue
        - deal with the POST request and send data to consumer
        -----------------------------------------------------------
        Task (HTTP POST)
	- posttest
	    - test
   */
    function sendToConsumerQueue($task, $data, $id, $request_type, $other = NULL) {
        $send_data = array();
        $send_data['task'] = $task;
        $send_data['data'] = $data;
        $send_data['id'] = $id;
        $send_data['request_type'] = $request_type;
        if(!empty($other)){
            $send_data['other'] = $other;
        }
        $valid_array = array(
                            "posttest"
                        );

	if(!in_array($task, $valid_array)){
            return false;
	}
        return _send_to_consumer($send_data, $task);
    }

    /*
        testStorage
        - use to test if Storage is accessible
    */
    /*function testStorage(){
        try {
            $server_info = array(
                'host' => 'Redis',
                'port' => 6379,
                'database' => 0
            );
            $storage_client = new Storage($server_info);

            if(!$storage_client->ping()){
                return "Fail to touch Storage";
            }
        } catch (Exception $e){
            return "Fail to touch Storage";
        }
        return "Successfully touch Storage";
    }*/

    /* 
        dataProcessor
        - deal with the GET request and return data (blocking code)
        -----------------------------------------------------------
        Task (HTTP GET)
        - check

    */
    function dataProcessor($task, $data, $id, $request_type, $other = NULL) {

        if($task == "check"){
            $get_data = doCheckServerAlive();
        } else if($task == "test"){
            return "test";
        } else{
            return "0";
        }

        // prepare the data for log
        $task_name = $task . "_get";
        $send_data = array();
        $send_data['task'] = $task_name;
        $send_data['data'] = $get_data;
        $send_data['id'] = $id;
        $send_data['request_type'] = $request_type;
        if(!empty($other)){
            $send_data['other'] = $other;
        }
        _send_to_consumer($send_data, $task_name);
        return $get_data;
    }

    function get_client_ip() {
        $ipaddress = '';
        if (isset($_SERVER['HTTP_CLIENT_IP']))
            $ipaddress = $_SERVER['HTTP_CLIENT_IP'];
        else if(isset($_SERVER['HTTP_X_FORWARDED_FOR']))
            $ipaddress = $_SERVER['HTTP_X_FORWARDED_FOR'];
        else if(isset($_SERVER['HTTP_X_FORWARDED']))
            $ipaddress = $_SERVER['HTTP_X_FORWARDED'];
        else if(isset($_SERVER['HTTP_FORWARDED_FOR']))
            $ipaddress = $_SERVER['HTTP_FORWARDED_FOR'];
        else if(isset($_SERVER['HTTP_FORWARDED']))
            $ipaddress = $_SERVER['HTTP_FORWARDED'];
        else if(isset($_SERVER['REMOTE_ADDR']))
            $ipaddress = $_SERVER['REMOTE_ADDR'];

        return $ipaddress;
    }
    function checkIP(){
        $client_ip = get_client_ip();
        if(empty($client_ip)){
            return false;
        }
        $domain_name = gethostbyaddr($client_ip);
        $valid_ips = array('::1',
                           '127.0.0.1',
                           '::ffff:127.0.0.1',
                           '0.0.0.0',
                           );
        if(in_array($client_ip, $valid_ips)){
            return true;
        }
        if(strpos($client_ip, '10.1.1.') === 0) {
            // the position must be 0, which means the ip is 10.1.1.x
            return true;
        }

        // deal with the ip from AWS Lambda
        // we expected the domain name will be ec2-52-195-14-21.ap-northeast-1.compute.amazonaws.com
        if(strpos($domain_name, "compute.amazonaws.com") !== FALSE && strpos($domain_name, "ec2") !== FALSE){
            return true;
        }
        return false;
    }

    function checkDebugIP(){
        $client_ip = get_client_ip();
        if(empty($client_ip)){
            return false;
        }
        $valid_ips = array('0.0.0.0');
        if(in_array($client_ip, $valid_ips)){
            return true;
        }
        return false;
    }

    // Helper functions
    function getCmdKey($cmd) {
        $frontend_tag = "service";
        $fe_delimiter = "|";
        return $frontend_tag . $fe_delimiter . $cmd;
    }

    function constructPayload($cmd_key) {
        $time = time();
        $data = array(
            $cmd_key => strval($time)
        );
        return json_encode($data);
    }

    /*
        Check server alive
    */
    function doCheckServerAlive(){
        // check if IP is valided

        // whitelist
        /*if(!checkIP()){
            return "-1";
        }*/
        $output = "Check OK";
        return $output;
    }
    
    function doRequest($task, $data, $id, $request_type, $other = NULL, $try_queue = true) {
        if ($try_queue === true) {
            // write log
            $date = date('Y-m-d H:i:s', time());
            $log_data = "[ ".$date." ] ".$id."\n\t".$task."\n\t".$request_type."\n\t".json_encode($data)."\n\n";
            writeLog($log_data);
            /*
                check /etc/hosts: kafka1, kafka2, kafka3, Redis
                need to set
                /etc/hosts
                - for kafka:
                    #kafka
                    127.0.0.1 kafka_1
                    127.0.0.1 kafka_2
                    127.0.0.1 kafka_3
                    127.0.0.1 Redis
            */
            // determine the process for certain type of request
            if($request_type == "get"){
                // wait for data back
                return dataProcessor($task, $data, $id, $request_type, $other);
            } else{
                // check if IP is valided
                /*if(!checkIP() && !checkDebugIP()){
                    return "-1";
                }*/
                // send data to consumer
                $res = sendToConsumerQueue($task, $data, $id, $request_type, $other);
                if ($res) {
                    return "1";
                } else{
                    return "0";
                }
            }
        }
    }

    function writeLog($log_data){
        $log_path = '/tmp/logs.log';
        @mkdir($log_path);
        $date_str = date('Y-m-d', time());
        $file_path = "$log_path/push-$date_str.log";
        $f = fopen($file_path, 'a');
        fwrite($f, $log_data);
        fclose($f);
    }

?>
