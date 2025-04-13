CREATE OR REPLACE VIEW `berliner-luft-dez.airquality.v_daily_pm_to_cigarettes` AS
WITH hourly_data AS (
  SELECT
    rm.station_id,
    TIMESTAMP_TRUNC(rm.measure_start_time, DAY) AS measurement_day,
    dc.code AS component_code,
    rm.value AS pm_concentration,
    TIMESTAMP_TRUNC(rm.measure_start_time, HOUR) AS measurement_hour
  FROM
    `berliner-luft-dez.airquality.raw_measures` rm
  JOIN
    `berliner-luft-dez.airquality.dim_components` dc
    ON rm.component_id = dc.id
  WHERE
    rm.scope_id = 2
    AND dc.code IN ('PM2')
    AND rm.value IS NOT NULL
  QUALIFY ROW_NUMBER() OVER (
    PARTITION BY station_id, measurement_hour, component_code 
    ORDER BY measure_start_time DESC
  ) = 1
)

SELECT
  station_id,
  measurement_day,
  component_code,
  ROUND(AVG(pm_concentration), 1) AS daily_avg_pm,
  COUNT(*) AS measure_count,
  CASE
    WHEN component_code = 'PM2' THEN 
      ROUND(AVG(pm_concentration) / 22, 2)
    ELSE NULL
  END AS cigarettes_equivalent,
  CASE
    WHEN component_code = 'PM2' THEN
      CASE
        WHEN AVG(pm_concentration) >= 22 THEN '1+ Zigarettenäquivalent'
        ELSE FORMAT('%.1f Zigaretten', AVG(pm_concentration) / 22)
      END
    ELSE 'nicht zutreffend'
  END AS cigarette_text,
  CASE
    WHEN COUNT(*) = 24 THEN 'vollständig'
    ELSE 'unvollständig'
  END AS data_quality
FROM hourly_data
GROUP BY
  station_id,
  measurement_day,
  component_code