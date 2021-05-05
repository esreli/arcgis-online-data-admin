import errno
import json
import os
import os.path
from pathlib import Path
from arcgis.features import FeatureSet
from datetime import datetime
import uuid


def mkdir_p(path):
    try:
        os.makedirs(path)
    except OSError as exc:  # Python >2.5
        if exc.errno == errno.EEXIST and os.path.isdir(path):
            pass
        else:
            raise


def safe_open_w(path):
    mkdir_p(os.path.dirname(path))
    return open(path, 'w')


class Backup(object):

    def __init__(self, base: str = None):
        if base:
            self._basepath = Path(base)
        else:
            self._basepath = None
        self.sessions = {}

    def prepare_backup(self, feature_set: FeatureSet, layer):
        if not self._basepath:
            return None

        backup_id = uuid.uuid4()
        backup = dict(feature_set=feature_set.to_dict(),
                      layer_type=layer.properties.type,
                      layer_url=layer.url,
                      layer_name=layer.properties.name,
                      backup_date=str(datetime.utcnow()))
        self.sessions[backup_id] = backup
        return backup_id

    def process_results(self, backup_id, results=None):
        if not self._basepath:
            return None

        if not self.sessions[backup_id]:
            return None

        # Get staged backup
        backup = self.sessions[backup_id]

        # Extract features that failed to delete from service
        if results:
            failures = [result['objectId'] for result in results["deleteResults"] if result['success'] == False]
            if len(failures) > 0:
                fs = FeatureSet.from_dict(backup['feature_set'])
                sdf = fs.sdf
                # Filter spatial data frame for features not included in failures
                failures_extracted = sdf[~sdf[fs.object_id_field_name].isin(failures)]
                fs = FeatureSet.from_dataframe(failures_extracted)
                backup["feature_set"] = fs.to_dict()

        path = self._basepath / f'{backup_id}-{backup["layer_name"]}.json.bak'
        with safe_open_w(path) as f:
            json.dump(backup, f, indent=4)
        return path
