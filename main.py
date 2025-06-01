#!/usr/bin/env python3
import math
import typing

DIAMETERS = [80, 100, 125, 150, 160, 180, 200, 250]
AIR_DENSITY = 1.2  # kg/m3


class Node:
    def __init__(self, name: str):
        self.name: str = name
        self._diameter: typing.Optional[float] = None

    def required_flow(self) -> float:
        """
        In qbm/h.
        """
        raise NotImplementedError()

    def outflow(self) -> float:
        """
        In qbm/h
        """
        raise NotImplementedError()

    def inflow(self) -> float:
        """
        In qbm/h
        """
        raise NotImplementedError()

    def valid_flow(self) -> bool:
        return self.outflow() == self.inflow() and self.inflow() == self.required_flow()

    def diameter(self, airspeed: float = 1.0) -> float:
        if self._diameter is None:
            raise ValueError("Diameter not set. Use min_diameter() or first_fit_diameter() to set it.")
        return self._diameter

    def min_area(self, airspeed: float = 1):
        """
        :param airspeed: m/s
        :return: area in cm2
        """
        flow_per_second = self.flow() / 3600
        area_in_m2 = flow_per_second / airspeed
        area_in_cm2 = area_in_m2 * 10000
        return area_in_cm2

    def min_diameter(self, airspeed: float = 1.0) -> float:
        """
        :param airspeed: m/s
        :return: diameter in mm
        """
        diameter_in_cm = 2 * math.sqrt(self.area(airspeed) / math.pi)
        return diameter_in_cm * 10

    def first_fit_diameter(self, airspeed: float = 1.0) -> int:
        """
        :param airspeed: m/s
        :return: first diameter in cm that fits the area
        """
        diameter = self.min_diameter(airspeed)
        for d in DIAMETERS:
            if d >= diameter:
                return d
        return DIAMETERS[-1]

    def pressure_loss(self, airspeed: float) -> float:
        """
        :return: pressure loss of this element in Pa
        """
        raise NotImplementedError()

    def total_pressure_loss(self, airspeed: float) -> float:
        """
        :return: total pressure loss including inflows
        """
        raise NotImplementedError()


class AirOutlet(Node):
    def __init__(self, name: str, required_flow: float):
        super().__init__(name)
        self._required_flow = required_flow
        self._inflow: float = 0
        self._outflow: float = 0

    def required_flow(self) -> float:
        return self._required_flow

    def outflow(self) -> float:
        return self._inflow

    def inflow(self) -> float:
        return self._outflow

    def pressure_loss(self, airspeed: float) -> float:
        return 0

    def total_pressure_loss(self, airspeed: float) -> float:
        return 0


class AirInlet(Node):
    def __init__(self, name: str, required_flow: float):
        super().__init__(name)
        self._required_flow = required_flow
        self._inflow: float = 0
        self._outflow: float = 0

    def required_flow(self) -> float:
        return self._required_flow

    def outflow(self) -> float:
        return self._outflow

    def inflow(self) -> float:
        return self._inflow

    def pressure_loss(self, airspeed: float) -> float:
        return 0

    def total_pressure_loss(self, airspeed: float) -> float:
        return 0


class Pipe(Node):
    def __init__(self, name: str, length: float):
        """
        :param length: in m
        """
        super().__init__(name)
        self._length = length
        self._inflow_node: typing.Optional[Node]
        self._outflow_node: typing.Optional[Node]
        self._required_flow: float = 0

    def set_inflow(self, inflow_node: Node) -> None:
        self._inflow_node = inflow_node

    def set_outflow(self, outflow_node: Node) -> None:
        self._outflow_node = outflow_node

    def required_flow(self) -> float:
        return self._required_flow

    def length(self) -> float:
        return self._length

    def pressure_loss(self, airspeed: float) -> float:
        # https://www.studysmarter.de/ausbildung/ausbildung-in-handwerk-produktion-und-gewerbe/heizungsbauer/druckverluste-lueftung/
        f = 0.02
        L_in_m = self.length()
        D_in_m = self.diameter(airspeed) / 100
        air_density = 1.2
        airspeed_in_m_per_s = airspeed
        return f * (L_in_m / D_in_m) * (air_density / 2) * airspeed_in_m_per_s ** 2

    def total_pressure_loss(self, airspeed: float) -> float:
        """
        :return: total pressure loss including inflows
        """
        return self.pressure_loss(airspeed) + self._inflow_node.total_pressure_loss(airspeed)


class PipeElbow90(Node):
    def __init__(self, name: str, required_flow: typing.Optional[Node] = None):
        super().__init__(name)
        self._outflow: typing.Optional[Node] = outflow

    def set_outflow(self, outflow: Node) -> None:
        self._outflow = outflow

    def flow(self) -> float:
        return self._outflow.flow()

    def pressure_loss(self, airspeed: float) -> float:
        # https://de.wikipedia.org/wiki/Rohrreibungszahl
        zeta = 0.4
        return zeta * AIR_DENSITY / 2 * airspeed ** 2

    def total_pressure_loss(self, airspeed: float) -> float:
        """
        :return: total pressure loss including inflows
        """
        return self.pressure_loss(airspeed) + self._outflow.total_pressure_loss(airspeed)


class PipeElbow45(Node):
    def __init__(self, name: str, outflow: typing.Optional[Node] = None):
        super().__init__(name)
        self._outflow: typing.Optional[Node] = outflow

    def set_outflow(self, outflow: Node) -> None:
        self._outflow = outflow

    def flow(self) -> float:
        return self._outflow.flow()

    def pressure_loss(self, airspeed: float) -> float:
        # https://de.wikipedia.org/wiki/Rohrreibungszahl
        # https://www.schweizer-fn.de/zeta/rohrbogen/rohrbogen.php
        zeta = 0.4 * 0.62
        return zeta * AIR_DENSITY / 2 * airspeed ** 2

    def total_pressure_loss(self, airspeed: float) -> float:
        """
        :return: total pressure loss including inflows
        """
        return self.pressure_loss(airspeed) + self._outflow.total_pressure_loss(airspeed)


class TFitting(Node):
    """
    T-Fitting with 90° angle
    0 -- 1
      |
      v
      2
    """

    def __init__(self, name: str, outflow: typing.Optional[Node] = None):
        super().__init__(name)
        self._outflow: typing.Optional[Node] = outflow

    def set_outflow(self, outflow: Node) -> None:
        self._outflow = outflow

    def flow(self) -> float:
        return self._outflow.flow()

    def pressure_loss(self, airspeed: float) -> float:
        # https://de.wikipedia.org/wiki/Rohrreibungszahl
        zeta = 0.4 * 0.62
        return zeta * AIR_DENSITY / 2 * airspeed ** 2

    def total_pressure_loss(self, airspeed: float) -> float:
        """
        :return: total pressure loss including inflows
        """
        return self.pressure_loss(airspeed) + self._outflow.total_pressure_loss(airspeed)


schlafzimmer = AirOutlet("Schlafzimmer", 60)
kinderzimmer1 = AirOutlet("Kinderzimmer 1", 25)
kinderzimmer2 = AirOutlet("Kinderzimmer 2", 25)
abstellraum = AirOutlet("Abstellraum", 50)
Esszimmer = AirOutlet("Esszimmer", 60)

bad_og = AirInlet("Bad OG", 30)
bad_eg = AirInlet("Bad EG", 30)
wc_og = AirInlet("WC OG", 20)
wc_eg = AirInlet("WC EG", 20)
hwr = AirInlet("HWR", 30)

all_outlets = [
    schlafzimmer,
    kinderzimmer1,
    kinderzimmer2,
    abstellraum,
    Esszimmer
]

all_inlets = [
    bad_og,
    bad_eg,
    wc_og,
    wc_eg,
    hwr
]

total_outlet_flow = sum([outlet.flow() for outlet in all_outlets])
total_inlet_flow = sum([inlet.flow() for inlet in all_inlets])
heuboden = AirInlet("Heuboden", total_outlet_flow - total_inlet_flow)

print("Total outlet flow: ", sum([outlet.flow() for outlet in all_outlets]), "qbm/h")
print("Total inlet flow: ", sum([inlet.flow() for inlet in all_inlets]), "qbm/h")

print("Outlets:")
for outlet in all_outlets:
    print(f"{outlet.name}: {outlet.flow()} -> A={outlet.area()}, DN={outlet.diameter()} cm")

print("Inlets:")
for inlet in all_inlets:
    print(f"{inlet.name}: {inlet.flow()} -> A={inlet.area()}, DN={inlet.diameter()} cm")

print(f"{heuboden.name}: {heuboden.flow()} -> A={heuboden.area()}, DN={heuboden.diameter()} cm")

schlafzimmer_anbindung: typing.List[Node] = [schlafzimmer]
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer Nord", 5, schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer Nord/Ost", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer Ost", 4, schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer Flur Einführung", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer - Flur", 7, schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer - Flur - Technikraum", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer - Technikraum", 5, schlafzimmer_anbindung[-1]))

esszimmer_anbidung: typing.List[Node] = [Esszimmer]
esszimmer_anbidung.append(PipeElbow90("Esszimmer", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer Nord", 11, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer Nord Steigschacht", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer Nord Steigschacht", 4, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer - Steigschacht - Technikraum", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer - Technikraum", 2, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(
    PipeElbow90("Esszimmer - Steigschacht - Technikraum zum Hauptverteiler", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer - Technikraum zum Hauptverteiler", 2, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(
    PipeElbow90("Esszimmer - Steigschacht - Technikraum Hauptverteiler Umkehrung Teil 1", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(
    PipeElbow90("Esszimmer - Steigschacht - Technikraum Hauptverteiler Umkehrung Teil 2", esszimmer_anbidung[-1]))

kinderzimmer2_anbindung: typing.List[Node] = [kinderzimmer2]
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 Süd Hoch", 4, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow45("Kinderzimmer 2 Süd First", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 Süd Runter", 4, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Flur", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 - Ost", 3.5, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Ost", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 - Ost", 0.5, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Nord", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 - Ost - Steigschacht", 0.5, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Steigschacht", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 - Steigschacht", 4, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Steigschacht - Flur", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 - Flur", 4, kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Steigschacht - Flur", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(PipeElbow90("Kinderzimmer 2 - Steigschacht - Flur", kinderzimmer2_anbindung[-1]))
kinderzimmer2_anbindung.append(Pipe("Kinderzimmer 2 - Flur - Technikraum", 4, kinderzimmer2_anbindung[-1]))

print(
    f"Schlafzimmer Anbindung: flow={schlafzimmer_anbindung[-1].flow()}, pressure_loss={schlafzimmer_anbindung[-1].total_pressure_loss(1)}")
print(
    f"Esszimmer Anbindung: flow={esszimmer_anbidung[-1].flow()}, pressure_loss={esszimmer_anbidung[-1].total_pressure_loss(1)}")
print(
    f"Kinderzimmer 2 Anbindung: flow={kinderzimmer2_anbindung[-1].flow()}, pressure_loss={kinderzimmer2_anbindung[-1].total_pressure_loss(1)}")
