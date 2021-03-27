<?php
require_once __DIR__ . '/Resource.php';

class Request extends Resource{
    /*
        POST APIs
        - post_test:
            Do POST test

        GET APIs
        - get_test:
            Do GET test
    */

    function sendRequest($segments, $request_type, $data){
        if(count($segments) == 3){
            $task = $segments[0];
            $id = $segments[1];
            $other = $segments[2];
        } else if(count($segments) == 2){
            $other = "";
            $task = $segments[0];
            $id = $segments[1];
        } else if(count($segments) == 1){
            $other = "";
            $id = "-1";
            $task = $segments[0];
        } else{
            return self::exceptionResponseJson(400, 'Bad Request!');
        }

        if( empty($task) || is_null($id) || $data === FALSE || empty($request_type)){
            return self::exceptionResponseJson(400, 'Bad Request!');
        }

        require_once __DIR__ . '/util/request.php';
        $request_return = doRequest($task, $data, $id, $request_type, $other);

        $output = array(
            'status'    => '',
            'http_code' => '',
            'http_info' => '',
            'timestamp' => '',
            'data'      => ''
        );

        if($request_return == "0"){
            return self::exceptionResponseJson(400, 'Bad Request!');
        } else if($request_return == "-1"){
            return self::exceptionResponseJson(404, 'Not found');
        } else{
            $output['status']    = true;
            $output['http_code'] = "200";
            $output['http_info'] = "OK";
            $output['timestamp'] = time();
            $output['data']      = $request_return;
        }

        return json_encode($output);
        //return $request_return;
    }

    function restGetHandler($segments){
        $entity_body  = file_get_contents('php://input');
        $request_type = "get";
        return $this -> sendRequest($segments, $request_type, $entity_body);
    }

    function restPostHandler($segments) {
        //$method_type = _post('method_type');
        $entity_body  = file_get_contents('php://input');
        $request_type = "post";
        return $this -> sendRequest($segments, $request_type, $entity_body);
    }
}
?>
