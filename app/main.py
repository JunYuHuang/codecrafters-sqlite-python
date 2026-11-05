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

def main() -> None:
    database_file_path = sys.argv[1]
    command = sys.argv[2]
    database_file: io.BufferedReader = open(database_file_path, "rb")

    if command == ".dbinfo":
        database_header_dict = parse_database_header(database_file)
        print(f"database page size: {database_header_dict["page_size"]}")
        print(f"number of tables: {database_header_dict["cell_count"]}")
    else:
        print(f"Invalid command: {command}")

    database_file.close()

if __name__ == "__main__":
    main()
