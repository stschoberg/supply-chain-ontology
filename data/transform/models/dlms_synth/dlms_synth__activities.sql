-- The DoD activities the dlms_synth records name. Their names are real; their codes are invented.

select distinct activity_code, name, true as synthetic
from (
    select storage_activity as activity_code, depot_name as name from {{ ref('int_dlms_synth__purchases') }}
    union all
    select customer_activity, customer_name from {{ ref('int_dlms_synth__purchases') }}
    union all
    select {{ activity_code("'Defense Contract Management Agency'") }}, 'Defense Contract Management Agency'
)
