CREATE OR REPLACE TABLE `airquality.air_quality_limits` (
  pollutant STRING,
  limit_type STRING,
  value_ug_m3 FLOAT64,
  organization STRING,
  category STRING
);

INSERT INTO `airquality.air_quality_limits` VALUES
('PM10', '24h_mean', 45, 'WHO', 'Grenzwert'),
('PM10', 'annual', 15, 'WHO', 'Grenzwert'),
('PM2.5', '24h_mean', 15, 'WHO', 'Grenzwert'),
('PM2.5', 'annual', 5, 'WHO', 'Grenzwert'),
('NO2', '1h_mean', 200, 'WHO', 'Grenzwert'),
('NO2', 'annual', 10, 'WHO', 'Grenzwert'),
('PM10', '24h_mean', 50, 'EU', 'Grenzwert'),
('PM2.5', 'annual', 25, 'EU', 'Grenzwert'),
('NO2', '1h_mean', 200, 'EU', 'Grenzwert'),
('NO2', 'annual', 40, 'EU', 'Grenzwert');