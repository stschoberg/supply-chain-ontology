-- Published: one row describing the build that produced this release.

select
    '{{ var("release_tag", "dev") }}'      as release_tag,
    '{{ var("git_sha", "unknown") }}'      as git_sha,
    {{ var("git_dirty", true) }}           as git_dirty,
    '{{ dbt_version }}'                    as dbt_version,
    current_timestamp                      as built_at
