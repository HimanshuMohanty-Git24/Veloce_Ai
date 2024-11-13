from dataclasses import dataclass

@dataclass
class Vehicle:
    id: int
    model: str
    year: int
    vin: str
    current_mileage: float
    battery_level: float
    tire_pressure: dict
    engine_oil_life: float
    last_service_date: str

@dataclass
class MaintenanceRecord:
    id: int
    vehicle_id: int
    service_date: str
    service_type: str
    mileage: float
    description: str