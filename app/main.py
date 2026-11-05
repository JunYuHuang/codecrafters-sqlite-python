from dataclasses import dataclass
import io
import sys
# import sqlparse - available if you need it!

DATABASE_HEADER_SIZE = 100
CELL_SIZE_POS = DATABASE_HEADER_SIZE + 1 + 2

def parse_database_header(database_file: io.BufferedReader) -> dict:
    res = {}

    database_file.seek(16)  # Skip the first 16 bytes of the header
    page_size = int.from_bytes(database_file.read(2), byteorder="big")
    res["page_size"] = page_size

    database_file.seek(CELL_SIZE_POS)
    cell_count = int.from_bytes(database_file.read(2), byteorder="big")
    res["cell_count"] = cell_count

    return res

def int_to_binary_str(integer: int, bit_length: int = 1) -> str:
    if type(bit_length) != int or bit_length <= 0:
        bit_length = 1
    return format(integer, f"0{bit_length}b")

# TODO: to test
def parse_varint(data: bytes, offset: int) -> list[int]:
    error_list = [float("inf"), float("inf")]
    DATA_LEN = len(data)
    MAX_VARINT_BYTES = 9

    if offset <= DATA_LEN:
        print(f"[Error]: Offset {offset} in bytestream is out of bounds")
        return error_list

    byte_count = 1
    varint_padded_bit_zeroes_count = 0
    varint_bits: list[str] = []
    while offset < DATA_LEN and byte_count <= MAX_VARINT_BYTES:
        data_byte_int = int.from_bytes(data[offset:offset + 1], byteorder='big')
        data_byte_str = int_to_binary_str(data_byte_int, 8)

        # msb = Most Significant Bit i.e., leftmost bit in a byte for a
        # big-endian encoded signed integer
        msb_int = int(data_byte_str[:1], 2)

        if byte_count == MAX_VARINT_BYTES:
            res.append(data_byte_str)
            varint_padded_bit_zeroes_count += 1
        else:
            # payload bits are the lower remaining 7 bits in the byte
            payload_bits_str = data_byte_str[1:]
            res.append(payload_bits_str)
            if msb == 0: break
        byte_count += 1

        # add padded binary 0's to final bit string?

        # TODO:
        # - set string `varint_bits_str` to all string elements of `varint_bits` joined together in order with empty space `` char
        # - return `varint_bits_str` as string bits converted to a signed integer

    return error_list

def main() -> None:
    database_file_path = sys.argv[1]
    command = sys.argv[2]
    database_file: io.BufferedReader = open(database_file_path, "rb")

    # TODO: debug varint parser


    if command == ".dbinfo":
        database_header_dict = parse_database_header(database_file)
        print(f"database page size: {database_header_dict["page_size"]}")
        print(f"number of tables: {database_header_dict["cell_count"]}")
    # TODO: to test
    elif command == ".tables":
        print("TODO: Implement command '.tables'")
    else:
        print(f"Invalid command: {command}")

    database_file.close()

if __name__ == "__main__":
    main()
