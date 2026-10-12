-- One row per invented shipment: when it left, when it arrived, how much of it, and who accepted
-- it. The shipment notice, acceptance report, receipt, and discrepancy report are each a view of
-- this.

{{ config(materialized='view') }}

with purchases as (

    select * from {{ ref('int_dlms_synth__purchases') }}

),

numbered as (

    select *, unnest(range(1, shipment_count + 1)) as shipment_number
    from purchases

),

moved as (

    select
        *,
        award_key || '/shipment ' || shipment_number              as shipment_key,
        -- The first shipment carries the remainder when the quantity doesn't divide.
        quantity_ordered // shipment_count
            + case when shipment_number = 1 then quantity_ordered % shipment_count else 0 end
                                                                  as quantity_shipped
    from numbered

),

dated as (

    select
        *,
        -- Ships between halfway through the period of performance and a tenth past its end, so
        -- some are late.
        performance_start_date + round(
            (performance_end_date - performance_start_date)
            * (0.5 + {{ draw('shipment_key', 'ship') }} * 0.6)
        )::integer                                                as ship_date,
        2 + round({{ draw('shipment_key', 'transit') }} * 7)::integer as transit_days,
        -- One shipment in ten arrives short by about a tenth.
        quantity_shipped > 1 and {{ draw('shipment_key', 'short') }} < 0.1 as is_short,
        {{ activity_code('supplier_cage') }}                      as shipper_activity
    from moved

)

select
    * exclude (transit_days, shipper_activity),
    -- Transportation control number: 17 characters, built on a document number of the shipper's.
    {{ document_number('shipper_activity', 'ship_date', 'shipment_key') }} || 'XXX' as tcn,
    ship_date + transit_days                                      as receipt_date,
    quantity_shipped - case when is_short then greatest(1, quantity_shipped // 10) else 0 end
                                                                  as quantity_received,
    -- Acceptance is the government taking title: by DCMA before shipment, or at the depot after.
    case
        when accepted_at_origin then {{ activity_code("'Defense Contract Management Agency'") }}
        else storage_activity
    end                                                           as accepting_activity,
    case
        when accepted_at_origin then ship_date - 1
        else ship_date + transit_days + 1 + round({{ draw('shipment_key', 'accept') }} * 4)::integer
    end                                                           as acceptance_date
from dated
