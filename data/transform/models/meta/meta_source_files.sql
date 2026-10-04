-- Published: which raw files this release was built from, with their checksums.

select
    'usaspending'                                        as source,
    regexp_extract(filename, '([^/]+)/[^/]+$', 1)        as snapshot,
    file,
    sha256,
    retrieved_at,
    job_status.total_rows                                as rows,
    license,
    request::varchar                                     as request
from read_json(
    '{{ var("usaspending_snapshot") }}/*.manifest.json',
    filename = true,
    columns = {
        file: 'varchar',
        sha256: 'varchar',
        retrieved_at: 'timestamptz',
        license: 'varchar',
        job_status: 'struct(total_rows bigint)',
        request: 'json'
    }
)
