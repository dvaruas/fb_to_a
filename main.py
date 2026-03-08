import argparse
import logging

import source.scalable

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "-c",
        "--config",
        required=True,
        help="config file location",
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

    config = source.scalable.Config.from_json(args.config)

    source.scalable.Orchestrator(config).fetch_and_save()
