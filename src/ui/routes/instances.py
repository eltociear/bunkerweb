# -*- coding: utf-8 -*-
from flask import Blueprint
from flask import request
from flask_jwt_extended import jwt_required

from utils import get_core_format_res
import json
from os import environ
from ui import UiConfig

from werkzeug.exceptions import HTTPException
from werkzeug.sansio.response import Response

UI_CONFIG = UiConfig("ui", **environ)

CORE_API = UI_CONFIG.CORE_ADDR

from os.path import join, sep
from sys import path as sys_path

deps_path = join(sep, "usr", "share", "bunkerweb", "utils")
if deps_path not in sys_path:
    sys_path.append(deps_path)

from api_models import BanAdd, BanDelete, Method  # type: ignore


PREFIX = "/api/instances"

instances = Blueprint("instances", __name__)


@instances.route(f"{PREFIX}", methods=["GET"])
@jwt_required()
def get_instances():
    """Get BunkerWeb instances"""
    return get_core_format_res(f"{CORE_API}/instances", "GET", "", "Retrieve instances")


@instances.route(f"{PREFIX}", methods=["PUT"])
@jwt_required()
def upsert_instance():
    """Upsert one or more BunkerWeb instances"""
    args = request.args.to_dict()
    method = args.get("method") or "ui"
    # is_valid_model(method, Model) True | False
    reload_instance = args.get("reload") or True
    # is_valid_model(method, Model) True | False
    instances = request.get_json()
    # is_valid_model(instances, Model) True | False
    data = json.dumps(instances, skipkeys=True, allow_nan=True, indent=6)
    return get_core_format_res(f"{CORE_API}/instances?method={method}&reload={reload_instance}", "PUT", data, "Upsert instances")


@instances.route(f"{PREFIX}/<string:instance_hostname>", methods=["DELETE"])
@jwt_required()
def delete_instance(instance_hostname):
    """Delete BunkerWeb instance"""
    # is_valid_model(instance_hostname, Model) True | False
    args = request.args.to_dict()
    method = args.get("method") or "ui"
    # is_valid_model(method, Model) True | False
    return get_core_format_res(f"{CORE_API}/instances/{instance_hostname}?method={method}", "DELETE", "", f"Delete instance {instance_hostname}")


@instances.route(f"{PREFIX}/<string:instance_hostname>/<string:action>", methods=["POST"])
@jwt_required()
def action_instance(instance_hostname, action):
    """Send action to a BunkerWeb instance"""
    # is_valid_model(instance_hostname, Model) True | False
    # is_valid_model(action, Model) True | False
    args = request.args.to_dict()
    method = args.get("method") or "ui"
    # is_valid_model(method, Model) True | False
    return get_core_format_res(f"{CORE_API}/instances/{instance_hostname}/{action}?method={method}", "POST", "", f"Send instance {instance_hostname} action : {action}")


@instances.route(f"{PREFIX}/ban", methods=["POST"])
@jwt_required()
def add_bans():
    """Add bans ip for all instances"""
    args = request.args.to_dict()
    method = args.get("method") or "ui"

    try:
        Method(method=method)
    except:
        raise HTTPException(response=Response(status=400), description=f"Request args bad format")

    bans = request.get_json()
    try:
        BanAdd(list=bans)
    except:
        raise HTTPException(response=Response(status=400), description="Request body bad format")

    # is_valid_model(instances, Model) True | False
    data = json.dumps(bans, skipkeys=True, allow_nan=True, indent=6)
    return get_core_format_res(f"{CORE_API}/instances/ban?method={method}", "POST", data, "Add bans ip")


@instances.route(f"{PREFIX}/ban", methods=["DELETE"])
@jwt_required()
def delete_bans():
    """Delete bans ip for all instances"""
    args = request.args.to_dict()
    method = args.get("method") or "ui"

    try:
        Method(method=method)
    except:
        raise HTTPException(response=Response(status=400), description=f"Request args bad format")

    bans = request.get_json()
    try:
        BanDelete(list=bans)
    except:
        raise HTTPException(response=Response(status=400), description=f"Request body bad format")

    data = json.dumps(bans, skipkeys=True, allow_nan=True, indent=6)
    return get_core_format_res(f"{CORE_API}/instances/ban?method={method}", "DELETE", data, "Delete bans ip")
