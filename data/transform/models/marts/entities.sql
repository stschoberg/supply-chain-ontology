-- One row per entity: every UEI an award reports, as its recipient or as the recipient's corporate
-- parent. Both award columns are foreign keys to this table.

with awards as (

    select * from {{ ref('stg_usaspending__awards') }}

),

reported as (

    select recipient_uei as uei, recipient_name as name, last_modified_at, award_key from awards
    union all
    select recipient_parent_uei, recipient_parent_name, last_modified_at, award_key from awards

)

select
    uei,
    -- Spelling can vary across awards. Keep the most recently reported name.
    arg_max(name, (last_modified_at, award_key, name)) filter (where name is not null) as name
from reported
where uei is not null
group by uei
