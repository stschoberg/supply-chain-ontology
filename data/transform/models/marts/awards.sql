-- Published: one row per DoD contract award for bearings (PSC group 31).

select
    award_key,
    piid,
    parent_piid,

    recipient_uei,
    recipient_name,
    recipient_parent_uei,
    recipient_parent_name,
    cage_code,
    domestic_or_foreign_entity,
    origin_country,

    psc,
    item_name,
    nsn,
    description,
    dla_reference_number,

    awarding_sub_agency,
    total_obligated_amount,
    base_action_date,

    extent_competed,
    offers_received,
    other_than_full_and_open_reason,

    last_modified_at,
    source_file

from {{ ref('stg_usaspending__awards') }}
