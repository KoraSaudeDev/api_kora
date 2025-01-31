from flask import Blueprint, request, jsonify
import mysql.connector
import math
from app.utils.decorators import token_required, permission_required

depara_bp = Blueprint('depara', __name__, url_prefix='/depara')

@depara_bp.route('/', methods=['POST'])
@token_required
@permission_required(route_prefix='/depara')
def query_de_para(user_data):
    data = request.json
    filtros = []
    valores = []

    colunas_permitidas = ["SISTEMAORIGEM", "SISTEMADESTINO", "IDSISTEMA", "DOMINIO", "VALORORIGEM", "VALORDESTINO"]
    
    valores_permitidos_sistema = {"1410", "1411", "1412", "1413", "1414", "1415", "1416", "1420", "9998", "9999"}
    dominios_permitidos = {
        "ATIVIDADE", "CAIXA", "CENARIOSTRANSACOES", "CENTRO", "CENTROCUSTO", "CENTROLUCRO",
        "CLIENTE", "CLIENTEPARTICULAR", "CODIGOREDUZIDO", "CONDICAOPAGAMENTO", "DEPOSITO", "EMPRESASENIOR",
        "FORNECEDOR", "FRETE", "GRUPOCOMPRADORES", "GRUPOMERCADORIA", "IMPOSTOS", "INVENTARIO", "MATERIAL",
        "MULTIEMPRESA", "NOTACREDITO", "OPERADORA", "ORDEMINTERNA", "PEDIDORC", "REQUISICAOCOMPRA",
        "RESPONSAVEL", "SERVICO", "SERVICOMEDICO", "SETORATIVIDADE", "STATUSRC", "TIPOCONTACONTABIL",
        "TIPODOCENTRADA", "TIPODOCUMENTO", "TIPOMOVIMENTO", "TIPOSOLICITACAO", "TIPOTRANSACAO", "UNIDADE",
        "UNIDADEDEMEDIDA"
    }

    for key in data.keys():
        if key not in colunas_permitidas and key not in ["page", "per_page"]:
            return jsonify({"error": f"O parâmetro '{key}' é inválido."}), 400

    for coluna in colunas_permitidas:
        if coluna in data and data[coluna] is not None:
            valor = str(data[coluna]).strip()
            
            if coluna in ["SISTEMAORIGEM", "SISTEMADESTINO"] and valor not in valores_permitidos_sistema:
                return jsonify({"error": f"O campo '{coluna}' deve conter um dos valores permitidos: {', '.join(valores_permitidos_sistema)}"}), 400
            
            if coluna == "DOMINIO" and valor not in dominios_permitidos:
                return jsonify({"error": f"O campo 'DOMINIO' deve conter um dos valores permitidos: {', '.join(dominios_permitidos)}"}), 400
            
            filtros.append(f"{coluna} = %s")
            valores.append(valor)
    
    page = data.get("page")
    per_page = data.get("per_page")
    
    try:
        page = int(page)
        per_page = int(per_page)
        if page < 1 or per_page < 1:
            raise ValueError
    except (ValueError, TypeError):
        return jsonify({"error": "Os parâmetros 'page' e 'per_page' são obrigatórios e devem ser números inteiros positivos."}), 400
    
    offset = (page - 1) * per_page
    
    base_query = """
    SELECT HIS, SISTEMAORIGEM, SISTEMADESTINO, IDSISTEMA, DOMINIO, VALORORIGEM, VALORDESTINO 
    FROM CONFIGURACOES.DE_PARA_DADOSMESTRES 
    WHERE BL_ATIVO = 1
    """
    
    if filtros:
        base_query += " AND " + " AND ".join(filtros)
    
    count_query = "SELECT COUNT(*) AS total FROM (" + base_query + ") AS subquery"
    paginated_query = base_query + " LIMIT %s OFFSET %s"
    
    valores_paginacao = valores.copy()
    valores_paginacao.extend([per_page, offset])
    
    try:
        connection = mysql.connector.connect(
            host="10.27.254.161",
            port="3307",
            user="root",
            password="Kora@2024",
            database="CONFIGURACOES"
        )
        cursor = connection.cursor(dictionary=True)
        
        cursor.execute(count_query, tuple(valores))
        total_items = cursor.fetchone()["total"]
        
        cursor.execute(paginated_query, tuple(valores_paginacao))
        results = cursor.fetchall()
        
        cursor.close()
        connection.close()
        
        total_pages = math.ceil(total_items / per_page)
        
        return jsonify({
            "page": page,
            "pages": total_pages,
            "total_items": total_items,
            "items_per_page": per_page,
            "data": results
        }), 200
    except mysql.connector.Error as e:
        return jsonify({"error": str(e)}), 500