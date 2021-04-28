from arcgis.features import FeatureSet, FeatureCollection, FeatureLayer, Table
from collections import namedtuple
import json

class Restore(object):
    @staticmethod
    def restore_gis_from_backup(path, gis):
        with open(path) as f:
            data = json.load(f)
            if all(k in data.keys() for k in ("feature_set", "layer_name", "layer_url", "layer_type")):
                Restore = namedtuple('Restore', 'layer feature_set')
                fs = FeatureSet.from_dict(data['feature_set'])
                if data['layer_type'] == 'Feature Layer':
                    layer = FeatureLayer(url=data['layer_url'], gis=gis)
                elif data['layer_type'] == 'Table':
                    layer = Table(url=data['layer_url'], gis=gis)
                else:
                    raise Exception('JSON from restore, unsupported layer type.')
                return Restore(layer, fs)
            else:
                raise Exception('JSON from restore, invalid formatting.')