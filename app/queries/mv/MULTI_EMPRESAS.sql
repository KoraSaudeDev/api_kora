SELECT
    cd_multi_empresa as cd_multi_empresa,
    NULLIF(REGEXP_REPLACE(ds_multi_empresa,'[''"!/:@;]', ''),'') as ds_multi_empresa,
    cd_cgc as cd_cgc,
    nr_cnpjcpf_repres_legal,
    sn_ativo
FROM
    DBAMV.MULTI_EMPRESAS
