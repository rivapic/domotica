#!/usr/bin/env python3
# DPS Parsing and Decoding Utilities
# -*- coding: utf-8 -*-

import json
import base64
from datetime import datetime


def load_device_info(device_name):
    """Load device info from devices.json by device name"""
    try:
        with open('devices.json', 'r') as f:
            devices = json.load(f)
    except FileNotFoundError:
        print("Error: devices.json not found.")
        return None
    
    device_info = next((d for d in devices if d['name'] == device_name), None)
    if not device_info:
        print(f"Error: Device '{device_name}' not found in devices.json.")
        return None
    
    return device_info


def _parse_values_obj(obj):
    """Parse values object which may be stored as JSON string or dict"""
    if isinstance(obj, dict):
        return obj
    if isinstance(obj, str):
        try:
            return json.loads(obj)
        except Exception:
            return {}
    return {}


def get_scale_for(dps_key, mapping):
    """Get scale factor for a DPS key from mapping"""
    entry = mapping.get(str(dps_key), {})
    # check 'values'
    vals = _parse_values_obj(entry.get('values', {}))
    if isinstance(vals, dict) and 'scale' in vals:
        try:
            return int(vals['scale'])
        except Exception:
            pass
    # check 'raw_values' (often a JSON string)
    raw = _parse_values_obj(entry.get('raw_values', {}))
    if isinstance(raw, dict) and 'scale' in raw:
        try:
            return int(raw['scale'])
        except Exception:
            pass
    return None


def scale_value(dps_key, raw_value, mapping):
    """Scale a DPS value based on the mapping scale factor"""
    try:
        num = float(raw_value)
    except Exception:
        return raw_value
    scale = get_scale_for(dps_key, mapping)
    if scale is not None:
        return num / (10 ** scale)
    return num


def get_code_for(dps_key, mapping):
    """Get code/name for a DPS key from mapping"""
    return mapping.get(str(dps_key), {}).get('code', 'N/A')


def get_unit_for(dps_key, mapping):
    """Get unit for a DPS key from mapping"""
    entry = mapping.get(str(dps_key), {})
    # check 'values'
    vals = _parse_values_obj(entry.get('values', {}))
    if isinstance(vals, dict) and 'unit' in vals:
        return vals['unit']
    # check 'raw_values'
    raw = _parse_values_obj(entry.get('raw_values', {}))
    if isinstance(raw, dict) and 'unit' in raw:
        return raw['unit']
    return None


def get_type_for(dps_key, mapping):
    """Get type for a DPS key from mapping"""
    return mapping.get(str(dps_key), {}).get('type', 'N/A')


def dps_sort_key(item):
    """Sort key for DPS items"""
    k, _ = item
    try:
        return int(k)
    except Exception:
        return k


def decode_phase(value):
    """Decode phase data from base64 encoded value"""
    decoded_value = base64.b64decode(value)
    binary_value = ''.join(format(byte, '08b') for byte in decoded_value)
    Tension = int(binary_value[:16], 2)
    Intensidad = int(binary_value[16:40], 2)
    Potencia = int(binary_value[-24:], 2)
    print(' Tension:', Tension / 10, 'V')
    print(' Intensidad:', Intensidad / 1000, 'A')
    print(' Potencia:', Potencia / 1000, 'KW')


def print_dps(dps_data, device_info, device_name):
    """Print formatted DPS data from status payload"""
    if not dps_data or 'dps' not in dps_data:
        return
    
    dps = dps_data['dps']
    mapping = device_info.get('mapping', {}) or {}
    
    now = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    print(f"Dispositivo: {device_name} a las {now}")
    
    # Imprimir timestamp si está disponible
    if 't' in dps_data:
        try:
            timestamp = int(dps_data['t'])
            dt = datetime.fromtimestamp(timestamp)
            dt_str = dt.strftime('%Y-%m-%d %H:%M:%S')
            print(f"Timestamp: {dt_str}")
        except Exception as e:
            print(f"Timestamp: {dps_data['t']} (error al convertir: {e})")
    
    for k, v in sorted(dps.items(), key=dps_sort_key):
        code = get_code_for(k, mapping)
        scaled = scale_value(k, v, mapping)
        data_type = get_type_for(k, mapping)
        unit = get_unit_for(k, mapping)
        
        # Format output based on type
        if data_type == "Boolean":
            output = f"{code}={v}"
        else:
            output = f"{code}={scaled}"
            if unit:
                output += f" {unit}"
        
        print(output)
        if code == "phase_a":
            decode_phase(v)
