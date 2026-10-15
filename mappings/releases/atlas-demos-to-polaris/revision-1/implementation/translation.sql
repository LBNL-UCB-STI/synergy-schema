-- Translation implementation SQL: DEMOS + ATLAS to POLARIS Demand Database
-- Implements translation contract 51ead67024fa32be5451125ee2d8c8fbedcef3fd02ce6cbd566b6e8c16f8e9a6

-- 1. Household Projection Query
WITH hh_members AS (
    SELECT
        m.household_id,
        count(m.person_id) AS persons,
        sum(CASE WHEN coalesce(e.employment_status, 0) IN (1, 4) THEN 1 ELSE 0 END) AS workers,
        max(CASE WHEN coalesce(d.relate, 99) = 1 THEN 1 ELSE 0 END) AS has_spouse,
        max(CASE WHEN coalesce(d.relate, 99) BETWEEN 2 AND 10 THEN 1 ELSE 0 END) AS has_other_relative,
        max(CASE WHEN coalesce(d.relate, 99) = 0 THEN coalesce(d.sex, 1) ELSE NULL END) AS head_gender
    FROM household_membership m
    LEFT JOIN person_demographics d ON m.person_id = d.person_id
    LEFT JOIN person_employment e ON m.person_id = e.person_id
    GROUP BY m.household_id
),
hh_vehicles AS (
    SELECT
        household_id,
        count(vehicle_id) AS vehicles
    FROM vehicles
    GROUP BY household_id
)
SELECT
    h.household_id AS household,
    h.household_id AS hhold,
    coalesce(loc.taz, 0) AS location,
    coalesce(mem.persons, 0) AS persons,
    coalesce(mem.workers, 0) AS workers,
    coalesce(veh.vehicles, 0) AS vehicles,
    CASE
        WHEN coalesce(dw.housing_unit_type, 1) = 5 THEN 11
        WHEN coalesce(dw.tenure, 1) IN (1, 3) THEN -- Own
            CASE
                WHEN coalesce(mem.has_spouse, 0) = 1 THEN 1
                WHEN coalesce(mem.has_other_relative, 0) = 1 THEN
                    CASE WHEN coalesce(mem.head_gender, 1) = 1 THEN 2 ELSE 3 END
                WHEN coalesce(mem.persons, 1) = 1 THEN 4
                ELSE 5
            END
        ELSE -- Rent (tenure 2 or other)
            CASE
                WHEN coalesce(mem.has_spouse, 0) = 1 THEN 6
                WHEN coalesce(mem.has_other_relative, 0) = 1 THEN
                    CASE WHEN coalesce(mem.head_gender, 1) = 1 THEN 7 ELSE 8 END
                WHEN coalesce(mem.persons, 1) = 1 THEN 9
                ELSE 10
            END
    END AS type,
    coalesce(inc.income, 0) AS income,
    0 AS bikes,
    coalesce(dw.housing_unit_type, 1) AS housing_unit_type,
    0 AS ecom,
    0.0 AS delRat,
    0 AS dispose_veh,
    coalesce(dw.has_residential_charging, 0) AS Has_Residential_Charging,
    0 AS num_groceries,
    0 AS num_meals,
    coalesce(dw.time_in_home, 0.0) AS time_in_home
FROM households h
LEFT JOIN household_location loc ON h.household_id = loc.household_id
LEFT JOIN household_dwelling dw ON h.household_id = dw.household_id
LEFT JOIN household_income inc ON h.household_id = inc.household_id
LEFT JOIN hh_members mem ON h.household_id = mem.household_id
LEFT JOIN hh_vehicles veh ON h.household_id = veh.household_id
ORDER BY h.household_id ASC;

-- 2. Person Projection Query
SELECT
    p.person_id AS person,
    m.household_id AS household,
    (ROW_NUMBER() OVER (
        PARTITION BY m.household_id
        ORDER BY
            coalesce(d.relate, 99) ASC,
            coalesce(d.age, 0) DESC,
            p.person_id ASC
    ) - 1) AS id,
    coalesce(s.school_location_id, -1) AS school_location_id,
    coalesce(e.work_location_id, -1) AS work_location_id,
    coalesce(d.age, 0) AS age,
    coalesce(e.worker_type, 0) AS worker_class,
    coalesce(s.education_level, 0) AS education,
    coalesce(e.industry, 0) AS industry,
    coalesce(e.employment_status, 0) AS employment,
    coalesce(d.sex, 1) AS gender,
    coalesce(e.income, 0) AS income,
    CASE WHEN coalesce(e.employment_status, 0) IN (1, 4) THEN 480 ELSE 0 END AS journey_to_work_arrival_time,
    coalesce(e.commute_mode, 0) AS journey_to_work_mode,
    0 AS journey_to_work_travel_time,
    CASE WHEN coalesce(e.employment_status, 0) IN (1, 4) THEN 1 ELSE 0 END AS journey_to_work_vehicle_occupancy,
    CASE
        WHEN coalesce(d.relate, 99) = 1 THEN 1
        WHEN coalesce(d.age, 0) < 15 THEN 5
        WHEN coalesce(d.relate, 99) = 0 THEN 1
        ELSE 5
    END AS marital_status,
    coalesce(d.race, 1) AS race,
    coalesce(d.hispanic, 0) AS hispanic,
    coalesce(s.school_type, 0) AS school_type,
    0 AS transit_pass,
    0 AS telecommute_frequency,
    0 AS work_at_home,
    0 AS work_hours,
    0 AS car_community,
    0 AS license
FROM people p
LEFT JOIN household_membership m ON p.person_id = m.person_id
LEFT JOIN person_demographics d ON p.person_id = d.person_id
LEFT JOIN person_schooling s ON p.person_id = s.person_id
LEFT JOIN person_employment e ON p.person_id = e.person_id
ORDER BY p.person_id ASC;

-- 3. Vehicle Projection Query
SELECT
    vehicle_id,
    household_id AS household,
    coalesce(type_id, 0) AS type_id,
    0 AS make,
    0 AS model,
    0 AS year,
    0 AS miles,
    0 AS osv
FROM vehicles
ORDER BY vehicle_id ASC;
