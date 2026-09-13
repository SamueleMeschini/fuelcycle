"""Tests for component graph plumbing, independent of the solver."""

from openfc import Component, ComponentMap


def test_connection_applies_port_fractions() -> None:
    source = Component("Source", residence_time=10, initial_inventory=1.0)
    destination = Component("Destination", residence_time=10)
    source_port = source.add_output_port("out", outgoing_fraction=0.5)
    destination_port = destination.add_input_port("in", incoming_fraction=0.25)

    component_map = ComponentMap()
    component_map.add_component(source)
    component_map.add_component(destination)
    component_map.connect_ports(source, source_port, destination, destination_port)

    # The source port records the component outflow; fractions are applied to
    # the flow delivered to the receiving port.
    assert source_port.flow_rate == 0.1
    assert destination_port.flow_rate == 0.0125


def test_components_can_be_disconnected() -> None:
    source = Component("Source", residence_time=10)
    destination = Component("Destination", residence_time=10)
    source_port = source.add_output_port("out")
    destination_port = destination.add_input_port("in")
    component_map = ComponentMap()
    component_map.add_component(source)
    component_map.add_component(destination)
    component_map.connect_ports(source, source_port, destination, destination_port)

    component_map.disconnect_ports(source, source_port, destination, destination_port)

    assert component_map.connections["Source"] == {}
    assert component_map.connections["Destination"] == {}
