// This contract is necessary only for the testing purpose on Kovan network
// because there is no dydx oracle on Kovan.
// deployed as 0x6D5A5E765F7a0399B4565322b5B636d8B5B45E9C on Kovan.
// It is a simplified version of https://etherscan.io/address/0x787f552bdc17332c98aa360748884513e3cb401a#code

pragma solidity >=0.4.0 <0.7.0;
pragma experimental ABIEncoderV2;

library Require {

    // ============ Constants ============

    uint256 constant ASCII_ZERO = 48; // '0'
    uint256 constant ASCII_RELATIVE_ZERO = 87; // 'a' - 10
    uint256 constant ASCII_LOWER_EX = 120; // 'x'
    bytes2 constant COLON = 0x3a20; // ': '
    bytes2 constant COMMA = 0x2c20; // ', '
    bytes2 constant LPAREN = 0x203c; // ' <'
    byte constant RPAREN = 0x3e; // '>'
    uint256 constant FOUR_BIT_MASK = 0xf;

    // ============ Library Functions ============

    function that(
        bool must,
        bytes32 file,
        bytes32 reason
    )
        internal
        pure
    {
        if (!must) {
            revert(
                string(
                    abi.encodePacked(
                        stringify(file),
                        COLON,
                        stringify(reason)
                    )
                )
            );
        }
    }

    function that(
        bool must,
        bytes32 file,
        bytes32 reason,
        uint256 payloadA
    )
        internal
        pure
    {
        if (!must) {
            revert(
                string(
                    abi.encodePacked(
                        stringify(file),
                        COLON,
                        stringify(reason),
                        LPAREN,
                        stringify(payloadA),
                        RPAREN
                    )
                )
            );
        }
    }

    function that(
        bool must,
        bytes32 file,
        bytes32 reason,
        uint256 payloadA,
        uint256 payloadB
    )
        internal
        pure
    {
        if (!must) {
            revert(
                string(
                    abi.encodePacked(
                        stringify(file),
                        COLON,
                        stringify(reason),
                        LPAREN,
                        stringify(payloadA),
                        COMMA,
                        stringify(payloadB),
                        RPAREN
                    )
                )
            );
        }
    }

    function that(
        bool must,
        bytes32 file,
        bytes32 reason,
        address payloadA
    )
        internal
        pure
    {
        if (!must) {
            revert(
                string(
                    abi.encodePacked(
                        stringify(file),
                        COLON,
                        stringify(reason),
                        LPAREN,
                        stringify(payloadA),
                        RPAREN
                    )
                )
            );
        }
    }

    function that(
        bool must,
        bytes32 file,
        bytes32 reason,
        address payloadA,
        uint256 payloadB
    )
        internal
        pure
    {
        if (!must) {
            revert(
                string(
                    abi.encodePacked(
                        stringify(file),
                        COLON,
                        stringify(reason),
                        LPAREN,
                        stringify(payloadA),
                        COMMA,
                        stringify(payloadB),
                        RPAREN
                    )
                )
            );
        }
    }

    function that(
        bool must,
        bytes32 file,
        bytes32 reason,
        address payloadA,
        uint256 payloadB,
        uint256 payloadC
    )
        internal
        pure
    {
        if (!must) {
            revert(
                string(
                    abi.encodePacked(
                        stringify(file),
                        COLON,
                        stringify(reason),
                        LPAREN,
                        stringify(payloadA),
                        COMMA,
                        stringify(payloadB),
                        COMMA,
                        stringify(payloadC),
                        RPAREN
                    )
                )
            );
        }
    }

    // ============ Private Functions ============

    function stringify(
        bytes32 input
    )
        private
        pure
        returns (bytes memory)
    {
        // put the input bytes into the result
        bytes memory result = abi.encodePacked(input);

        // determine the length of the input by finding the location of the last non-zero byte
        for (uint256 i = 32; i > 0; ) {
            // reverse-for-loops with unsigned integer
            /* solium-disable-next-line security/no-modify-for-iter-var */
            i--;

            // find the last non-zero byte in order to determine the length
            if (result[i] != 0) {
                uint256 length = i + 1;

                /* solium-disable-next-line security/no-inline-assembly */
                assembly {
                    mstore(result, length) // r.length = length;
                }

                return result;
            }
        }

        // all bytes are zero
        return new bytes(0);
    }

    function stringify(
        uint256 input
    )
        private
        pure
        returns (bytes memory)
    {
        if (input == 0) {
            return "0";
        }

        // get the final string length
        uint256 j = input;
        uint256 length;
        while (j != 0) {
            length++;
            j /= 10;
        }

        // allocate the string
        bytes memory bstr = new bytes(length);

        // populate the string starting with the least-significant character
        j = input;
        for (uint256 i = length; i > 0; ) {
            // reverse-for-loops with unsigned integer
            /* solium-disable-next-line security/no-modify-for-iter-var */
            i--;

            // take last decimal digit
            bstr[i] = byte(uint8(ASCII_ZERO + (j % 10)));

            // remove the last decimal digit
            j /= 10;
        }

        return bstr;
    }

    function stringify(
        address input
    )
        private
        pure
        returns (bytes memory)
    {
        uint256 z = uint256(input);

        // addresses are "0x" followed by 20 bytes of data which take up 2 characters each
        bytes memory result = new bytes(42);

        // populate the result with "0x"
        result[0] = byte(uint8(ASCII_ZERO));
        result[1] = byte(uint8(ASCII_LOWER_EX));

        // for each byte (starting from the lowest byte), populate the result with two characters
        for (uint256 i = 0; i < 20; i++) {
            // each byte takes two characters
            uint256 shift = i * 2;

            // populate the least-significant character
            result[41 - shift] = char(z & FOUR_BIT_MASK);
            z = z >> 4;

            // populate the most-significant character
            result[40 - shift] = char(z & FOUR_BIT_MASK);
            z = z >> 4;
        }

        return result;
    }

    function char(
        uint256 input
    )
        private
        pure
        returns (byte)
    {
        // return ASCII digit (0-9)
        if (input < 10) {
            return byte(uint8(input + ASCII_ZERO));
        }

        // return ASCII letter (a-f)
        return byte(uint8(input + ASCII_RELATIVE_ZERO));
    }
}

library SafeMath {
    /**
    * @dev Multiplies two unsigned integers, reverts on overflow.
    */
    function mul(uint256 a, uint256 b) internal pure returns (uint256) {
        // Gas optimization: this is cheaper than requiring 'a' not being zero, but the
        // benefit is lost if 'b' is also tested.
        // See: https://github.com/OpenZeppelin/openzeppelin-solidity/pull/522
        if (a == 0) {
            return 0;
        }

        uint256 c = a * b;
        require(c / a == b);

        return c;
    }

    /**
    * @dev Integer division of two unsigned integers truncating the quotient, reverts on division by zero.
    */
    function div(uint256 a, uint256 b) internal pure returns (uint256) {
        // Solidity only automatically asserts when dividing by 0
        require(b > 0);
        uint256 c = a / b;
        // assert(a == b * c + a % b); // There is no case in which this doesn't hold

        return c;
    }

    /**
    * @dev Subtracts two unsigned integers, reverts on overflow (i.e. if subtrahend is greater than minuend).
    */
    function sub(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b <= a);
        uint256 c = a - b;

        return c;
    }

    /**
    * @dev Adds two unsigned integers, reverts on overflow.
    */
    function add(uint256 a, uint256 b) internal pure returns (uint256) {
        uint256 c = a + b;
        require(c >= a);

        return c;
    }

    /**
    * @dev Divides two unsigned integers and returns the remainder (unsigned integer modulo),
    * reverts when dividing by zero.
    */
    function mod(uint256 a, uint256 b) internal pure returns (uint256) {
        require(b != 0);
        return a % b;
    }
}

library Math {
    using SafeMath for uint256;
    
    // ============ Constants ============

    bytes32 constant FILE = "Math";

    // ============ Library Functions ============
    function to128(
        uint256 number
    )
        internal
        pure
        returns (uint128)
    {
        uint128 result = uint128(number);
        Require.that(
            result == number,
            FILE,
            "Unsafe cast to uint128"
        );
        return result;
    }

    function to32(
        uint256 number
    )
        internal
        pure
        returns (uint32)
    {
        uint32 result = uint32(number);
        Require.that(
            result == number,
            FILE,
            "Unsafe cast to uint32"
        );
        return result;
    }
}

contract DaiPriceOracle {
    using SafeMath for uint256;
    
    // ============ Structs ============
    struct PriceInfo {
        uint128 price;
        uint32 lastUpdate;
    }
    
    // ============ Events ============
    event PriceSet(
        PriceInfo newPriceInfo
    );

    // ============ Storage ============
    PriceInfo public g_priceInfo;

    // ============ Public Functions ============
    function updatePrice(uint newPrice) public returns (PriceInfo memory){
        g_priceInfo = PriceInfo({
            price: Math.to128(newPrice.value),
            lastUpdate: Math.to32(block.timestamp)
        });
	
        emit PriceSet(g_priceInfo);
        return g_priceInfo;
    }
}
