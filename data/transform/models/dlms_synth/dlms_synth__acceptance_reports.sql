-- DLMS 861P, Procurement Acceptance Report: the government accepts a shipment's goods, at origin
-- before they ship or at the depot after they arrive. Procure-to-Pay: Perform Receipt, Acceptance,
-- and Return.

select
    tcn, award_key, piid, clin, accepting_activity,
    case when accepted_at_origin then quantity_shipped else quantity_received end as quantity_accepted,
    acceptance_date,
    true as synthetic
from {{ ref('int_dlms_synth__shipments') }}
