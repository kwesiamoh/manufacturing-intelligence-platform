# Stage 3C Equipment Hierarchy

## Scope
Stage 3C creates only the equipment master needed to support the planned production, downtime, maintenance, quality, telemetry and energy relationships.

It does not generate:
- downtime events
- maintenance work orders
- sensor readings
- quality events
- energy consumption
- OEE values

## Standard line structure
PET beverage lines use a minimal common hierarchy:
1. blow moulder
2. air conveyor
3. filler/capper
4. inspection system
5. labeller
6. packer or shrink wrapper
7. pack conveyor
8. palletiser

Energy-drink can lines use:
1. can depalletiser
2. can rinser
3. filler/seamer
4. inspection system
5. packer
6. pack conveyor
7. palletiser

These equipment types are consistent with complete-line structures published by Krones and Sidel.

## Site utilities
Only three site-level utility assets are created because they directly support the project scope:
- compressed air system
- process water treatment system
- chilled-water system

No additional boiler house, wastewater plant, warehouse automation, laboratory equipment, forklifts, HVAC hierarchy, or building services are introduced at this stage.

## Data policy
All equipment records are synthetic master data.

Manufacturer, model, rated power, commissioning date and other unsupported attributes remain blank rather than being invented.

Real telemetry or benchmark datasets retain their original identities. Any later mapping from a real source pattern to this hierarchy must be explicitly marked as synthetic integration.
