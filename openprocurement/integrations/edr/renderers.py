# -*- coding: utf-8 -*-
import yaml


class YAMLRenderer(object):
    def __init__(self, info):
        pass

    def __call__(self, value, system):
        request = system.get('request')
        if request is not None:
            response = request.response
            response.content_type = 'application/yaml'
        return yaml.safe_dump(value, allow_unicode=True, default_flow_style=False)
