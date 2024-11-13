CREATE DATABASE IF NOT EXISTS `veloce_ai`;
USE `veloce_ai`;

DROP TABLE IF EXISTS `maintenance_records`;

CREATE TABLE `maintenance_records` (
  `id` int NOT NULL AUTO_INCREMENT,
  `vehicle_id` int DEFAULT NULL,
  `service_date` date DEFAULT NULL,
  `service_type` varchar(255) DEFAULT NULL,
  `mileage` float DEFAULT NULL,
  `description` text,
  PRIMARY KEY (`id`),
  KEY `vehicle_id` (`vehicle_id`),
  CONSTRAINT `maintenance_records_ibfk_1` FOREIGN KEY (`vehicle_id`) REFERENCES `vehicles` (`id`)
);

DROP TABLE IF EXISTS `vehicles`;

CREATE TABLE `vehicles` (
  `id` int NOT NULL AUTO_INCREMENT,
  `model` varchar(255) DEFAULT NULL,
  `year` int DEFAULT NULL,
  `vin` varchar(17) DEFAULT NULL,
  `current_mileage` float DEFAULT NULL,
  `battery_level` float DEFAULT NULL,
  `tire_pressure` json DEFAULT NULL,
  `engine_oil_life` float DEFAULT NULL,
  `last_service_date` date DEFAULT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `vehicles` (`id`, `model`, `year`, `vin`, `current_mileage`, `battery_level`, `tire_pressure`, `engine_oil_life`, `last_service_date`) VALUES
(1, 'ID.4', 2024, 'WVGZZZE2ZMP123456', 15000.5, 85.5, '{"FL": 32, "FR": 32, "RL": 32, "RR": 32}', 75, '2024-01-15'),
(2, 'Golf GTI', 2023, 'WVWZZZ1KZNW987654', 22000, NULL, '{"FL": 35, "FR": 35, "RL": 35, "RR": 34}', 45, '2023-12-01');
