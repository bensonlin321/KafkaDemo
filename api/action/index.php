<?php
require_once __DIR__ . '/Resource.php';
class Container extends Resource {

    private static $PATH_INFO = "REDIRECT_PATH_INFO";

    private $_control = FALSE;
    private $_segments = FALSE;

    function __construct() {
        $this -> _segments = self::parse_segments();
        if (empty($this -> _segments)) return;
        // first element is always an empty string
        array_shift($this -> _segments);

        //check number of uri
        /*if(count($this -> _segments) == 3){
            $region = $this -> _segments[0];
            $mac = $this -> _segments[1];
            $topic = $this -> _segments[2];
        } else if(count($this -> _segments) == 2){
            $mac = $this -> _segments[0];
            $topic = $this -> _segments[1];
        }*/

        $file_path = __DIR__ . "/Request.php";
        if (file_exists($file_path)) {
            require_once $file_path;
        } else {
            self::exceptionResponseJson(503, 'Service Unavailable!');
        }
        header("Cache-Control: no-store, no-cache, must-revalidate, max-age=0");
        header("Cache-Control: post-check=0, pre-check=0", false);
        header("Pragma: no-cache");
        
        // start class
        $this -> _control = new Request;
    }
    
    function parse_segments() {
        if (strpos($_SERVER['SERVER_SOFTWARE'], 'nginx') !== FALSE) {
            if (!isset($_SERVER['REQUEST_URI']) || $_SERVER['REQUEST_URI'] == '/')
                return array();
            // get uri path [api/iot]
            $path = str_replace(basename($_SERVER['DOCUMENT_URI']), '', $_SERVER['DOCUMENT_URI']);

            // cut out lang/api/iot
            $uri = substr($_SERVER['REQUEST_URI'], strpos($_SERVER['REQUEST_URI'], $path) + strlen($path));

            // make sure the first element is empty
            if(strpos($uri, '/') !== 0) {
                $uri = "/$uri";
            }

            // cut out query string
            if(strpos($_SERVER['REQUEST_URI'], '?') !== false) {
                $tokens = explode('?', $uri);
                $uri = $tokens[0];
	    }
            return explode('/', $uri);
        } else {
            if (!isset($_SERVER[self::$PATH_INFO]) || $_SERVER[self::$PATH_INFO] == '/')
                return array();
            return explode('/', $_SERVER[self::$PATH_INFO]);
        }
    }
    
    function run() {
        if ($this -> _control === FALSE)
            self::exceptionResponseJson(404, 'Not Found!');
	    // check method
        $method = 'rest' . ucfirst(strtolower($_SERVER['REQUEST_METHOD'])) . 'Handler';
	    if (!method_exists($this -> _control, $method))
            self::exceptionResponseJson(405, 'Method not Allowed!');
        $argument = $this -> _segments;
        $result = $this -> _control -> $method($argument);
        return $result;
    }
}

    // exception list
    function addDefense() {
        $request_uri = isset($_SERVER['REQUEST_URI']) ? $_SERVER['REQUEST_URI'] : '';
        $except_uri_list = array('logo', 'thumbnail', 'snapshot', 'offline', 'online', 'unknown');
        // check uri
        foreach ($except_uri_list as $except_uri) {
            if (strpos($request_uri, $except_uri) !== FALSE) {
                return FALSE;
            }
        }
        return TRUE;
    }

    /*
    $ini = @parse_ini_file('/opt/Config.ini');
    if (isset($ini) && isset($ini['SKS']) && $ini['SKS']) {
        if (isMobile() === FALSE && addDefense() === TRUE) {
            echo '<script type="text/javascript">';
            echo 'if (self != top) {';
            echo 'top.location = self.location;';
            echo '}';
            echo '</script>';
        }
    }*/
    
    // run
    $container = new Container();
    echo $container -> run();
?>
