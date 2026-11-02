# Your Task

In this stage, you'll add "number of tables" to your `.dbinfo` command's output.

## The `sqlite_schema` table

To get the number of tables in a SQLite database, you need to examine the database's [`sqlite_schema`](https://www.sqlite.org/schematab.html) table. The `sqlite_schema` table stores the database schema.

For each table, index, view, or trigger in the database, there's a corresponding row in `sqlite_schema`. The one exception is that there's no row for the `sqlite_schema` table itself.

To see what `sqlite_schema` looks like, run this command:
```
$ sqlite3 sample.db "SELECT * FROM sqlite_schema;"
```

In this challenge, you can assume that databases only contain tables—no indexes, views, or triggers. So, each row in `sqlite_schema` represents a table in the database. As a result, you can get the total number of tables in the database by getting the number of rows in `sqlite_schema`.


## Pages

A SQLite database file is made up of one or more [pages](https://www.sqlite.org/fileformat.html#pages). All tables, including `sqlite_schema`, are stored on one or more [table b-tree pages](https://www.sqlite.org/fileformat.html#b_tree_pages).

In this challenge, you can assume that the `sqlite_schema` table is small enough to fit entirely on a single page. (In reality, it can sometimes span multiple pages.) In order to get the number of rows in `sqlite_schema`, you need to read the `sqlite_schema` page.


### The `sqlite_schema` page

You'll learn more about b-tree pages in later stages. For now, here's what you need to know:

- The `sqlite_schema` page is always page 1, and it always begins at offset 0. The file header is a part of the page.
- The `sqlite_schema` page stores the rows of the `sqlite_schema` table in chunks of data called "cells." Each cell stores a single row.

So, the number of tables in the database is equal to the number of cells on the `sqlite_schema` page.

### Cell count

You can get the number of cells on the `sqlite_schema` page by looking at the `sqlite_schema` page header. The b-tree page header contains a 2-byte big-endian value that specifies number of cells on the page. See the [official documentation](https://www.sqlite.org/fileformat.html#b_tree_pages) for more information.

Note that the page header is separate from the file header. The page header appears directly after the file header.

## Tests

Here's how the tester will execute your program:
```
$ ./your_program.sh sample.db .dbinfo
```

Your program must print the following values:

- Database page size
- Number of tables

```
database page size: 4096
number of tables: 3
```

## Notes

- You may find it useful to read through `sample.db` and make sure you understand the file format, before working on a solution. To do this, you can run `hexdump -C sample.db`, or use a hex editor like [HexEd.it](https://hexed.it/).

## How to pass this stage

### 1. Write code to pass this stage

Head over to your editor / IDE and implement your solution.

If you want a quick look at what functions to use or how to structure your code, we recommend looking at [Code Examples](https://app.codecrafters.io/courses/sqlite/stages/ce0/code-examples).

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
            - `argv[2]`: SQLite command to run e.g., `.dbinfo`
    - output:
        - none
    - side effects:
        - prints to terminal stdout:
            ```
            database page size: <size of each page in database, in bytes>
            number of tables: <count of (table) pages in database>
            ```
    - questions
        - how to traverse + parse a table b-tree page in a SQLite database file?
            - TODO
        - how are table pages in a SQLite database structured (in binary)?
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
    - ex.1
        - run in terminal:
            ```
            ./your_program.sh sample.db .dbinfo
            ```
        - terminal output:
            ```
            database page size: 4096
            number of tables: 3
            ```
- PEDAC: Data Structures And Algorithms
    - set string `database_file_path` to `argv[1]`
    - set string `command` to `argv[2]`
    - if `command` is `.dbinfo`,
        - open file (descriptor) object `database_file` from path `database_file_path` as bytes with read permissions
        - set int `cell_count_start_pos` to 100 + 1 + 2 = 103
        - set `cell_count_bytes` to bytes read from `database_file` in index (inclusive) range [`cell_count_start_pos`, `cell_count_start_pos` + 1]
        - set int `cell_count` to `cell_count_bytes` converted to text via UTF-8 encoding, then converted to an int
        - print to terminal the database page size and number of tables `cell_count`
