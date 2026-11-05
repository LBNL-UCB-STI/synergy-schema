-- Translation implementation SQL: DEMOS + ATLAS to POLARIS Demand Database
-- Implements translation contract d5f03bb6ebde1f7f88679f6475561f372e99d4533e89202664405e9985840d05

-- 1. Household Projection Query
WITH hh_members AS (
    SELECT
        m.household_id,
        count(m.person_id) AS persons,
        sum(coalesce(x_p2.is_at_work, 0)) AS workers,
        max(CASE WHEN coalesce(d.relate, 99) = 1 THEN 1 ELSE 0 END) AS has_spouse,
        max(CASE WHEN coalesce(d.relate, 99) BETWEEN 2 AND 10 THEN 1 ELSE 0 END) AS has_other_relative,
        max(CASE WHEN coalesce(d.relate, 99) = 0 THEN coalesce(d.sex, 1) ELSE NULL END) AS head_gender
    FROM household_membership m
    LEFT JOIN person_demographics d ON m.person_id = d.person_id
    LEFT JOIN person_employment e ON m.person_id = e.person_id
    LEFT JOIN _contract_crosswalk_x_p2 x_p2 ON coalesce(e.employment_status, 0) = x_p2.employment_status
    GROUP BY m.household_id
),
hh_vehicles AS (
    SELECT
        household_id,
        count(vehicle_id) AS vehicles
    FROM vehicles
    GROUP BY household_id
),
hh_composition AS (
    SELECT
        h.household_id,
        loc.taz,
        dw.housing_unit_type,
        dw.tenure,
        dw.has_residential_charging,
        dw.time_in_home,
        inc.income,
        mem.persons,
        mem.workers,
        veh.vehicles,
        CASE
            WHEN coalesce(dw.housing_unit_type, def.housing_unit_type) = 5 THEN 1
            ELSE 0
        END AS is_gq,
        CASE
            WHEN coalesce(dw.housing_unit_type, def.housing_unit_type) = 5 THEN 0
            WHEN coalesce(dw.tenure, 1) IN (1, 3) THEN 1
            ELSE 0
        END AS is_owner,
        CASE
            WHEN coalesce(dw.housing_unit_type, def.housing_unit_type) = 5 THEN 0
            WHEN coalesce(mem.has_spouse, 0) = 1 THEN 1
            WHEN coalesce(mem.has_other_relative, 0) = 1 THEN
                CASE WHEN coalesce(mem.head_gender, 1) = 1 THEN 2 ELSE 3 END
            WHEN coalesce(mem.persons, 1) = 1 THEN 4
            ELSE 5
        END AS hht
    FROM households h
    CROSS JOIN _contract_defaults_household def
    LEFT JOIN household_location loc ON h.household_id = loc.household_id
    LEFT JOIN household_dwelling dw ON h.household_id = dw.household_id
    LEFT JOIN household_income inc ON h.household_id = inc.household_id
    LEFT JOIN hh_members mem ON h.household_id = mem.household_id
    LEFT JOIN hh_vehicles veh ON h.household_id = veh.household_id
)
SELECT
    c.household_id AS household,
    c.household_id AS hhold,
    coalesce(c.taz, def.location) AS location,
    coalesce(c.persons, 0) AS persons,
    coalesce(c.workers, 0) AS workers,
    coalesce(c.vehicles, 0) AS vehicles,
    x_h2.polaris_type AS type,
    coalesce(c.income, 0) AS income,
    def.bikes AS bikes,
    coalesce(c.housing_unit_type, def.housing_unit_type) AS housing_unit_type,
    def.ecom AS ecom,
    def.delRat AS delRat,
    def.dispose_veh AS dispose_veh,
    coalesce(c.has_residential_charging, def.Has_Residential_Charging) AS Has_Residential_Charging,
    def.num_groceries AS num_groceries,
    def.num_meals AS num_meals,
    coalesce(c.time_in_home, def.time_in_home) AS time_in_home
FROM hh_composition c
CROSS JOIN _contract_defaults_household def
LEFT JOIN _contract_crosswalk_x_h2 x_h2
    ON c.is_gq = x_h2.is_gq
    AND c.is_owner = x_h2.is_owner
    AND c.hht = x_h2.hht
ORDER BY c.household_id ASC;

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
    coalesce(s.school_location_id, def.school_location_id) AS school_location_id,
    coalesce(e.work_location_id, def.work_location_id) AS work_location_id,
    coalesce(d.age, 0) AS age,
    coalesce(e.worker_type, def.worker_class) AS worker_class,
    coalesce(s.education_level, 0) AS education,
    coalesce(e.industry, def.industry) AS industry,
    coalesce(e.employment_status, 0) AS employment,
    coalesce(d.sex, 1) AS gender,
    coalesce(e.income, 0) AS income,
    CASE
        WHEN coalesce(x_p2.is_at_work, 0) = 1 THEN x_p2.default_arrival_time
        ELSE def.journey_to_work_arrival_time
    END AS journey_to_work_arrival_time,
    coalesce(e.commute_mode, def.journey_to_work_mode) AS journey_to_work_mode,
    def.journey_to_work_travel_time AS journey_to_work_travel_time,
    CASE
        WHEN coalesce(x_p2.is_at_work, 0) = 1 THEN x_p2.default_vehicle_occupancy
        ELSE def.journey_to_work_vehicle_occupancy
    END AS journey_to_work_vehicle_occupancy,
    CASE
        WHEN coalesce(d.relate, 99) = 1 THEN 1
        WHEN coalesce(d.age, 0) < 15 THEN 5
        WHEN coalesce(d.relate, 99) = 0 THEN 1
        ELSE 5
    END AS marital_status,
    coalesce(d.race, def.race) AS race,
    coalesce(s.school_status, 1) AS school_enrollment,
    coalesce(s.school_grade_level, def.school_grade_level) AS school_grade_level,
    coalesce(e.hours_worked, def.work_hours) AS work_hours,
    def.telecommute_level AS telecommute_level,
    def.transit_pass AS transit_pass,
    def.disability AS disability,
    def.time_in_job AS time_in_job,
    def.is_long_term_chooser AS is_long_term_chooser,
    def.escooter_use_level AS escooter_use_level
FROM people p
CROSS JOIN _contract_defaults_person def
JOIN household_membership m ON p.person_id = m.person_id
LEFT JOIN person_demographics d ON p.person_id = d.person_id
LEFT JOIN person_schooling s ON p.person_id = s.person_id
LEFT JOIN person_employment e ON p.person_id = e.person_id
LEFT JOIN _contract_crosswalk_x_p2 x_p2 ON coalesce(e.employment_status, 0) = x_p2.employment_status
ORDER BY p.person_id ASC;

-- 3. Vehicle Projection Query
SELECT
    ROW_NUMBER() OVER (ORDER BY v.household_id ASC, v.vehicle_id ASC) AS vehicle_id,
    v.household_id AS hhold,
    def.parking AS parking,
    def.L3_wtp AS L3_wtp,
    def.L4_wtp AS L4_wtp,
    coalesce(v.type_id, def.type) AS type,
    def.fleet AS fleet,
    def.subtype AS subtype
FROM vehicles v
CROSS JOIN _contract_defaults_vehicle def
ORDER BY vehicle_id ASC;
