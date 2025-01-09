SELECT
	cd_tuss
	, ie_versao_atual
	, ie_versao_origem
	, nr_sequencia
	, REGEXP_REPLACE(cd_apresentacao,'[''"!/:@;]', '') as cd_apresentacao
	, REGEXP_REPLACE(cd_ean,'[''"!/:@;]', '') as cd_ean
	, REGEXP_REPLACE(cd_hierarquia,'[''"!/:@;]', '') as cd_hierarquia
	, REGEXP_REPLACE(cd_laboratorio,'[''"!/:@;]', '') as cd_laboratorio
	, REGEXP_REPLACE(cd_medicamento,'[''"!/:@;]', '') as cd_medicamento
	, REGEXP_REPLACE(cd_tiss,'[''"!/:@;]', '') as cd_tiss
	, REGEXP_REPLACE(ie_generico,'[''"!/:@;]', '') as ie_generico
	, REGEXP_REPLACE(ie_oncologico,'[''"!/:@;]', '') as ie_oncologico
	, REGEXP_REPLACE(ie_pis_cofins,'[''"!/:@;]', '') as ie_pis_cofins
	, REGEXP_REPLACE(ie_preco_port,'[''"!/:@;]', '') as ie_preco_port
	, REGEXP_REPLACE(ie_restrito,'[''"!/:@;]', '') as ie_restrito
	, REGEXP_REPLACE(ie_solucao,'[''"!/:@;]', '') as ie_solucao
	, REGEXP_REPLACE(ie_tipo_preco,'[''"!/:@;]', '') as ie_tipo_preco
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, REGEXP_REPLACE(nm_usuario_liberacao,'[''"!/:@;]', '') as nm_usuario_liberacao
	, TO_CHAR(pr_ipi) as pr_ipi
	, TO_CHAR(vl_preco_final) as vl_preco_final
	, TO_CHAR(vl_preco_medicamento) as vl_preco_medicamento
	, cd_estabelecimento
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia
	, TO_CHAR(dt_liberacao, 'YYYY-MM-DD hh24:mi:ss') as dt_liberacao
FROM
	TASY.BRASINDICE_PRECO