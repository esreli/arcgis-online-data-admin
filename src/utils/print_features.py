def print_features(features, oid_name='OBJECTID'):
    formatted_features = ['\tOID: {oid}, Geometry: {geometry}'.format(
        oid=f.attributes['OBJECTID'],
        geometry=f.geometry
    ) for f in features]
    return '\n'.join(formatted_features)
