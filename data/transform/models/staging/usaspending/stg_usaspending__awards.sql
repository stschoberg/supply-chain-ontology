-- One row per DoD contract award, typed and renamed, from the raw USAspending award summaries.

with source as (

    select * from {{ source('usaspending', 'Contracts_PrimeAwardSummaries') }}

),

deduplicated as (

    -- Fiscal-year files overlap: an award with actions in several years appears in each.
    -- Keep the most recently modified copy.
    select *
    from source
    qualify row_number() over (
        partition by contract_award_unique_key
        order by last_modified_date desc, filename desc
    ) = 1

),

renamed as (

    select
        contract_award_unique_key                                 as award_key,
        award_id_piid                                             as piid,
        nullif(parent_award_id_piid, '')                          as parent_piid,

        nullif(recipient_uei, '')                                 as recipient_uei,
        recipient_name,
        nullif(recipient_parent_uei, '')                          as recipient_parent_uei,
        nullif(recipient_parent_name, '')                         as recipient_parent_name,
        nullif(cage_code, '')                                     as cage_code,
        domestic_or_foreign_entity,
        nullif(country_of_product_or_service_origin, '')          as origin_country,

        product_or_service_code                                   as psc,
        prime_award_base_transaction_description                  as description,
        -- DLA writes most descriptions as "<10 digits>!<item name>". The number is unique per award
        -- (likely the purchase request number), so it does NOT identify the item.
        nullif(regexp_extract(description, '^([0-9]{10})!', 1), '') as dla_reference_number,
        trim(regexp_replace(description, '^[0-9]{10}!', ''))       as item_name,
        -- NSN = 4-digit supply class + 9-digit NIIN, written with or without dashes. Present in <1% of
        -- descriptions. Not preceded by a letter, which rules out document numbers like N4215830672984.
        nullif(replace(regexp_extract(
            description, '(?:^|[^0-9A-Za-z])([0-9]{4}-?[0-9]{2}-?[0-9]{3}-?[0-9]{4})(?:[^0-9]|$)', 1
        ), '-', ''), '')                                          as nsn,

        awarding_sub_agency_name                                  as awarding_sub_agency,
        try_cast(total_obligated_amount as decimal(18, 2))        as total_obligated_amount,
        try_cast(award_base_action_date as date)                  as base_action_date,

        nullif(extent_competed, '')                               as extent_competed,
        try_cast(number_of_offers_received as integer)            as offers_received,
        nullif(other_than_full_and_open_competition, '')          as other_than_full_and_open_reason,

        try_cast(last_modified_date as timestamp)                 as last_modified_at,
        -- Last two path segments (<fiscal-year folder>/<csv>), so no local paths leak into releases.
        regexp_extract(filename, '([^/]+/[^/]+)$', 1)            as source_file

    from deduplicated

)

select * from renamed
