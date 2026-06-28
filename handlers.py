import logging
import typing

import destination.params
import destination.parqet
import source.params
import source.scalable

_module_logger = logging.getLogger(__name__)


def fetch(source_params: source.params.Params) -> typing.Optional[typing.List[str]]:
    if isinstance(source_params, source.scalable.Params):
        return fetch_scalable(source_params)
    else:
        _module_logger.critical("unknown source params type: %s", source_params.name)
        return None


def from_source_to_destination(
    source_params: source.params.Params,
    destination_params: destination.params.Params,
    new_txn_ids: typing.List[str],
):
    if isinstance(source_params, source.scalable.Params) and isinstance(
        destination_params, destination.parqet.Params
    ):
        from_scalable_to_parqet(
            source_params,
            destination_params,
            new_txn_ids=new_txn_ids,
        )
    else:
        _module_logger.critical(
            "unknown source and destination params types: %s, %s",
            source_params.name,
            destination_params.name if destination_params else None,
        )


# fetch = scalable
def fetch_scalable(source_params: source.scalable.Params) -> typing.List[str]:
    _module_logger.info("fetching and saving data from scalable")
    source_config = source.scalable.Config(source_params)
    source_orchestrator = source.scalable.Orchestrator(source_config)
    return source_orchestrator.fetch_and_save()


# from_source_to_destination = scalable -> parqet
def from_scalable_to_parqet(
    source_params: source.scalable.Params,
    destination_params: destination.parqet.Params,
    new_txn_ids: typing.List[str],
):
    _module_logger.info("converting data from scalable to parqet")
    source_config = source.scalable.Config(source_params)
    destination_config = destination.parqet.Config(destination_params)
    source_orchestrator = source.scalable.Orchestrator(source_config)
    destination_orchestrator = destination.parqet.Orchestrator(destination_config)
    destination_orchestrator.from_source_scalable(
        source_orchestrator,
        new_txn_ids=new_txn_ids,
    )
