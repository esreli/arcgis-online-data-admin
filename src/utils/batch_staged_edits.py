from collections import namedtuple
from pandas import DataFrame


Edits = namedtuple('Edits', 'add update delete')


def batch(source_sdf: DataFrame, destination_sdf: DataFrame, destination_oid_key: str, destination_reference_id_key: str) -> Edits:
    # Build keys
    if destination_reference_id_key in destination_sdf.columns:
        keys = destination_sdf[destination_reference_id_key].to_list()
    else:
        keys = []
    #
    # Derive batched lists.
    #
    # Note, this function is used in place of using:
    #   `FeatureSet.from_dataframe(sdf)`.
    # When using the above function, the arcgis python API incorrectly casts the object ID
    # field column name to the reserved 'OBJECTID'. This breaks if the service's object ID
    # field name is anything other then 'OBJECTID'.
    def sdf_to_list(sdf):
        features = []
        for index, row in sdf.iterrows():
            if 'SHAPE' in sdf.columns:
                geometry = row.pop('SHAPE')
                features.append(dict(attributes=row.to_dict(), geometry=geometry))
            else:
                features.append(dict(attributes=row.to_dict()))
        return features
    # Add Edits
    add_sdf = source_sdf[~source_sdf[destination_reference_id_key].isin(keys)]
    add_sdf.spatial = source_sdf.spatial
    if len(add_sdf) > 0:
        adds = sdf_to_list(add_sdf)
    else:
        adds = None
    del add_sdf
    # Conditionally Update and Delete
    updates = None
    deletes = None
    if destination_reference_id_key in destination_sdf.columns:
        # Update Edits
        update_sdf = source_sdf[source_sdf[destination_reference_id_key].isin(keys)]
        update_sdf.spatial = source_sdf.spatial
        if destination_oid_key in destination_sdf.columns:
            oid_column = update_sdf[destination_reference_id_key].apply(
                lambda x: str(destination_sdf.loc[destination_sdf[destination_reference_id_key] == x][destination_oid_key].values[0]))
            update_sdf[destination_oid_key] = oid_column
        if len(update_sdf) > 0:
            updates = sdf_to_list(update_sdf)
        del update_sdf
        # Delete Edits
        delete_sdf = destination_sdf[~destination_sdf[destination_reference_id_key].isin(source_sdf[destination_reference_id_key].to_list())]
        delete_sdf.spatial = source_sdf.spatial
        if len(delete_sdf) > 0:
            deletes = delete_sdf[destination_oid_key].to_list()
        del delete_sdf
    # Finish
    return Edits(
        add=adds,
        update=updates,
        delete=deletes
    )
