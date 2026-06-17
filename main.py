import argparse
import logging
import pathlib
import typing

import pydantic

import destination.params
import destination.parqet
import handlers
import source.params
import source.scalable

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-s",
        "--source",
        help="source params file location",
    )
    parser.add_argument(
        "-d",
        "--destination",
        help="destination params file location",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable verbose logging",
    )
    parser.add_argument(
        "-f",
        "--fetch",
        action="store_true",
        help="fetch data from source, source params are required for this",
    )
    parser.add_argument(
        "-m",
        "--migration",
        action="store_true",
        help="enable migration mode: create a new csv file in the destination with a timestamp prefix containing only new fetched data",
    )

    args = parser.parse_args()

    # param validation
    if args.source is None or args.destination is None:
        parser.error("source and destination params must be provided")

    if args.migration:
        args.fetch = True

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s:%(funcName)s - %(message)s",
        datefmt="%d.%m %H:%M",
    )

    source_params: typing.Optional[pydantic.TypeAdapter] = None
    source_path = pathlib.Path(args.source)
    if not source_path.exists():
        parser.error(f"source params file not found: {args.source}")
    try:
        source_params = pydantic.TypeAdapter(
            source.params.AnyParamsModel
        ).validate_json(source_path.read_bytes())
    except (pydantic.ValidationError, ValueError) as e:
        parser.error(f"invalid source params file: {e}")

    destination_params: typing.Optional[pydantic.TypeAdapter] = None
    dest_path = pathlib.Path(args.destination)
    if not dest_path.exists():
        parser.error(f"destination params file not found: {args.destination}")
    try:
        destination_params = pydantic.TypeAdapter(
            destination.params.AnyParamsModel
        ).validate_json(dest_path.read_bytes())
    except (pydantic.ValidationError, ValueError) as e:
        parser.error(f"invalid destination params file: {e}")

    new_txn_ids: typing.Optional[typing.List[str]] = None
    if args.fetch:
        new_txn_ids = handlers.fetch(source_params)

    if destination_params is not None:
        handlers.from_source_to_destination(
            source_params,
            destination_params,
            migration_mode=args.migration,
            new_txn_ids=new_txn_ids,
        )
