SELECT
	REGEXP_REPLACE(cd_categoria,'[''"!/:@;]', '') as cd_categoria
	, REGEXP_REPLACE(ie_tipo_preco,'[''"!/:@;]', '') as ie_tipo_preco
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, REGEXP_REPLACE(nm_usuario_nrec,'[''"!/:@;]', '') as nm_usuario_nrec
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_atualizacao_nrec, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao_nrec
	, TO_CHAR(dt_final_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_final_vigencia
	, TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia
	, TO_CHAR(cd_classe_material) as cd_classe_material
	, TO_CHAR(cd_convenio) as cd_convenio
	, TO_CHAR(cd_estabelecimento) as cd_estabelecimento
	, TO_CHAR(cd_grupo_material) as cd_grupo_material
	, TO_CHAR(cd_material) as cd_material
	, TO_CHAR(cd_subgrupo_material) as cd_subgrupo_material
	, TO_CHAR(ie_tipo_atendimento) as ie_tipo_atendimento
	, TO_CHAR(nr_seq_estrutura) as nr_seq_estrutura
	, TO_CHAR(nr_seq_familia) as nr_seq_familia
	, TO_CHAR(nr_sequencia) as nr_sequencia
FROM
	TASY.REGRA_BRASINDICE_PRECO