import argparse
import logging
import pathlib
import typing
import sys
import pydantic

import destination.params
import handlers
import source.params

_module_logger = logging.getLogger(__name__)

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

    # fetch source
    new_txn_ids = handlers.fetch(source_params)

    if new_txn_ids is None or len(new_txn_ids) == 0:
        _module_logger.warning("No new transactions found, exiting....")
        sys.exit(0)

    # save source to destination
    handlers.from_source_to_destination(
        source_params,
        destination_params,
        new_txn_ids=new_txn_ids,
    )
