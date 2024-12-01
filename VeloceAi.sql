CREATE DATABASE IF NOT EXISTS `veloce_ai`;
USE `veloce_ai`;

DROP TABLE IF EXISTS `emergency_contacts`;
CREATE TABLE `emergency_contacts` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `relation` varchar(50) NOT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `emergency_contacts` VALUES (1,'Himanshu Mohanty','+917008719907','brother');

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

DROP TABLE IF EXISTS `police_stations`;
CREATE TABLE `police_stations` (
  `id` int NOT NULL AUTO_INCREMENT,
  `name` varchar(100) NOT NULL,
  `address` varchar(255) NOT NULL,
  `phone_number` varchar(15) NOT NULL,
  `latitude` decimal(10,8) NOT NULL,
  `longitude` decimal(11,8) NOT NULL,
  PRIMARY KEY (`id`)
);

INSERT INTO `police_stations` VALUES 
(1,'Patia Police Station','Patia Square, Bhubaneswar','+917008719907',20.35182900,85.82493600),
(2,'Chandrasekharpur Police Station','Chandrasekharpur, Bhubaneswar','+917008719907',20.34324200,85.81987300);

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

INSERT INTO `vehicles` VALUES 
(1,'ID.4',2024,'WVGZZZE2ZMP123456',15000.5,85.5,'{\"FL\": 32, \"FR\": 32, \"RL\": 32, \"RR\": 32}',75,'2024-01-15'),
(2,'Golf GTI',2023,'WVWZZZ1KZNW987654',22000,NULL,'{\"FL\": 35, \"FR\": 35, \"RL\": 35, \"RR\": 34}',45,'2023-12-01');
