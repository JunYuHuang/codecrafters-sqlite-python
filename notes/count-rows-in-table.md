# Your Task

Now that you've gotten your feet wet with the [SQLite database file format](https://www.sqlite.org/fileformat.html), it's time to move on to actual SQL!

In this stage, your program will need to read the count of rows from a table.

Here's how the tester will execute your program:
```
$ ./your_program.sh sample.db "SELECT COUNT(*) FROM apples"
```

and here's the output it expects:
```
4
```

You'll need to read the table's row from the [sqlite_schema](https://www.sqlite.org/schematab.html) table and follow the `rootpage` value to visit the page corresponding to the table. For now you can assume that the contents of the table are small enough to fit inside the root page. We'll deal with tables that span multiple pages in stage 7.

Remember: You don't need to implement a full-blown SQL parser just yet. We'll get to that in the next stages. For now you can just split the input by " " and pick the last item to get the table name.

## How to pass this stage

### 1. Write code to pass this stage

Head over to your editor / IDE and implement your solution.

If you want a quick look at what functions to use or how to structure your code, we recommend looking at [Code Examples](https://app.codecrafters.io/courses/sqlite/stages/nd9/code-examples).

### 2. Submit code

To run tests, make changes to your code and run the submit command:
```
codecrafters submit # Visit https://codecrafters.io/cli to install
```

To run tests, make changes to your code and run the following commands:
```
git add .
git commit --allow-empty -m "[any message]"
git push origin master
```

# Notes:

- PEDAC: Problem
    - input:
        - `argv`: string array of CLI arguments taken + passed when running the program
            - `argv[0]`: path to program i.e., `./your_program.sh`
            - `argv[1]`: path to a SQLite database e.g., `sample.db`
            - `argv[2]`: SQLite command to run e.g., `SELECT COUNT(*) FROM apples`
    - output:
        - none
    - side effects:
        - TODO
    - questions
        - TODO
    - SQLite database = 1+ pages
        - `sqlite_schema` table
            - stores database schema
            - is in page 1
            - cell count in its page header
                - = 2-byte big-endian value
        - each page = 1+ cells (i.e., rows)
    - SQLite database page 1 structure:
        - database header (100 Bytes) +
        - page header (8 Bytes) +
        - n * cell pointers (n * 2 Bytes)
    - page header structure (8 Bytes):
        - page type (1 Byte) +
        - first free block (2 Bytes) +
        - cell count (2 Bytes) +
        - cell content area (2 Bytes) +
        - fragement free bytes (1 Byte)
    - useful learning links:
        - https://sqlite-internal.pages.dev/
        - https://fly.io/blog/sqlite-internals-btree/
        - https://link.springer.com/content/pdf/10.1007/978-3-030-98467-0_5.pdf
        - https://torymur.github.io/sqlite-repr/
- PEDAC: Examples
    - ex.1: run `.dbinfo` command
        - run in terminal:
            ```
            ./your_program.sh sample.db .dbinfo
            ```
        - terminal output:
            ```
            database page size: 4096
            number of tables: 3
            ```
    - ex.2: run `.tables` command
        - run in terminal:
            ```
            ./your_program.sh sample.db .tables
            ```
        - terminal output:
            ```
            apples oranges
            ```
    - ex.3: run `SELECT COUNT(*) FROM <table>` command
        - run in terminal:
            ```
            ./your_program.sh sample.db SELECT COUNT(*) FROM apples
            ```
        - terminal output:
            ```
            4
            ```
- PEDAC: Data Structures And Algorithms
    - helper functions
        - `rootpage_of(database_file: file, table_name: string) -> integer`
            - done
        - `parse_leaf_page_header(database_file: file, rootpage: integer) -> hashmap`
            - set int `database_offset` to `(rootpage - 1)` * `PAGE_SIZE`
            - if `rootpage` is 1,
                - add `DATABASE_HEADER_SIZE` to `database_offset`
            - move file cursor in `database_file` to position `database_offset`
            - set `page_header_bytes` to `LEAF_PAGE_HEADER_SIZE` bytes read from `database_file` at current position
            - set hashmap `res` empty
            - set int `cell_count_start_pos` to `PAGE_TYPE_SIZE` + `FIRST_FREE_BLOCK_SIZE`
            - set key `res["cell_count"]` to `page_header_bytes[cell_count_start_pos:cell_count_start_pos + CELL_COUNT_SIZE]` converted to an integer
            - return `res`
        - `parse_sql(statement: string) -> dict`
            - done
    - set int `DATABASE_HEADER_SIZE` to 100
    - set int `LEAF_PAGE_HEADER_SIZE` to 8
    - set int `INTERIOR_PAGE_HEADER_SIZE` to 12
    - set int `PAGE_SIZE` to 4096
    - set int `PAGE_TYPE_SIZE` to 1
    - set int `FIRST_FREE_BLOCK_SIZE` to 2
    - set int `CELL_COUNT_SIZE` to 2
    - set string `database_file_path` to `argv[1]`
    - set string `command` to `argv[2]`
    - open file (descriptor) object `database_file` from path `database_file_path` as bytes with read permissions
    - if length of `command` > 1,
        - assume it's a SQL statement
        - set hashmap `sql_dict` to `parse_sql(command)`
        - set int `rootpage` to `rootpage_of(database_file, sql_dict["table"])`
        - set hashmap `leaf_page_header_dict` to `parse_leaf_page_header(database_file, rootpage)`
        - print int `leaf_page_header_dict["cell_count"]`
    - close file object at path `database_file`