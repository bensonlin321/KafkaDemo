<?php
/* vim: set expandtab tabstop=4 shiftwidth=4 softtabstop=4 foldmethod=marker: */
// +---------------------------------------------------------------------------
// | SWAN [ $_SWANBR_SLOGAN_$ ]
// +---------------------------------------------------------------------------
// | Copyright $_SWANBR_COPYRIGHT_$
// +---------------------------------------------------------------------------
// | Version  $_SWANBR_VERSION_$
// +---------------------------------------------------------------------------
// | Licensed ( $_SWANBR_LICENSED_URL_$ )
// +---------------------------------------------------------------------------
// | $_SWANBR_WEB_DOMAIN_$
// +---------------------------------------------------------------------------

namespace KafkaTest\Protocol;

/**
+------------------------------------------------------------------------------
* Kafka protocol since Kafka v0.8
+------------------------------------------------------------------------------
*
* @package
* @version $_SWANBR_VERSION_$
* @copyright Copyleft
* @author $_SWANBR_AUTHOR_$
+------------------------------------------------------------------------------
*/

class HeartbeatTest extends \PHPUnit_Framework_TestCase
{
    // {{{ consts
    // }}}
    // {{{ members

    /**
     * heart object
     *
     * @var mixed
     * @access protected
     */
    protected $heart = null;

    // }}}
    // {{{ functions
    // {{{ public function setUp()

    /**
     * setUp
     *
     * @access public
     * @return void
     */
    public function setUp()
    {
        if (is_null($this->heart)) {
            $this->heart = new \Kafka\Protocol\Heartbeat('0.9.0.1');
        }
    }

    // }}}
    // {{{ public function testEncode()

    /**
     * testEncode
     *
     * @access public
     * @return void
     */
    public function testEncode()
    {
        $data = array(
            'group_id' => 'test',
            'member_id' => 'kafka-php-0e7cbd33-7950-40af-b691-eceaa665d297',
            'generation_id' => 2,
        );
        $test = $this->heart->encode($data);
        $this->assertEquals(\bin2hex($test), '0000004d000c00000000000c00096b61666b612d70687000047465737400000002002e6b61666b612d7068702d30653763626433332d373935302d343061662d623639312d656365616136363564323937');
    }

    // }}}
    // {{{ public function testEncodeNoGroupId()

    /**
     * testEncodeNoGroupId
     *
     * @expectedException \Kafka\Exception\Protocol
     * @expectedExceptionMessage given heartbeat data invalid. `group_id` is undefined.
     * @access public
     * @return void
     */
    public function testEncodeNoGroupId()
    {
        $data = array();

        $test = $this->heart->encode($data);
    }

    // }}}
    // {{{ public function testEncodeNoGenerationId()

    /**
     * testEncodeNoGenerationId
     *
     * @expectedException \Kafka\Exception\Protocol
     * @expectedExceptionMessage given heartbeat data invalid. `generation_id` is undefined.
     * @access public
     * @return void
     */
    public function testEncodeNoGenerationId()
    {
        $data = array(
            'group_id' => 'test',
        );

        $test = $this->heart->encode($data);
    }

    // }}}
    // {{{ public function testEncodeNoMemberId()

    /**
     * testEncodeNoMemberId
     *
     * @expectedException \Kafka\Exception\Protocol
     * @expectedExceptionMessage given heartbeat data invalid. `member_id` is undefined.
     * @access public
     * @return void
     */
    public function testEncodeNoMemberId()
    {
        $data = array(
            'group_id' => 'test',
            'generation_id' => '1',
        );

        $test = $this->heart->encode($data);
    }

    // }}}
    // {{{ public function testDecode()

    /**
     * testDecode
     *
     * @access public
     * @return void
     */
    public function testDecode()
    {
        $test = $this->heart->decode(\hex2bin('0000'));
        $result = '{"errorCode":0}';
        $this->assertEquals(json_encode($test), $result);
    }

    // }}}
    // }}}
}
