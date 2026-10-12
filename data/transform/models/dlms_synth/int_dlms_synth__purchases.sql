-- One row per award that bought something, with the invented terms every later record repeats:
-- how many units, in how many shipments, to which depot, and where the government accepts them.

{{ config(materialized='view') }}

with awards as (

    select * from {{ ref('stg_usaspending__awards') }}
    -- A zero or negative total is a cancelled or de-obligated award: nothing was bought.
    where total_obligated_amount > 0

),

drawn as (

    select
        *,
        -- An invented unit price turns the real obligated amount into an invented quantity.
        greatest(1, round(total_obligated_amount / (25 + {{ draw('award_key', 'unit price') }} * 1975)))::integer
                                                                  as quantity_ordered,
        {{ draw('award_key', 'split') }} < 0.4                    as is_split,
        -- About a third of awards are accepted at origin, by DCMA, before they ship.
        {{ draw('award_key', 'inspection point') }} < 0.35        as accepted_at_origin,
        -- DLA's two primary distribution centers; awards go to the nearer coast.
        case
            when place_of_performance_state in
                ('AK', 'AZ', 'CA', 'CO', 'HI', 'ID', 'MT', 'NM', 'NV', 'OR', 'UT', 'WA', 'WY')
                then 'DLA Distribution San Joaquin'
            else 'DLA Distribution Susquehanna'
        end                                                       as depot_name
    from awards

)

select
    award_key,
    piid,
    '0001'                                                        as clin,
    nsn,
    psc,
    'EA'                                                          as unit_of_issue,
    cage_code                                                     as supplier_cage,
    coalesce(place_of_performance_city, recipient_city)           as ship_from_city,
    coalesce(place_of_performance_country, recipient_country)     as ship_from_country,
    awarding_sub_agency                                           as customer_name,
    {{ activity_code('awarding_sub_agency') }}                    as customer_activity,
    depot_name,
    {{ activity_code('depot_name') }}                             as storage_activity,
    performance_start_date,
    performance_end_date,
    quantity_ordered,
    case when quantity_ordered > 1 and is_split then 2 else 1 end as shipment_count,
    accepted_at_origin
from drawn
