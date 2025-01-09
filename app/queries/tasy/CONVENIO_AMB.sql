SELECT
	REGEXP_REPLACE(cd_categoria,'[''"!/:@;]', '') as cd_categoria
	, REGEXP_REPLACE(ie_situacao,'[''"!/:@;]', '') as ie_situacao
	, REGEXP_REPLACE(nm_usuario,'[''"!/:@;]', '') as nm_usuario
	, TO_CHAR(dt_atualizacao, 'YYYY-MM-DD hh24:mi:ss') as dt_atualizacao
	, TO_CHAR(dt_final_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_final_vigencia
	, TO_CHAR(dt_inicio_vigencia, 'YYYY-MM-DD hh24:mi:ss') as dt_inicio_vigencia
	, TO_CHAR(cd_convenio) as cd_convenio
	, TO_CHAR(cd_edicao_amb) as cd_edicao_amb
	, TO_CHAR(cd_estabelecimento) as cd_estabelecimento
	, TO_CHAR(ie_prioridade) as ie_prioridade
	, TO_CHAR(nr_seq_cbhpm_edicao) as nr_seq_cbhpm_edicao
	, TO_CHAR(nr_seq_tiss_tabela) as nr_seq_tiss_tabela
	, TO_CHAR(tx_ajuste_geral) as tx_ajuste_geral
	, TO_CHAR(vl_ch_custo_oper) as vl_ch_custo_oper
	, TO_CHAR(vl_ch_honorarios) as vl_ch_honorarios
	, TO_CHAR(vl_filme) as vl_filme
FROM
	TASY.CONVENIO_AMB