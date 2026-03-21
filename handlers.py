import destination.parqet
import source.scalable


def from_scalable_to_parqet(
    source_params: source.scalable.params.Params,
    destination_params: destination.parqet.params.Params,
):
    source_config = source.scalable.Config(source_params)
    destination_config = destination.parqet.Config(destination_params)
    source_orchestrator = source.scalable.Orchestrator(source_config)
    destination_orchestrator = destination.parqet.Orchestrator(destination_config)
    destination_orchestrator.from_source_scalable(source_orchestrator)
