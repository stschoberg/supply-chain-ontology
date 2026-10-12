-- DLMS 856P, Procurement Advance Shipment Notice (ASN): the supplier says a shipment has left.
-- Procure-to-Pay: Perform Receipt, Acceptance, and Return.

select
    tcn, award_key, piid, clin, shipment_number, supplier_cage, ship_from_city, ship_from_country,
    storage_activity as ship_to_activity,
    quantity_shipped, ship_date,
    case when accepted_at_origin then 'ORIGIN' else 'DESTINATION' end as acceptance_point,
    true as synthetic
from {{ ref('int_dlms_synth__shipments') }}
