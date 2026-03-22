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

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s:%(funcName)s - %(message)s",
        datefmt="%d.%m %H:%M",
    )

    source_params: typing.Optional[pydantic.TypeAdapter] = None
    if args.source is not None:
        source_params = pydantic.TypeAdapter(
            source.params.AnyParamsModel
        ).validate_json(pathlib.Path(args.source).read_bytes())
    destination_params: typing.Optional[pydantic.TypeAdapter] = None
    if args.destination is not None:
        destination_params = pydantic.TypeAdapter(
            destination.params.AnyParamsModel
        ).validate_json(pathlib.Path(args.destination).read_bytes())

    # if fetch is true, then source_params must be provided
    if args.fetch and source_params is None:
        parser.error("source params must be provided when fetch is true")

    if args.fetch:
        if isinstance(source_params, source.scalable.Params):
            handlers.fetch_scalable(source_params)

    # scalable -> parqet
    if isinstance(source_params, source.scalable.Params) and isinstance(
        destination_params, destination.parqet.Params
    ):
        handlers.from_scalable_to_parqet(source_params, destination_params)
