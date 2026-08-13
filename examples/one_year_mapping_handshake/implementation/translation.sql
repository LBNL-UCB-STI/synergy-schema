-- synthetic draft translation with declared residue behavior
-- Household type uses the deterministic synthetic-household-type-r1 lookup.
select household_id as hhold,
       persons,
       case hh_type
         when 'family' then 'family'
         when 'single' then 'single'
         else 'other'
       end as household_type
from atlas_households
where region_flag = 'in_region';
-- tenure and atlas_vehicles.modelyear are intentionally not translated.
