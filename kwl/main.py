#!/usr/bin/env python3
import math
import sys
import typing

diamaters = [80, 100, 125, 150, 160, 180, 200, 250]

AIR_DENSITY = 1.2  # kg/m3

class Diamater:
    def __init__(self, diamater_in_mm: typing.Union[int, float]):
        self.diamater_in_mm = int(diamater_in_mm)

    def __str__(self):
        return f"DN{self.diamater_in_mm}"

class Node:
    def __init__(self, name: str):
        self.name: str = name

    def flow(self) -> float:
        """
        In qbm/h
        """
        raise NotImplementedError()

    def area(self, airspeed: float=1):
        """
        :param airspeed: m/s
        :return: area in cm2
        """
        flow_per_second = self.flow() / 3600
        area_in_m2 = flow_per_second / airspeed
        area_in_cm2 = area_in_m2 * 10000
        return area_in_cm2

    def diameter(self, airspeed: float=1.0) -> Diamater:
        """
        :param airspeed: m/s
        :return: diameter in cm
        """
        diameter_in_cm = 2 * math.sqrt(self.area(airspeed) / math.pi)
        return Diamater(diameter_in_cm*10)

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
    def __init__(self, name: str, flow_rate: float):
        super().__init__(name)
        self.flow_rate = flow_rate

    def flow(self) -> float:
        return self.flow_rate

    def pressure_loss(self, airspeed: float) -> float:
        return 0

    def total_pressure_loss(self, airspeed: float) -> float:
        return 0


class AirInlet(Node):
    def __init__(self, name: str, flow_rate: float):
        super().__init__(name)
        self.flow_rate = flow_rate

    def flow(self) -> float:
        return self.flow_rate

    def pressure_loss(self, airspeed: float) -> float:
        return 0

    def total_pressure_loss(self, airspeed: float) -> float:
        return 0


class Pipe(Node):
    def __init__(self, name: str, length: float, outflow: typing.Optional[Node]):
        """
        :param length: in m
        """
        super().__init__(name)
        self._length = length
        self._outflow: typing.Optional[Node] = outflow

    def set_outflow(self, outflow: Node) -> None:
        self._outflow = outflow

    def flow(self) -> float:
        return self._outflow.flow()

    def length(self) -> float:
        return self._length

    def pressure_loss(self, airspeed: float) -> float:
        # https://www.studysmarter.de/ausbildung/ausbildung-in-handwerk-produktion-und-gewerbe/heizungsbauer/druckverluste-lueftung/
        f = 0.02
        L_in_m = self.length()
        D_in_m = self.diameter(airspeed)/100
        air_density = 1.2
        airspeed_in_m_per_s = airspeed
        return f * (L_in_m / D_in_m) * (air_density / 2) * airspeed_in_m_per_s ** 2

    def total_pressure_loss(self, airspeed: float) -> float:
        """
        :return: total pressure loss including inflows
        """
        return self.pressure_loss(airspeed) + self._outflow.total_pressure_loss(airspeed)


class PipeElbow90(Node):
    def __init__(self, name: str, outflow: typing.Optional[Node] = None):
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

schlafzimmer = AirOutlet("Schlafzimmer", 50)
kinderzimmer1 = AirOutlet("Kinderzimmer 1", 30)
kinderzimmer2 = AirOutlet("Kinderzimmer 2", 30)
wohnzimmer_1 = AirOutlet("Wohnzimmer NW", 45)
wohnzimmer_2 = AirOutlet("Wohnzimmer NO", 45)
buero = AirOutlet("Büro", 30)
keller_zuluft = AirOutlet("Keller", 0.3*50*2.72) # Luftwechsel 0.3/h
dachboden_zuluft = AirOutlet("Dachboden", 0.3*23*12.75) # Luftwechsel 0.3/h

bad_eltern = AirInlet("Elternbad", schlafzimmer.flow_rate)
bad_kind1 = AirInlet("Bad Kind 1", 30)
bad_kind2 = AirInlet("Bad Kind 2", 30)
wc = AirInlet("WC", 20)
kueche_1 = AirInlet("Küche 1", wohnzimmer_1.flow_rate)
kueche_2 = AirInlet("Küche 2", wohnzimmer_2.flow_rate)
keller_abluft = AirInlet("Keller", keller_zuluft.flow_rate)
dachbode_abluft = AirInlet("Dachboden", dachboden_zuluft.flow_rate)

all_outlets = [
    schlafzimmer,
    kinderzimmer1,
    kinderzimmer2,
    wohnzimmer_1,
    wohnzimmer_2,
    buero,
    keller_zuluft,
    dachboden_zuluft
]

all_inlets = [
    bad_eltern,
    bad_kind1,
    bad_kind2,
    wc,
    kueche_1,
    kueche_2,
    keller_abluft,
    dachbode_abluft
]

total_outlet_flow = sum([outlet.flow() for outlet in all_outlets])
total_inlet_flow = sum([inlet.flow() for inlet in all_inlets])
residual_flow = AirInlet("Residualfluss", total_outlet_flow - total_inlet_flow)
building_inflow = AirOutlet("Zuluft", total_outlet_flow)
building_outflow = AirInlet("Fortluft", total_outlet_flow)

print("Total outlet flow: ", sum([outlet.flow() for outlet in all_outlets]), "qbm/h")
print("Total inlet flow: ", sum([inlet.flow() for inlet in all_inlets]), "qbm/h")

print("Outlets:")
for outlet in all_outlets:
    print(f"{outlet.name}: {outlet.flow()} -> A={outlet.area()}, DN={outlet.diameter()}")

print("Inlets:")
for inlet in all_inlets:
    print(f"{inlet.name}: {inlet.flow()} -> A={inlet.area()}, DN={inlet.diameter()}")

print("Zuluft/Fortluft:")
print(f"{building_inflow.name}: {building_inflow.flow()} -> A={building_inflow.area(airspeed=2)}, DN={building_inflow.diameter(airspeed=2)}")
print(f"{building_outflow.name}: {building_outflow.flow()} -> A={building_outflow.area(airspeed=2)}, DN={building_outflow.diameter(airspeed=2)}")

if residual_flow.flow() > 0:
    print(f"{residual_flow.name}: {residual_flow.flow()} -> A={residual_flow.area()}, DN={residual_flow.diameter()}")
else:
    print("No residual flow")
    
sys.exit(0)


schlafzimmer_anbindung: typing.List[Node] = [schlafzimmer]
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer Nord", 5, schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer Nord/Ost", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer Ost", 4, schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer Flur Einführung", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer - Flur", 7, schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(PipeElbow90("Schlafzimmer - Flur - Technikraum", schlafzimmer_anbindung[-1]))
schlafzimmer_anbindung.append(Pipe("Schlafzimmer - Technikraum", 5, schlafzimmer_anbindung[-1]))

esszimmer_anbidung : typing.List[Node] = [Esszimmer]
esszimmer_anbidung.append(PipeElbow90("Esszimmer", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer Nord", 11, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer Nord Steigschacht", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer Nord Steigschacht", 4, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer - Steigschacht - Technikraum", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer - Technikraum", 2, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer - Steigschacht - Technikraum zum Hauptverteiler", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(Pipe("Esszimmer - Technikraum zum Hauptverteiler", 2, esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer - Steigschacht - Technikraum Hauptverteiler Umkehrung Teil 1", esszimmer_anbidung[-1]))
esszimmer_anbidung.append(PipeElbow90("Esszimmer - Steigschacht - Technikraum Hauptverteiler Umkehrung Teil 2", esszimmer_anbidung[-1]))



kinderzimmer2_anbindung : typing.List[Node] = [kinderzimmer2]
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


print(f"Schlafzimmer Anbindung: flow={schlafzimmer_anbindung[-1].flow()}, pressure_loss={schlafzimmer_anbindung[-1].total_pressure_loss(1)}")
print(f"Esszimmer Anbindung: flow={esszimmer_anbidung[-1].flow()}, pressure_loss={esszimmer_anbidung[-1].total_pressure_loss(1)}")
print(f"Kinderzimmer 2 Anbindung: flow={kinderzimmer2_anbindung[-1].flow()}, pressure_loss={kinderzimmer2_anbindung[-1].total_pressure_loss(1)}")
