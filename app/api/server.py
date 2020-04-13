from app.api import bp
from flask import jsonify, current_app
from app.modules.server.models import Server
from app.modules.rack.models import Rack
from app.models import User, Service, Location
from flask import url_for
from app import db, audit
from app.api.errors import bad_request
from flask import request
from app.api.auth import token_auth


@bp.route('/server/add', methods=['POST'])
@token_auth.login_required
def create_server():
    data = request.get_json() or {}
    for field in ['hostname', 'status', 'ipaddress', 'netmask', 'gateway',
                  'memory', 'cpu', 'psu', 'hd', 'serial', 'model', 'os_name',
                  'os_version', 'manufacturer', 'rack_id', 'location_id',
                  'service_id', 'support_start', 'support_end', 'comment',
                  'rack_position']:
        if field not in data:
            return bad_request('must include %s fields' % field)

    server = Server()
    server.from_dict(data)

    if 'service_id' in data:
        service = Service.query.get(data['service_id'])
        server.service = service

    if 'location_id' in data:
        location = Location.query.get(data['location_id'])
        server.location = location

    if 'rack_id' in data:
        rack = Rack.query.get(data['rack_id'])
        server.rack = rack

    db.session.add(server)
    db.session.commit()
    audit.auditlog_new_post('server', original_data=server.to_dict(), record_name=server.hostname)

    response = jsonify(server.to_dict())

    response.status_code = 201
    response.headers['Location'] = url_for('api.get_server', id=server.id)
    return response


@bp.route('/serverlist', methods=['GET'])
@token_auth.login_required
def get_serverlist():
    page = request.args.get('page', 1, type=int)
    per_page = min(request.args.get('per_page', 10, type=int), 100)
    data = Server.to_collection_dict(Server.query, page, per_page, 'api.get_server')
    return jsonify(data)


@bp.route('/server/<int:id>', methods=['GET'])
@token_auth.login_required
def get_server(id):
    return jsonify(Server.query.get_or_404(id).to_dict())


@bp.route('/server/<int:id>', methods=['PUT'])
@token_auth.login_required
def update_server(id):
    server = Server.query.get_or_404(id)
    original_data = server.to_dict()

    data = request.get_json() or {}
    server.from_dict(data, new_server=False)
    db.session.commit()
    audit.auditlog_update_post('server', original_data=original_data, updated_data=server.to_dict(), record_name=server.hostname)

    return jsonify(server.to_dict())
