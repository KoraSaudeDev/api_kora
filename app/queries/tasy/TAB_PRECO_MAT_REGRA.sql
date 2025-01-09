SELECT
	nr_sequencia
	, REGEXP_REPLACE(ie_ignora_atualizacao,'[''"!/:@;]', '') as ie_ignora_atualizacao
	, REGEXP_REPLACE(ie_situacao,'[''"!/:@;]', '') as ie_situacao
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, REGEXP_REPLACE(nm_usuario_nrec,'[''"!/:@;]', '') as nm_usuario_nrec
	, cd_classe_material
	, cd_material
	, cd_estabelecimento
	, cd_grupo_material
	, cd_subgrupo_material
	, cd_tab_preco_mat
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao_nrec
FROM
	TASY.TAB_PRECO_MAT_REGRA