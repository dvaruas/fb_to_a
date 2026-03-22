import logging

import destination.parqet
import source.scalable

_module_logger = logging.getLogger(__name__)


def fetch_scalable(source_params: source.scalable.Params):
    _module_logger.info("fetching and saving data from scalable")
    source_config = source.scalable.Config(source_params)
    source_orchestrator = source.scalable.Orchestrator(source_config)
    source_orchestrator.fetch_and_save()


def from_scalable_to_parqet(
    source_params: source.scalable.Params,
    destination_params: destination.parqet.Params,
):
    _module_logger.info("converting data from scalable to parqet")
    source_config = source.scalable.Config(source_params)
    destination_config = destination.parqet.Config(destination_params)
    source_orchestrator = source.scalable.Orchestrator(source_config)
    destination_orchestrator = destination.parqet.Orchestrator(destination_config)
    destination_orchestrator.from_source_scalable(source_orchestrator)
