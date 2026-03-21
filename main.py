import argparse
import logging
import pathlib

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
        required=True,
        help="source params file location",
    )
    parser.add_argument(
        "-d",
        "--destination",
        required=True,
        help="destination params file location",
    )
    parser.add_argument(
        "-v",
        "--verbose",
        action="store_true",
        help="enable verbose logging",
    )

    args = parser.parse_args()

    log_level = logging.DEBUG if args.verbose else logging.INFO
    logging.basicConfig(
        level=log_level,
        format="%(asctime)s - %(levelname)s - %(name)s:%(funcName)s - %(message)s",
    )

    source_params = pydantic.TypeAdapter(source.params.AnyParamsModel).validate_json(
        pathlib.Path(args.source).read_bytes()
    )
    destination_params = pydantic.TypeAdapter(
        destination.params.AnyParamsModel
    ).validate_json(pathlib.Path(args.destination).read_bytes())

    if isinstance(source_params, source.scalable.params.Params) and isinstance(
        destination_params, destination.parqet.params.Params
    ):
        handlers.from_scalable_to_parqet(source_params, destination_params)
    else:
        raise ValueError("no handler found for the given source and destination params")
