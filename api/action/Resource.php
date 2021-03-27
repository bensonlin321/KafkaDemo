<?php

class Resource {
    
    static function exceptionResponse($statusCode, $message) {
        header("HTTP/1.0 {$statusCode} {$message}");
        echo "{$statusCode} {$message}";
        exit;
    }

    static function exceptionResponseJson($statusCode, $message) {
        header("HTTP/1.0 {$statusCode} {$message}");
        $output = array(
	        'status'    => false,
	        'http_code' => $statusCode,
	        'http_info' => $message,
	        'timestamp' => time(),
	        'data'      => ''
	    );
        echo json_encode($output);
        exit;
    }
}
?>
