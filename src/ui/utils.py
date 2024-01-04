# -*- coding: utf-8 -*-
from functools import wraps
import requests, json  # noqa: E401

from hook import hooks

from flask import request

from logging import Logger
from os.path import join, sep
from sys import path as sys_path
import os
from ui import UiConfig
from datetime import datetime

deps_path = join(sep, "usr", "share", "bunkerweb", "utils")
if deps_path not in sys_path:
    sys_path.append(deps_path)

from logger import setup_logger  # type: ignore

LOGGER: Logger = setup_logger("UI")

UI_CONFIG = UiConfig("ui", **os.environ)
CORE_API = UI_CONFIG.CORE_ADDR


def get_req_data(req, queries=[]):
    # get body json or fallback
    try:
        body = req.get_json()
    except:
        body = None

    data = {}
    if body and len(body) > 0:
        data = json.dumps(body, skipkeys=True, allow_nan=True, indent=6)

    # get queries
    args = req.args.to_dict()

    # Set data
    result = {}

    for query in queries:
        result[query] = args.get(query) or ""

    result["args"] = args
    result["data"] = data

    return result


# Communicate with core and send response to client
@hooks(hooks=["BeforeCoreReq", "AfterCoreReq"])
def get_core_format_res(path, method, data=None, message=None, retry=1):
    from exceptions.api import CoreReqException

    # Retry limit
    if retry == 5:
        raise CoreReqException

    # Try request core
    req = None
    try:
        # Request core api and store response
        if method.upper() == "GET":
            req = requests.get(path)

        if method.upper() == "POST":
            req = requests.post(path, data=data)

        if method.upper() == "DELETE":
            req = requests.delete(path, data=data)

        if method.upper() == "PATCH":
            req = requests.patch(path, data=data)

        if method.upper() == "PUT":
            req = requests.put(path, data=data)

        # Case 503, retry request
        if req.status_code == 503:
            LOGGER.warn(log_format("warn", "503", path, f"Communicate with {path} {method} retry={retry}. Maybe CORE is setting something up on background.", data))
            return get_core_format_res(path, method, data, message, retry + 1)
    except:
        raise CoreReqException(f"CORE request failed on path {path}, method {method}, data : {data or 'none'}")

    return proceed_core_data(req, path, method, data, message)

@hooks(hooks=["BeforeProceedCore", "AfterProceedCore"])
def proceed_core_data(res, path, method, data=None, message=None,):
    from exceptions.api import ProceedCoreException
    # Case response from core, format response for client
    LOGGER.warn(f"PROCEED CORE RESPONDR FOR PATH : {path} WITH DATA : {res.text}")

    try:
        # Proceed data
        data = res.text

        obj = json.loads(res.text)
        if isinstance(obj, dict):
            data = obj.get("message", obj)
            if isinstance(data, dict):
                data = data.get("data", data)

            data = json.dumps(data, skipkeys=True, allow_nan=True, indent=6)

        # Additional info
        res_type = "success" if str(res.status_code).startswith("2") else "error"
        res_status = str(res.status_code)

        if res_type == "error":
            LOGGER.error(log_format(res_type, res_status, path, message, data))

        return res_format(res_type, res_status, "", message, data)
    # Case impossible to format
    except:
        raise ProceedCoreException(f"Proceed CORE response failed on path {path}, method {method}")

# Standard response format
def res_format(type="error", status_code="500", path="", detail="Internal Server Error", data={"message": "error"}):
    return json.dumps({"type": type, "status": status_code, "message": f"{path} {detail}", "data": data}, skipkeys=True, allow_nan=True, indent=6)


# Standard log format
def log_format(type="", status_code="500", path="", detail="Internal Server Error", data=""):
    return f"[UI] {status_code} {path} || {detail} || data : {data or ''}"


# Send action to CORE
def create_action_format(type="info", status_code="500", title="", detail="", tags=["ui", "exception"], exception_logger=True):
    data = json.dumps(
        {"date": datetime.now().isoformat(), "api_method": "UNKNOWN", "method": "ui", "title": title, "description": f"{detail} { f'(status {status_code})' or ''}", "status": type, "tags": tags},
        skipkeys=True,
        allow_nan=True,
        indent=6,
    )
    try:
        requests.post(f"{CORE_API}/actions", data=data)
    except:
        if exception_logger:
            LOGGER.error(log_format("error", "500", "", f"Try to send action to CORE but failed. CORE down or data invalid ({data})."))


# Handle error and exception with default format
# We need to log, send action and error response
def default_error_handler(code="500", path="", desc="Internal server error.", tags=["ui", "exception"]):
    # Try to send details
    try:
        LOGGER.error(log_format("error", code, path, desc))
        create_action_format("error", code, f"UI exception {'path : ' + path or ''}", desc, tags)
        return res_format("error", code, path, desc)
    # Case impossible to send custom data and detail, send fallback
    except:
        LOGGER.error(log_format("error", "500", "", "Internal server error but impossible to get detail."))
        create_action_format("error", "500", "UI exception", "Internal server error but impossible to get detail.", tags)
        return res_format("error", "500", "", "Internal server error.")


def format_exception():
    def decorator(f):
        @wraps(f)
        def wrapped(*args, **kwargs):
            # Run main error function to get possible override data (code, desc)
            error = str(f(*args, **kwargs))

            # Split message and prepare data
            code = error.split(" ")[0]
            title = error.split(":")[0].replace(code, "")
            desc = error.split(":")[-1]
            path = request.path

            # Send format and additionnal logic
            try:
                LOGGER.error(log_format("error", code, path, desc))
                create_action_format("error", code, f"UI exception {'path : ' + path or ''}", f"{title} : {desc}", ["ui", "exception"])
                return res_format("error", code, path, f"{title} : {desc}")
            # Case impossible to send custom data and detail, send fallback
            except:
                LOGGER.error(log_format("error", "500", "", "Internal server error but impossible to get detail."))
                create_action_format("error", "500", "UI exception", "Internal server error but impossible to get detail.", ["ui", "exception"])
                return res_format("error", "500", "", "Internal server error.")
            
        return wrapped

    return decorator

