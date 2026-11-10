#!/usr/bin/env python3
"""Reproducible power and thermal calculations used by the IDE-005 reference.

Every function is plain arithmetic on stated inputs. None of them describes a real
facility: the results show what follows from the inputs, nothing more. Units are
part of each function name or argument so that power (kW) and energy (kWh) cannot
be mixed by accident.
"""

from __future__ import annotations

HOURS_PER_YEAR = 8760


def energy_kwh(power_kw: float, hours: float) -> float:
    """Energy (kWh) = power (kW) x time (h)."""
    if power_kw < 0 or hours < 0:
        raise ValueError("power and time must be non-negative")
    return power_kw * hours


def average_power_gw(energy_twh: float, hours: float = HOURS_PER_YEAR) -> float:
    """Average power (GW) over a period from energy (TWh): 1 TWh / 1 h = 1,000 GW."""
    if hours <= 0:
        raise ValueError("hours must be positive")
    return energy_twh * 1000 / hours


def input_power_kw(output_kw: float, efficiency: float) -> float:
    """Input power needed to deliver an output through a converter of given efficiency (0-1]."""
    if not 0 < efficiency <= 1:
        raise ValueError("efficiency must be in (0, 1]")
    return output_kw / efficiency


def conversion_loss_kw(output_kw: float, efficiency: float) -> float:
    """Power dissipated as heat in a converter: input minus output."""
    return input_power_kw(output_kw, efficiency) - output_kw


def redundant_capacity_kw(units: int, unit_kw: float, redundancy: str) -> float:
    """Capacity available with all units installed and the stated redundancy scheme.

    'N' uses every unit; 'N+N' holds half in reserve; 'N+1' holds one unit in reserve.
    """
    if units <= 0 or unit_kw <= 0:
        raise ValueError("units and unit rating must be positive")
    installed = units * unit_kw
    if redundancy == "N":
        return installed
    if redundancy == "N+N":
        if units % 2:
            raise ValueError("N+N needs an even number of units")
        return installed / 2
    if redundancy == "N+1":
        return installed - unit_kw
    raise ValueError(f"unknown redundancy scheme: {redundancy}")


def dc_power_kw(current_a: float, voltage_v: float) -> float:
    """DC power (kW) = current (A) x voltage (V) / 1000."""
    return current_a * voltage_v / 1000


def coolant_mass_flow_kg_s(heat_kw: float, cp_kj_per_kg_k: float, delta_t_k: float) -> float:
    """Mass flow needed to carry a heat load: m = Q / (cp x dT)."""
    if cp_kj_per_kg_k <= 0 or delta_t_k <= 0:
        raise ValueError("specific heat and temperature rise must be positive")
    return heat_kw / (cp_kj_per_kg_k * delta_t_k)


def coolant_volume_flow_lpm(heat_kw: float, cp_kj_per_kg_k: float, delta_t_k: float,
                            density_kg_per_l: float) -> float:
    """Volume flow (L/min) for a heat load, from mass flow and coolant density."""
    if density_kg_per_l <= 0:
        raise ValueError("density must be positive")
    return coolant_mass_flow_kg_s(heat_kw, cp_kj_per_kg_k, delta_t_k) / density_kg_per_l * 60


def pue(total_facility_energy_kwh: float, it_equipment_energy_kwh: float) -> float:
    """PUE = total facility energy / IT equipment energy, over the same period and boundary."""
    if it_equipment_energy_kwh <= 0:
        raise ValueError("IT equipment energy must be positive")
    if total_facility_energy_kwh < it_equipment_energy_kwh:
        raise ValueError("total facility energy cannot be below IT equipment energy")
    return total_facility_energy_kwh / it_equipment_energy_kwh


def wue_l_per_kwh(annual_site_water_l: float, it_equipment_energy_kwh: float) -> float:
    """Site WUE (L/kWh) = annual site water use / IT equipment energy."""
    if it_equipment_energy_kwh <= 0:
        raise ValueError("IT equipment energy must be positive")
    return annual_site_water_l / it_equipment_energy_kwh


def worked_examples() -> dict[str, float]:
    """The values shown on /power-and-thermal-limits/ section 10, computed from their inputs."""
    return {
        "psu_installed_kw": redundant_capacity_kw(48, 5.5, "N"),
        "psu_n_plus_n_kw": redundant_capacity_kw(48, 5.5, "N+N"),
        "busbar_kw_at_50v": dc_power_kw(1400, 50),
        "busbar_kw_at_51v": dc_power_kw(1400, 51),
        "su_rack_sum_mw": 8 * 120 / 1000,
        "rack_input_kw_at_97pct": input_power_kw(120, 0.97),
        "rack_loss_kw_at_97pct": conversion_loss_kw(120, 0.97),
        "rack_energy_mwh_per_year": energy_kwh(120, HOURS_PER_YEAR) / 1000,
        "flow_lpm_dt10": coolant_volume_flow_lpm(120, 4.18, 10, 1.0),
        "flow_lpm_dt15": coolant_volume_flow_lpm(120, 4.18, 15, 1.0),
        "us_2023_average_gw": average_power_gw(176),
        "us_2028_low_average_gw": average_power_gw(325),
        "us_2028_high_average_gw": average_power_gw(580),
        "accelerator_board_kw_8x750w": 8 * 750 / 1000,
        "pue_example": pue(1200, 1000),
    }


if __name__ == "__main__":
    for name, value in worked_examples().items():
        print(f"{name}: {value:.2f}")
