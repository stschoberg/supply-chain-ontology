-- One row per invented customer order: later, the buying agency draws on the stock a purchase put
-- on the shelf. The requisition, release order, and issue are each a view of this.
--
-- The order is generated from a purchase but does not refer to it. Once received, units from
-- different contracts are one stock, so the DLMS transactions name an item and a depot, never an
-- award. `award_key` is kept here only to derive values; the published tables drop it.

{{ config(materialized='view') }}

with stocked as (

    select
        award_key,
        any_value(nsn)                                            as nsn,
        any_value(psc)                                            as psc,
        any_value(unit_of_issue)                                  as unit_of_issue,
        any_value(storage_activity)                               as storage_activity,
        any_value(customer_activity)                              as customer_activity,
        sum(quantity_received)                                    as quantity_stocked,
        max(receipt_date)                                         as last_receipt_date
    from {{ ref('int_dlms_synth__shipments') }}
    group by award_key

),

requested as (

    select
        *,
        last_receipt_date + 10 + round({{ draw('award_key', 'requisition') }} * 80)::integer
                                                                  as requisition_date,
        -- Between a fifth and four fifths of what was stocked, so no depot issues more than it has.
        greatest(1, floor(quantity_stocked * (0.2 + {{ draw('award_key', 'requisition quantity') }} * 0.6)))::integer
                                                                  as quantity
    from stocked

),

released as (

    select
        *,
        requisition_date + 1 + round({{ draw('award_key', 'release') }} * 3)::integer as release_date
    from requested

)

select
    {{ document_number('customer_activity', 'requisition_date', 'award_key') }}
                                                                  as document_number,
    nsn,
    psc,
    unit_of_issue,
    customer_activity,
    storage_activity,
    quantity,
    lpad((1 + round({{ draw('award_key', 'priority') }} * 14)::integer)::varchar, 2, '0') as priority,
    requisition_date,
    release_date,
    release_date + round({{ draw('award_key', 'issue') }} * 2)::integer as issue_date
from released
