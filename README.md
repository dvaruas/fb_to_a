# fb_to_a

Helper tool to migrate financial data from one platform to another.

## Currently supported platforms

* [scalable](https://de.scalable.capital/en)
* [parquet](https://parqet.com/de/)

## Currently supported migrations

* [scalable](source/scalable) -> [parquet](destination/parqet)

## How to use

* [one-time] install [uv](https://github.com/astral-sh/uv)
* [one-time] set up project using `uv sync`
* [one-time] set up data directory. 
  * The default is `$PWD/data`. 
  * It should contain `source.params.json` and `destination.params.json` files.
    * `source.params.json` contains the source platform credentials and other configuration.
    * `destination.params.json` contains the destination platform credentials and other configuration.
    * Examples of source and destination params can be found in the specific source and destination directories. Example [source](source/scalable/example.params.json) and [destination](destination/parqet/example.params.json) params.
* `uv run python main.py -h` to see the help message.
