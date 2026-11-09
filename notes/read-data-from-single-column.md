# Your Task

Now that you're comfortable with jumping across database pages, let's dig a little deeper and read data from rows in a table.

Here's how the tester will execute your program:
```
$ ./your_program.sh sample.db "SELECT name FROM apples"
```

and here's the output it expects:
```
Granny Smith
Fuji
Honeycrisp
Golden Delicious
```

The order of rows returned doesn't matter.

Rows are stored on disk in the [Record Format](https://www.sqlite.org/fileformat.html#record_format), which is just an ordered sequence of values. To extract data for a single column, you'll need to know the order of that column in the sequence. You'll need to parse the table's `CREATE TABLE` statement to do this. The `CREATE TABLE` statement is stored in the [`sqlite_schema`](https://www.sqlite.org/schematab.html) table's `sql` column.

Not interested in implementing a SQL parser from scratch? [sqlparse](https://pypi.org/project/sqlparse/) is available as a dependency if you'd like to use it.

## How to pass this stage

### 1. Write code to pass this stage

Head over to your editor / IDE and implement your solution.

If you want a quick look at what functions to use or how to structure your code, we recommend looking at [Code Examples](https://app.codecrafters.io/courses/sqlite/stages/az9/code-examples).

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
            - `argv[2]`: SQLite command to run e.g., `SELECT name FROM apples`
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
            ./your_program.sh sample.db "SELECT COUNT(*) FROM apples"
            ```
        - terminal output:
            ```
            4
            ```
    - ex.4: run `SELECT <column> FROM <table>` command
        - run in terminal:
            ```
            ./your_program.sh sample.db "SELECT name FROM apples"
            ```
        - terminal output:
            ```
            Granny Smith
            Fuji
            Honeycrisp
            Golden Delicious
            ```
- PEDAC: Data Structures And Algorithms
    - helper functions
        - `sql_of(database_file: file, target_table: string) -> string`
            - set int array `cell_offsets` to `parse_schema_cell_pointers(database_file)`
            - for int `offset` in `cell_offsets`,
                - set hashmap `cell_dict` to `parse_schema_leaf_cell(database_file, offset)`
                - set string `table_name` to `cell_dict["record"]["body"]["tbl_name"]`
                - if `table_name` is `target_table`,
                    - return `cell_dict["record"]["body"]["sql"]`
            - print `[Error]: Failed to find sql of table '<target_table>'`
            - return empty string
        - `column_index_of(sql_create: string, target_column: string) -> integer`
            - returns 0-indexed column integer
        - `parse_cell_pointers(database_file: file, rootpage: integer)`
            - TODO
        - `parse_leaf_cell(database_file: file, offset: integer, rootpage: integer) -> hashmap`
            - TODO
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
    - if `command` follows the regex `SELECT <col> FROM <table>`,
        - set hashmap `sql_dict` to `parse_sql(command)`
        - set string `column` to `sql_dict["column"]`
        - set string `table` to `sql_dict["table"]`
        - set string `sql_create` to `sql_of(database_file, table)`
        - set int `column_index` to `column_index_of(sql_create, column)`
        - set string `rootpage` to `rootpage_of(database_file, table)`
        - set string array `rows` empty
        - set int array `cell_offsets` to `parse_cell_pointers(database_file, offset)`
        - for int `offset` in `cell_offsets`,
            - set hashmap `cell_dict` to `parse_leaf_cell(database_file, offset, rootpage)`
            - append string `cell_dict["record"]["body"][column_index]` to `rows`
        - set string `rows_str` to joining each string in `rows` with a newline char `\n`
        - print `rows_str`
    - close file object at path `database_file`