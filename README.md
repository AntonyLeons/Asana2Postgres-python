# Asana2Postgres-Python

- Create a database
- Ensure environment variables are set or coded
  This uses Metabase variables and an `ASANA_TOKEN` variable
- Run import then sync


## Compile with 

```
gradle jar
```
in respective folders.

## Run with

```
java -jar <NAME> <PROJECT_ID> <TABLE_NAME>
```
`<PROJECT_ID> <TABLE_NAME> ` are optional and default is support tickets table, however these must be in order so a `<PROJECT_ID>` must be set to set a `<TABLE_NAME>`.
Database creation is NOT supported and to change database edit the py file.
