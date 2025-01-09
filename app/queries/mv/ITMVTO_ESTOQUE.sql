WITH PaginatedQuery AS (
    SELECT 
        ROW_NUMBER() OVER (ORDER BY ie.dh_mvto_estoque) AS row_num,
        ie.cd_mvto_estoque,
        ie.cd_itmvto_estoque,
        ie.cd_produto,
        ie.cd_uni_pro,
        to_char(ie.qt_movimentacao) AS qt_movimentacao,
        NULLIF(REGEXP_REPLACE(ie.cd_lote, '[''"!/:@;]', ''), '') AS cd_lote,
        TO_CHAR(ie.dt_validade, 'YYYY-MM-DD hh24:mi:ss') AS dt_validade,
        to_char(ie.qt_perda) AS qt_perda,
        TO_CHAR(ie.dh_mvto_estoque, 'YYYY-MM-DD hh24:mi:ss') AS dh_mvto_estoque,
        ie.cd_importa_reg_fat,
        ie.cd_itsolsai_pro,
        ie.cd_importa_reg_amb,
        to_char(ie.vl_unitario_emprestimo) AS vl_unitario_emprestimo,
        to_char(ie.vl_total_emprestimo) AS vl_total_emprestimo,
        ie.cd_itent_pro,
        NULLIF(REGEXP_REPLACE(ie.tp_uso_produto, '[''"!/:@;]', ''), '') AS tp_uso_produto,
        ie.cd_fornecedor,
        NULLIF(REGEXP_REPLACE(ie.cd_produto_kit, '[''"!/:@;]', ''), '') AS cd_produto_kit,
        NULLIF(REGEXP_REPLACE(ie.tp_estoque, '[''"!/:@;]', ''), '') AS tp_estoque,
        ie.cd_formula_kit,
        to_char(ie.qt_kit) AS qt_kit,
        NULLIF(REGEXP_REPLACE(ie.tp_orcamento, '[''"!/:@;]', ''), '') AS tp_orcamento,
        NULLIF(REGEXP_REPLACE(ie.sn_fatura, '[''"!/:@;]', ''), '') AS sn_fatura,
        to_char(ie.vl_icms) AS vl_icms,
        to_char(ie.vl_unitario) AS vl_unitario,
        TO_CHAR(ie.dt_gravacao, 'YYYY-MM-DD hh24:mi:ss') AS dt_gravacao,
        NULLIF(REGEXP_REPLACE(ie.sn_pendencia, '[''"!/:@;]', ''), '') AS sn_pendencia,
        NULLIF(REGEXP_REPLACE(ie.cd_itmvto_estoque_integra, '[''"!/:@;]', ''), '') AS cd_itmvto_estoque_integra,
        NULLIF(REGEXP_REPLACE(ie.sn_prod_recebido_solicitacao, '[''"!/:@;]', ''), '') AS sn_prod_recebido_solicitacao,
        to_char(ie.qt_recebido) AS qt_recebido,
        to_char(ie.qt_retornada_doado) AS qt_retornada_doado
    FROM itmvto_estoque ie
    WHERE 
        ie.dh_mvto_estoque >= ADD_MONTHS(TRUNC(SYSDATE, 'mm'), 
            (CASE WHEN EXTRACT(DAY FROM SYSDATE) < 20 THEN '-5' ELSE '-4' END))
        AND ie.dh_mvto_estoque < ADD_MONTHS(TRUNC(SYSDATE, 'mm'), 
            (CASE WHEN EXTRACT(DAY FROM SYSDATE) < 20 THEN '-1' ELSE '0' END))
)
SELECT *
FROM PaginatedQuery
WHERE row_num BETWEEN :start_row AND :end_row;
