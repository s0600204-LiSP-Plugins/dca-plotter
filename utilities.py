
# get_mic_assign_name
from lisp.plugins import get_plugin

def build_default_mic_name(num):
    # TODO: translate string
    return "Microphone {0}".format(num)

def get_mic_assign_name(numid):
    inputs = get_plugin('DcaPlotter').SessionConfig['inputs']

    return '{id} : {name}'.format_map({
        'id': numid,
        'name': inputs[numid - 1]['name'] if inputs else build_default_mic_name(numid)
    })
